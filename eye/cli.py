#!/usr/bin/env python
import io
import os
import sys
import time
from datetime import datetime

import logging
logger = logging.getLogger(__name__)

import numpy as np
import picamera

import eye
from eye import s3
from eye import sqs

def round_up(n, multiple):
    remainder = n % multiple
    return (n + multiple - remainder) if remainder else n

# YUV conversion matrix from ITU-R BT.601 version (SDTV)
#                             Y       U       V
SDTV_RGB2YUV = np.array([[1.164,  0.000,  1.596],    # R
                         [1.164, -0.392, -0.813],    # G
                         [1.164,  2.017,  0.000]])   # B
SDTV_YUV2RGB = SDTV_RGB2YUV.T


def timestamp():
    # almost ISO-8601, except: no timezone, no milliseconds, and s/:/-/g
    return datetime.now().strftime('%Y-%m-%dT%H-%M-%S')


def YUV2RGB(Y, U, V):
    # Mostly from picamera docs:
    # Offset Y by 16, and UV by 128
    YUV = np.dstack((Y - 16, U - 128, V - 128))
    # Take the dot product with the matrix to produce RGB output, clamp the
    # results to byte range and convert to bytes
    return YUV.dot(SDTV_YUV2RGB).clip(0, 255).astype(np.uint8)


def read_YUV(camera, image_buffer, width, height):
    # reuse the buffer
    image_buffer.seek(0)
    image_buffer.truncate()

    # if opts.diff:
    logger.debug('Capturing YUV from Pi Camera')
    camera.capture(image_buffer, 'yuv')

    image_buffer.seek(0)
    # the buffer is now in chunks of 4/6 Y, 1/6 U, and 1/6 V
    area = width*height
    Y = np.fromfile(image_buffer, np.uint8, area).reshape((height, width))
    # load the color data (U and V)
    U = np.fromfile(image_buffer, np.uint8, area // 4).\
        reshape((height // 2, width // 2)).repeat(2, axis=0).repeat(2, axis=1)
    V = np.fromfile(image_buffer, np.uint8, area // 4).\
        reshape((height // 2, width // 2)).repeat(2, axis=0).repeat(2, axis=1)
    return Y, U, V


def refit(X, lower, upper):
    X_min, X_max = np.min(X), np.max(X)
    X_range = float(X_max - X_min)
    target_range = float(upper - lower)
    return ((X - X_min) / X_range) * target_range + lower


def imwrite(filename, data):
    import cv2
    return cv2.imwrite('/home/pi/Desktop/tmp/' + filename, data)


def get_diff(camera, image_buffer, width, height, interval=5):
    Y1, U1, V1 = read_YUV(camera, image_buffer, width, height)
    time.sleep(interval)
    Y2, U2, V2 = read_YUV(camera, image_buffer, width, height)
    # RGB = YUV2RGB(Y, U, V)

    Y1F = Y1.astype(np.float64)
    Y2F = Y2.astype(np.float64)
    DYFSQ = (Y2F - Y1F)**2
    imwrite('%s-DYFSQ.jpg' % timestamp(), DYFSQ)
    return DYFSQ
    # import IPython; IPython.embed(); raise SystemExit(26)


def timelapse(parser):
    parser.add_argument('--interval', type=int, default=60,
        help='# of seconds between pictures')
    parser.add_argument('--width', type=int, default=800,
        help='Image width')
    parser.add_argument('--height', type=int, default=600,
        help='Image height')
    parser.add_argument('--rotation', type=int,
        choices=(0, 90, 180, 270), default=0,
        help='Rotation (cable goes down)')
    # parser.add_argument('--diff', action='store_true',
    #     help='Handle diffs instead of individual images')
    opts = parser.parse_args()

    with picamera.PiCamera() as camera:
        width = round_up(opts.width, 32)
        height = round_up(opts.height, 16)
        logger.debug('Using resolution: (w=%d, h=%d)', width, height)
        camera.resolution = (width, height)
        camera.rotation = opts.rotation
        camera.start_preview()
        # Camera warm-up time
        logger.debug('Camera warming up')
        time.sleep(2)
        logger.debug('Camera warmed up')

        image_buffer = io.BytesIO()
        # image_buffer = os.tmpfile() # required for numpy (Yeah, I don't know why numpy is so difficult sometimes)

        while True:
            image_buffer.seek(0)
            image_buffer.truncate()
            logger.debug('Capturing JPEG from Pi Camera')
            camera.capture(image_buffer, 'jpeg')

            # capture is in memory -- upload it
            image_buffer.seek(0)
            s3_key = 'images/%s/%s.jpg' % (opts.id, timestamp())
            logger.info('Uploading to S3 with key: %s', s3_key)
            s3.upload(image_buffer, s3_key)
            sqs.push(dict(id=opts.id, s3=s3_key))

            logger.info('Sleeping %ds', opts.interval)
            time.sleep(opts.interval)


def app(parser):
    parser.add_argument('--reload', action='store_true', help='Reload bottle app automatically')
    opts = parser.parse_args()

    import bottle
    from eye.www import app

    bottle.run(app, port=8091, reloader=opts.reload)


def listen(parser):
    '''
    `pi-eye listen` should be run in conjunction with `pi-eye app`,
    '''
    import redis
    # pi:latest-images is an intermediate cache of the latest images
    # sent home from the various pis
    redis_client = redis.StrictRedis()
    redis_key = 'pi:latest-image-urls'
    latest_image_urls = redis_client.hgetall(redis_key)
    logger.info('Listening (current value: %r)', latest_image_urls)

    from eye import sqs, s3
    for message in sqs.pop_loop():
        # each message in the queue should be a dict with id and s3 bucket key
        url = s3.get_url(message['s3'])
        logger.info('Setting: %s[%s] = %r', redis_key, message['id'], url)
        redis_client.hset(redis_key, message['id'], url)
    # this loop should never exit
    logger.critical('Stopping listening')


def main():
    import argparse
    commands = dict(timelapse=timelapse, app=app, listen=listen)
    parser = argparse.ArgumentParser(description='Primary entry point for common pi-eye commands',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('command', choices=commands,
        help='Command to run')
    parser.add_argument('--id', default='pi2',
        help='Identifier of current camera')
    parser.add_argument('--verbose', action='store_true',
        help='Log extra information')
    parser.add_argument('--version', action='version',
        version=eye.__version__)
    opts, _ = parser.parse_known_args()

    level = logging.DEBUG if opts.verbose else logging.INFO
    logging.basicConfig(level=level)

    commands[opts.command](parser)


if __name__ == '__main__':
    main()

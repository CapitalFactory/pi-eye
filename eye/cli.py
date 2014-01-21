#!/usr/bin/env python
import sys
import io
import time
from datetime import datetime

import logging
logger = logging.getLogger(__name__)


import picamera

import eye
from eye import s3
from eye import sqs


def timelapse(parser):
    parser.add_argument('--interval', type=int, default=60,
        help='# of seconds between pictures')
    parser.add_argument('--width', type=int, default=800, help='Image width')
    parser.add_argument('--height', type=int, default=600, help='Image height')
    parser.add_argument('--rotation', type=int, choices=(0, 90, 180, 270), default=0,
        help='Rotation (cable goes down)')
    opts = parser.parse_args()

    with picamera.PiCamera() as camera:
        camera.resolution = (opts.width, opts.height)
        camera.rotation = opts.rotation
        camera.start_preview()
        # Camera warm-up time
        time.sleep(2)
        print >> sys.stderr, 'Camera warmed up'

        while True:
            # timestamp is almost ISO-8601, except:
            # no timezone, no milliseconds, and s/:/-/g
            timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
            s3_path = 'images/%s/%s.jpg' % (opts.id, timestamp)

            bytestream = io.BytesIO()

            # capture from pi camera into fd/filepath
            logger.debug('Capturing from Pi Camera')
            camera.capture(bytestream, 'jpeg')

            # capture is in memory -- upload it
            logger.info('Uploading %s', s3_path)
            bytestream.seek(0)
            s3.upload(bytestream, s3_path)
            sqs.push('%s s3:%s' % (opts.id, s3_path))

            print >> sys.stderr, 'Sleeping %ds' % opts.interval
            time.sleep(opts.interval)


def app(parser):
    parser.add_argument('--reload', action='store_true', help='Reload bottle app automatically')
    opts = parser.parse_args()

    import bottle
    from eye.www import app

    bottle.run(app, port=8091, reloader=opts.reload)


def main():
    import argparse
    commands = dict(timelapse=timelapse, app=app)
    parser = argparse.ArgumentParser(description='Primary entry point for common pi-eye commands',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('command', choices=commands, help='Command to run')
    parser.add_argument('--id', default='pi2', help='Identifier of current camera')
    parser.add_argument('--verbose', action='store_true', help='Log extra information')
    parser.add_argument('--version', action='version', version=eye.__version__)
    opts, _ = parser.parse_known_args()

    level = logging.DEBUG if opts.verbose else logging.INFO
    logging.basicConfig(level=level)

    commands[opts.command](parser)


if __name__ == '__main__':
    main()

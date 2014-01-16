#!/usr/bin/env python
import sys
import io
import time
from datetime import datetime
# import sched
# scheduler = sched.scheduler(time.time, time.sleep)
# import tempfile

import picamera

import eye
from eye import s3


def timelapse(parser):
    parser.add_argument('--interval', type=int, default=60, help='# of seconds between pictures')
    parser.add_argument('--width', type=int, default=800, help='Image width')
    parser.add_argument('--height', type=int, default=600, help='Image height')
    opts = parser.parse_args()

    with picamera.PiCamera() as camera:
        camera.resolution = (opts.width, opts.height)
        camera.start_preview()
        # Camera warm-up time
        time.sleep(2)
        print >> sys.stderr, 'Camera warmed up'

        while True:
            timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
            s3_path = 'images/%s/%s' % (opts.id, timestamp)

            # fd, filepath = tempfile.mkstemp()
            # with tempfile.TemporaryFile(suffix='.jpg') as fd:
            bytestream = io.BytesIO()

            # capture from pi camera into fd/filepath
            print >> sys.stderr, 'Capturing  %s', s3_path
            camera.capture(bytestream, 'jpeg')
            print >> sys.stderr, 'Uploading %s', s3_path
            s3.upload(bytestream, s3_path)

            print >> sys.stderr, 'Sleeping %ds', opts.interval
            time.sleep(opts.interval)


def main():
    import argparse
    commands = dict(timelapse=timelapse)
    parser = argparse.ArgumentParser(description='Primary entry point for common pi-eye commands',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('command', choices=commands, help='Command to run')
    parser.add_argument('--id', default='pi2', help='Identifier of current camera')
    parser.add_argument('--verbose', action='store_true', help='Log extra information')
    parser.add_argument('--version', action='version', version=eye.__version__)
    opts, _ = parser.parse_known_args()

    commands[opts.command](parser)

if __name__ == '__main__':
    main()

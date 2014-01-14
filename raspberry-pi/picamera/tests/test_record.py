# vim: set et sw=4 sts=4 fileencoding=utf-8:
#
# Python camera library for the Rasperry-Pi camera module
# Copyright (c) 2013,2014 Dave Hughes <dave@waveform.org.uk>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the copyright holder nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from __future__ import (
    unicode_literals,
    print_function,
    division,
    absolute_import,
    )

# Make Py2's str equivalent to Py3's
str = type('')

import io
import os
import re
import time
import tempfile
import picamera
import pytest
import subprocess
from collections import namedtuple


RecordingCase = namedtuple('TestCase', ('format', 'ext', 'options'))

RECORDING_CASES = (
    RecordingCase('h264',  '.h264', {'profile': 'baseline'}),
    RecordingCase('h264',  '.h264', {'profile': 'main'}),
    RecordingCase('h264',  '.h264', {'profile': 'high'}),
    RecordingCase('h264',  '.h264', {'profile': 'constrained'}),
    RecordingCase('h264',  '.h264', {'resize': (640, 480)}),
    RecordingCase('h264',  '.h264', {'bitrate': 0, 'quantization': 10}),
    RecordingCase('h264',  '.h264', {'bitrate': 0, 'quantization': 20}),
    RecordingCase('h264',  '.h264', {'bitrate': 0, 'quantization': 30}),
    RecordingCase('h264',  '.h264', {'bitrate': 0, 'quantization': 40}),
    RecordingCase('h264',  '.h264', {'bitrate': 10000000, 'intra_period': 15}),
    RecordingCase('h264',  '.h264', {'bitrate': 10000000, 'inline_headers': False}),
    RecordingCase('h264',  '.h264', {'bitrate': 15000000}),
    RecordingCase('h264',  '.h264', {'bitrate': 20000000, 'profile': 'main'}),
    RecordingCase('mjpeg', '.mjpg', {}),
    RecordingCase('mjpeg', '.mjpg', {'bitrate': 10000000}),
    RecordingCase('mjpeg', '.mjpg', {'bitrate': 0, 'quantization': 20}),
    )


@pytest.fixture(scope='module', params=RECORDING_CASES)
def filenames_format_options(request):
    filename1 = tempfile.mkstemp(suffix=request.param.ext)[1]
    filename2 = tempfile.mkstemp(suffix=request.param.ext)[1]
    def fin():
        os.unlink(filename1)
        os.unlink(filename2)
    request.addfinalizer(fin)
    return filename1, filename2, request.param.format, request.param.options

# Run tests with a variety of format specs
@pytest.fixture(scope='module', params=RECORDING_CASES)
def format_options(request):
    return request.param.format, request.param.options

def verify_video(filename_or_obj, format, resolution):
    width, height = resolution
    if isinstance(filename_or_obj, str):
        p = subprocess.Popen([
            'avconv',
            '-f', format,
            '-i', filename_or_obj,
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    else:
        p = subprocess.Popen([
            'avconv',
            '-f', format,
            '-i', '-',
            ], stdin=filename_or_obj, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.communicate()[0]
    assert p.returncode == 1, 'avconv returned unexpected code %d' % p.returncode
    state = 'start'
    for line in out.splitlines():
        line = line.decode('utf-8').strip()
        if state == 'start' and re.match(r'^Input #0', line):
            state = 'input'
        elif state == 'input' and re.match(r'^Duration', line):
            state = 'dur'
        elif state == 'dur' and re.match(r'^Stream #0\.0', line):
            assert re.match(
                r'^Stream #0\.0: '
                r'Video: %s( \(.*\))?, '
                r'yuvj?420p, '
                r'%dx%d( \[PAR \d+:\d+ DAR \d+:\d+\])?, '
                r'\d+ fps, \d+ tbr, \d+k? tbn, \d+k? tbc$' % (
                    format, width, height),
                line
                ), 'Unexpected avconv output: %s' % line
            return
    assert False, 'Failed to locate stream analysis in avconv output'


def test_record_to_file(camera, previewing, resolution, filenames_format_options):
    filename1, filename2, format, options = filenames_format_options
    if resolution == (2592, 1944) and 'resize' not in options:
        pytest.xfail('Cannot encode video at max resolution')
    camera.start_recording(filename1, **options)
    try:
        camera.wait_recording(1)
        verify2 = (
                format != 'h264' or (
                    options.get('inline_headers', True) and
                    options.get('bitrate', 1)
                    )
                )
        if verify2:
            camera.split_recording(filename2)
            camera.wait_recording(1)
        else:
            with pytest.raises(picamera.PiCameraRuntimeError):
                camera.split_recording(filename2)
    finally:
        camera.stop_recording()
    if 'resize' in options:
        resolution = options['resize']
    verify_video(filename1, format, resolution)
    if verify2:
        verify_video(filename2, format, resolution)

def test_record_to_stream(camera, previewing, resolution, format_options):
    format, options = format_options
    if resolution == (2592, 1944) and 'resize' not in options:
        pytest.xfail('Cannot encode video at max resolution')
    stream1 = tempfile.SpooledTemporaryFile()
    stream2 = tempfile.SpooledTemporaryFile()
    camera.start_recording(stream1, format, **options)
    try:
        camera.wait_recording(1)
        verify2 = (
                format != 'h264' or (
                    options.get('inline_headers', True) and
                    options.get('bitrate', 1)
                    )
                )
        if verify2:
            camera.split_recording(stream2)
            camera.wait_recording(1)
        else:
            with pytest.raises(picamera.PiCameraRuntimeError):
                camera.split_recording(stream2)
    finally:
        camera.stop_recording()
    stream1.seek(0)
    if 'resize' in options:
        resolution = options['resize']
    verify_video(stream1, format, resolution)
    if verify2:
        stream2.seek(0)
        verify_video(stream2, format, resolution)

def test_circular_record(camera, previewing, resolution):
    if resolution == (2592, 1944):
        pytest.xfail('Cannot encode video at max resolution')
    stream = picamera.PiCameraCircularIO(camera, seconds=4)
    camera.start_recording(stream, format='h264')
    try:
        # Keep recording until the stream is definitely full and starts
        # removing earlier bits, or until 20 seconds
        start = time.time()
        while stream._length < stream._size and time.time() - start < 20:
            camera.wait_recording(1)
        # Record one more second, then test the result
        camera.wait_recording(1)
    finally:
        camera.stop_recording()
    temp = tempfile.SpooledTemporaryFile()
    for frame in stream.frames:
        if frame.header:
            stream.seek(frame.position)
            break
    while True:
        buf = stream.read1()
        if not buf:
            break
        temp.write(buf)
    temp.seek(0)
    verify_video(temp, 'h264', resolution)


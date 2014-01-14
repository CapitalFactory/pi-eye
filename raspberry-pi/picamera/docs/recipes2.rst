.. _recipes2:

================
Advanced Recipes
================

The following recipes involve advanced techniques and may not be "beginner
friendly". Please feel free to suggest enhancements or additional recipes.


.. _yuv_capture:

Raw image capture (YUV format)
==============================

If you want images captured without loss of detail (due to JPEG's lossy
compression), you are probably better off exploring PNG as an alternate image
format (PNG uses lossless compression). However, some applications
(particularly scientific ones) simply require the raw sensor data in numeric
form. For this, the ``'yuv'`` format is provided::

    import time
    import picamera

    with picamera.PiCamera() as camera:
        camera.resolution = (100, 100)
        camera.start_preview()
        time.sleep(2)
        camera.capture('image.data', 'yuv')

The specific `YUV`_ format used is YUV420 (planar). This means that the Y
(luminance) values occur first in the resulting data and have full resolution
(one 1-byte Y value for each pixel in the image). The Y values are followed by
the U (chrominance) values, and finally the V (chrominance) values.  The UV
values have one quarter the resolution of the Y components (4 1-byte Y values
in a square for each 1-byte U and 1-byte V value).

It is also important to note that when outputting to raw format, the camera
rounds the requested resolution. The horizontal resolution is rounded up to the
nearest multiple of 32, while the vertical resolution is rounded up to the
nearest multiple of 16. For example, if the requested resolution is 100x100,
a raw capture will actually contain 128x112 pixels worth of data, but pixels
beyond 100x100 will be uninitialized.

Given that the YUV420 format contains 1.5 bytes worth of data for each pixel
(a 1-byte Y value for each pixel, and 1-byte U and V values for every 4 pixels),
and taking into account the resolution rounding, the size of a 100x100 raw
capture will be:

.. math::

           & 128   \quad \text{100 rounded up to nearest multiple of 32} \\
    \times & 112   \quad \text{100 rounded up to nearest multiple of 16} \\
    \times & 1.5   \quad \text{bytes of data per pixel in YUV420 format} \\
    =      & 21504 \quad \text{bytes}

The first 14336 bytes of the data (128*112) will be Y values, the next 3584
bytes (128*112/4) will be U values, and the final 3584 bytes will be the V
values.

The following code demonstrates capturing an image in raw YUV format, loading
the data into a set of `numpy`_ arrays, and converting the data to RGB format
in an efficient manner::

    from __future__ import division

    import time
    import picamera
    import numpy as np

    width = 100
    height = 100
    stream = open('image.data', 'wb')
    # Capture the image in raw YUV format
    with picamera.PiCamera() as camera:
        camera.resolution = (width, height)
        camera.start_preview()
        time.sleep(2)
        camera.capture(stream, 'yuv')
    # Rewind the stream for reading
    stream.seek(0)
    # Calculate the actual image size in the stream (accounting for rounding
    # of the resolution)
    fwidth = (width + 31) // 32 * 32
    fheight = (height + 15) // 16 * 16
    # Load the Y (luminance) data from the stream
    Y = np.fromfile(stream, dtype=np.uint8, count=fwidth*fheight).\
            reshape((fheight, fwidth))
    # Load the UV (chrominance) data from the stream, and double its size
    U = np.fromfile(stream, dtype=np.uint8, count=(fwidth//2)*(fheight//2)).\
            reshape((fheight//2, fwidth//2)).\
            repeat(2, axis=0).repeat(2, axis=1)
    V = np.fromfile(stream, dtype=np.uint8, count=(fwidth//2)*(fheight//2)).\
            reshape((fheight//2, fwidth//2)).\
            repeat(2, axis=0).repeat(2, axis=1)
    # Stack the YUV channels together, crop the actual resolution, convert to
    # floating point for later calculations, and apply the standard biases
    YUV = np.dstack((Y, U, V))[:height, :width, :].astype(np.float)
    YUV[:, :, 0]  = YUV[:, :, 0]  - 16   # Offset Y by 16
    YUV[:, :, 1:] = YUV[:, :, 1:] - 128  # Offset UV by 128
    # YUV conversion matrix from ITU-R BT.601 version (SDTV)
    #              Y       U       V
    M = np.array([[1.164,  0.000,  1.596],    # R
                  [1.164, -0.392, -0.813],    # G
                  [1.164,  2.017,  0.000]])   # B
    # Take the dot product with the matrix to produce RGB output, clamp the
    # results to byte range and convert to bytes
    RGB = YUV.dot(M.T).clip(0, 255).astype(np.uint8)

Alternatively, see :ref:`rgb_capture` for a method of having the camera output
RGB data directly.

.. versionchanged:: 1.0

    The :attr:`~picamera.PiCamera.raw_format` attribute is now deprecated, as
    is the ``'raw'`` format specification for the
    :meth:`~picamera.PiCamera.capture` method. Simply use the ``'yuv'`` format
    instead, as shown in the code above.


.. _rgb_capture:

Raw image capture (RGB format)
==============================

The RGB format is rather larger than the `YUV`_ format discussed in the section
above, but is more useful for most analyses. To have the camera produce raw
output in `RGB`_ format, you simply need to specify ``'rgb'`` as the format
for the :meth:`~picamera.PiCamera.capture` method instead::

    import time
    import picamera

    with picamera.PiCamera() as camera:
        camera.resolution = (100, 100)
        camera.start_preview()
        time.sleep(2)
        camera.capture('image.data', 'rgb')

The size of raw RGB data can be calculated similarly to YUV captures. Firstly
round the resolution appropriately (see :ref:`yuv_capture` for the specifics),
then multiply the number of pixels by 3 (1 byte of red, 1 byte of green, and
1 byte of blue intensity). Hence, for a 100x100 capture, the amount of data
produced is:

.. math::

           & 128   \quad \text{100 rounded up to nearest multiple of 32} \\
    \times & 112   \quad \text{100 rounded up to nearest multiple of 16} \\
    \times & 3     \quad \text{bytes of data per pixel in RGB888 format} \\
    =      & 43008 \quad \text{bytes}

The resulting RGB data is interleaved. That is to say that the red, green and
blue values for a given pixel are grouped together, in that order. The first
byte of the data is the red value for the pixel at (0, 0), the second byte is
the green value for the same pixel, and the third byte is the blue value for
that pixel. The fourth byte is the red value for the pixel at (1, 0), and so
on.

Loading the resulting RGB data into a `numpy`_ array is simple::

    from __future__ import division

    width = 100
    height = 100
    stream = open('image.data', 'wb')
    # Capture the image in raw RGB format
    with picamera.PiCamera() as camera:
        camera.resolution = (width, height)
        camera.start_preview()
        time.sleep(2)
        camera.capture(stream, 'rgb')
    # Rewind the stream for reading
    stream.seek(0)
    # Calculate the actual image size in the stream (accounting for rounding
    # of the resolution)
    fwidth = (width + 31) // 32 * 32
    fheight = (height + 15) // 16 * 16
    # Load the data in a three-dimensional array and crop it to the requested
    # resolution
    image = np.fromfile(stream, dtype=uint8).\
            reshape((fheight, fwidth, 3))[:height, :width, :]
    # If you wish, the following code will convert the image's bytes into
    # floating point values in the range 0 to 1 (a typical format for some
    # sorts of analysis)
    image = image.astype(np.float, copy=False)
    image = image / 255.0

.. versionchanged:: 1.0

    The :attr:`~picamera.PiCamera.raw_format` attribute is now deprecated, as
    is the ``'raw'`` format specification for the
    :meth:`~picamera.PiCamera.capture` method. Simply use the ``'yuv'`` format
    instead, as shown in the code above.

.. warning::

    You may find RGB captures rather slow. If this is the case, please try the
    ``'rgba'`` format instead. The reason for this is that GPU component that
    picamera uses to perform RGB conversion doesn't support RGB output, only
    RGBA. As a result, RGBA data can be written directly, but picamera has to
    spend time stripping out the (unused) alpha byte from RGBA if RGB format
    is requested. A similar situation exists for the BGR and BGRA formats.


.. _rapid_capture:

Rapid capture and processing
============================

The camera is capable of capturing a sequence of images extremely rapidly by
utilizing its video-capture capabilities with a JPEG encoder (via the
``use_video_port`` parameter). However, there are several things to note about
using this technique:

* When using video-port based capture only the preview area is captured; in
  some cases this may be desirable (see the discussion under
  :ref:`preview_still_resolution`).

* No Exif information is embedded in JPEG images captured through the
  video-port.

* Captures typically appear "granier" with this technique. The author is not
  aware of the exact technical reasons why this is so, but suspects that some
  part of the image processing pipeline that is present for still captures is
  not used when performing still captures through the video-port.

All capture methods support the ``use_video_port`` option, but the methods
differ in their ability to rapidly capture sequential frames. So, whilst
:meth:`~picamera.PiCamera.capture` and
:meth:`~picamera.PiCamera.capture_continuous` both support ``use_video_port``,
:meth:`~picamera.PiCamera.capture_sequence` is by far the fastest method. Using
this method, the author has managed 30fps JPEG captures at a resolution of
1024x768.

By default, :meth:`~picamera.PiCamera.capture_sequence` is particular suited to
capturing a fixed number of frames rapidly, as in the following example which
captures a "burst" of 5 images::

    import time
    import picamera

    with picamera.PiCamera() as camera:
        camera.resolution = (1024, 768)
        camera.framerate = 30
        camera.start_preview()
        time.sleep(2)
        camera.capture_sequence([
            'image1.jpg',
            'image2.jpg',
            'image3.jpg',
            'image4.jpg',
            'image5.jpg',
            ])

We can refine this slightly by using a generator expression to provide the
filenames for processing instead of specifying every single filename manually::

    import time
    import picamera

    frames = 60

    with picamera.PiCamera() as camera:
        camera.resolution = (1024, 768)
        camera.framerate = 30
        camera.start_preview()
        # Give the camera some warm-up time
        time.sleep(2)
        start = time.time()
        camera.capture_sequence([
            'image%02d.jpg' % i
            for i in range(frames)
            ], use_video_port=True)
        finish = time.time()
    print('Captured %d frames at %.2ffps' % (
        frames,
        frames / (finish - start)))

However, this still doesn't let us capture an arbitrary number of frames until
some condition is satisfied. To do this we need to use a generator function to
provide the list of filenames (or more usefully, streams) to the
:meth:`~picamera.PiCamera.capture_sequence` method::

    import time
    import picamera

    frames = 60

    def filenames():
        frame = 0
        while frame < frames:
            yield 'image%02d.jpg' % frame
            frame += 1

    with picamera.PiCamera() as camera:
        camera.resolution = (1024, 768)
        camera.framerate = 30
        camera.start_preview()
        # Give the camera some warm-up time
        time.sleep(2)
        start = time.time()
        camera.capture_sequence(filenames(), use_video_port=True)
        finish = time.time()
    print('Captured %d frames at %.2ffps' % (
        frames,
        frames / (finish - start)))

The major issue with capturing this rapidly is that the Raspberry Pi's IO
bandwidth is extremely limited. As a format, JPEG is considerably less
efficient than the H.264 video format (which is to say that, for the same
number of bytes, H.264 will provide considerably better quality over the same
number of frames).

At higher resolutions (beyond 800x600) you are likely to find you cannot
sustain 30fps captures to the Pi's SD card for very long (before exhausting the
disk cache).  In other words, if you are intending to perform processing on the
frames after capture, you may be better off just capturing video and decoding
frames from the resulting file rather than dealing with individual JPEG
captures.

However, if you can perform your processing fast enough, you may not need to
involve the disk at all.  Using a generator function, we can maintain a queue
of objects to store the captures, and have parallel threads accept and process
the streams as captures come in. Provided the processing runs at a faster frame
rate than the captures, the encoder won't stall and nothing ever need hit the
disk.

Please note that the following code involves some fairly advanced techniques
(threading and all its associated locking fun is typically not a "beginner
friendly" subject, not to mention generator expressions)::

    import io
    import time
    import threading
    import picamera

    # Create a pool of image processors
    done = False
    lock = threading.Lock()
    pool = []

    class ImageProcessor(threading.Thread):
        def __init__(self):
            super(ImageProcessor, self).__init__()
            self.stream = io.BytesIO()
            self.event = threading.Event()
            self.terminated = False
            self.start()

        def run(self):
            # This method runs in a separate thread
            global done
            while not self.terminated:
                if self.event.wait(1):
                    try:
                        self.stream.seek(0)
                        # Read the image and do some processing on it
                        #Image.open(self.stream)
                        #...
                        #...
                        # Set done to True if you want the script to terminate
                        # at some point
                        #done=True
                    finally:
                        # Reset the stream and event
                        self.stream.seek(0)
                        self.stream.truncate()
                        self.event.clear()
                        # Return ourselves to the pool
                        with lock:
                            pool.append(self)

    def streams():
        while not done:
            with lock:
                processor = pool.pop()
            yield processor.stream
            processor.event.set()

    with picamera.PiCamera() as camera:
        pool = [ImageProcessor() for i in range (4)]
        camera.resolution = (640, 480)
        # Set the framerate appropriately; too fast and the image processors
        # will stall the image pipeline and crash the script
        camera.framerate = 10
        camera.start_preview()
        time.sleep(2)
        camera.capture_sequence(streams(), use_video_port=True)

    # Shut down the processors in an orderly fashion
    while pool:
        with lock:
            processor = pool.pop()
        processor.terminated = True
        processor.join()

.. versionadded:: 0.5


.. _rapid_streaming:

Rapid capture and streaming
===========================

Following on from :ref:`rapid_capture`, we can combine the video-port capture
technique with :ref:`streaming_capture`. The server side script doesn't change
(it doesn't really care what capture technique is being used - it just reads
JPEGs off the wire). The changes to the client side script can be minimal at
first - just add ``use_video_port=True`` to the
:meth:`~picamera.PiCamera.capture_continuous` call::

    import io
    import socket
    import struct
    import time
    import picamera

    client_socket = socket.socket()
    client_socket.connect(('my_server', 8000))
    connection = client_socket.makefile('wb')
    try:
        with picamera.PiCamera() as camera:
            camera.resolution = (640, 480)
            time.sleep(2)
            start = time.time()
            stream = io.BytesIO()
            # Use the video-port for captures...
            for foo in camera.capture_continuous(stream, 'jpeg',
                                                 use_video_port=True):
                connection.write(struct.pack('<L', stream.tell()))
                connection.flush()
                stream.seek(0)
                connection.write(stream.read())
                if time.time() - start > 30:
                    break
                stream.seek(0)
                stream.truncate()
        connection.write(struct.pack('<L', 0))
    finally:
        connection.close()
        client_socket.close()

Using this technique, the author can manage about 14fps of streaming at
640x480. One deficiency of the script above is that it interleaves capturing
images with sending them over the wire (although we deliberately don't flush on
sending the image data). Potentially, it would be more efficient to permit
image capture to occur simultaneously with image transmission. We can attempt
to do this by utilizing the background threading techniques from the final
example in :ref:`rapid_capture`.

Once again, please note that the following code involves some quite advanced
techniques and is not "beginner friendly"::

    import io
    import socket
    import struct
    import time
    import threading
    import picamera

    client_socket = socket.socket()
    client_socket.connect(('spider', 8000))
    connection = client_socket.makefile('wb')
    try:
        connection_lock = threading.Lock()
        pool = []
        pool_lock = threading.Lock()

        class ImageStreamer(threading.Thread):
            def __init__(self):
                super(ImageStreamer, self).__init__()
                self.stream = io.BytesIO()
                self.event = threading.Event()
                self.terminated = False
                self.start()

            def run(self):
                # This method runs in a background thread
                while not self.terminated:
                    if self.event.wait(1):
                        try:
                            with connection_lock:
                                connection.write(struct.pack('<L', self.stream.tell()))
                                connection.flush()
                                self.stream.seek(0)
                                connection.write(self.stream.read())
                        finally:
                            self.stream.seek(0)
                            self.stream.truncate()
                            self.event.clear()
                            with pool_lock:
                                pool.append(self)

        count = 0
        start = time.time()
        finish = time.time()

        def streams():
            global count, finish
            while finish - start < 30:
                with pool_lock:
                    streamer = pool.pop()
                yield streamer.stream
                streamer.event.set()
                count += 1
                finish = time.time()

        with picamera.PiCamera() as camera:
            pool = [ImageStreamer() for i in range(4)]
            camera.resolution = (640, 480)
            # Set the framerate appropriately; too fast and we'll starve the
            # pool of streamers and crash the script
            camera.framerate = 15
            camera.start_preview()
            time.sleep(2)
            camera.capture_sequence(streams(), 'jpeg', use_video_port=True)

        # Shut down the streamers in an orderly fashion
        while pool:
            with pool_lock:
                streamer = pool.pop()
            streamer.terminated = True
            streamer.join()

        # Write the terminating 0-length to the connection to let the server
        # know we're done
        with connection_lock:
            connection.write(struct.pack('<L', 0))

    finally:
        connection.close()
        client_socket.close()

    print('Sent %d images in %.2f seconds at %.2ffps' % (
        count, finish-start, count / (finish-start)))

The author's tests with the script above haven't yielded substantial
improvements over the former script using
:meth:`~picamera.PiCamera.capture_continuous`, but the reason for this is not
currently clear. Suggestions for further improvements are welcomed!

.. versionadded:: 0.5


.. _circular_record:

Recording to a circular stream
==============================

This is similar to :ref:`stream_record` but uses a special kind of in-memory
stream provided by the picamera library. The
:class:`~picamera.PiCameraCircularIO` class implements a `ring buffer`_ based
stream, specifically for video recording.  This enables you to keep an
in-memory stream containing the last *n* seconds of video recorded (where *n*
is determined by the bitrate of the video recording and the size of the ring
buffer underlying the stream).

For example, the following script keeps at least 10 seconds of video in the
circular stream and then writes it to disk when the user presses a key::

    import io
    import sys
    import picamera
    from select import select

    with picamera.PiCamera() as camera:
        camera.resolution = (1280, 720)
        stream = picamera.PiCameraCircularIO(camera, seconds=10)
        camera.start_recording(stream, format='h264')
        print('Press Enter to stop recording and write out the video')
        while True:
            camera.wait_recording(0.5)
            # Wait half a second for a key press
            r, w, x = select([sys.stdin], [], [], 0.5)
            if r:
                break
        camera.stop_recording()
        print('Writing the video to foo.h264')
        # Find the first header frame in the video
        for frame in stream.frames:
            if frame.header:
                stream.seek(frame.position)
                break
        # Write the rest of the stream to a disk file
        with io.open('foo.h264', 'wb') as output:
            output.write(stream.read())

.. note::

    Note that *at least* 10 seconds of video are in the stream. This is an
    estimate only; if the H.264 encoder requires less than the specified
    bitrate (17Mbps by default) for recording the video, then more than 10
    seconds of video will be available in the stream.

In the above script we stop the camera recording before writing the stream's
content to disk. However, it is possible to read from the stream without
stopping the recording. To do this one must use the threading lock in the
:attr:`~picamera.CircularIO.lock` attribute to prevent the camera's background
writing thread from changing the stream while your own thread reads from it (as
the stream is a circular buffer, a write can remove information that is about
to be read).

Additionally, when reading from the stream, the
:meth:`~picamera.CircularIO.read1` method should be used whenever possible (as
opposed to :meth:`~picamera.CircularIO.read`) for greater efficiency. However,
note that :meth:`~picamera.CircularIO.read1` does not guarantee to return the
number of bytes requested even if they are available in the underlying stream -
it simply returns as many as are available from a single chunk up to the limit
specified.

The following variant on the above script demonstrates both of these
techniques::

    # Py2 compatibility
    from __future__ import print_function
    try:
        input = raw_input
    except NameError:
        pass

    import io
    import sys
    import picamera
    from select import select


    with picamera.PiCamera() as camera:
        camera.resolution = (1280, 720)
        stream = picamera.PiCameraCircularIO(camera, seconds=10)
        camera.start_recording(stream, format='h264')
        print('Enter <w> to write the stream to disk')
        print('Enter <q> to stop recording and exit')
        while camera.recording:
            while True:
                camera.wait_recording(0.5)
                # Wait half a second for a key press
                r, w, x = select([sys.stdin], [], [], 0.5)
                if r:
                    break
            c = input()
            if c == 'q':
                print('Exiting...')
                camera.stop_recording()
            elif c == 'w':
                print('Writing the video to foo.h264...', end='')
                # Lock the stream to prevent the camera mutating it while we
                # read from it
                with stream.lock:
                    # Find the first header frame in the video
                    for frame in stream.frames:
                        if frame.header:
                            stream.seek(frame.position)
                            break
                    # Write the rest of the stream to a disk file using read1
                    # for speed
                    with io.open('foo.h264', 'wb') as output:
                        while True:
                            buf = stream.read1()
                            if not buf:
                                break
                            output.write(buf)
                print('done')
            else:
                print('Unrecognized input: %s' % c)

.. versionadded:: 1.0


.. _record_and_capture:

Capturing images whilst recording
=================================

The camera is capable of capturing still images while it is recording video.
However, if one attempts this using the stills capture mode, the resulting
video will have dropped frames during the still image capture. This is because
regular stills require a mode change, causing the dropped frames (this is the
flicker to a higher resolution that one sees when capturing while a preview is
running).

However, if the *use_video_port* parameter is used to force a video-port based
image capture (see :ref:`rapid_capture`) then the mode change does not occur,
and the resulting video will not have dropped frames::

    import picamera

    with picamera.PiCamera() as camera:
        camera.resolution = (800, 600)
        camera.start_preview()
        camera.start_recording('foo.h264')
        camera.wait_recording(10)
        camera.capture('foo.jpg', use_video_port=True)
        camera.wait_recording(10)
        camera.stop_recording()

The above code should produce a 20 second video with no dropped frames, and a
still frame from 10 seconds into the video.

.. versionadded:: 0.8


.. _YUV: http://en.wikipedia.org/wiki/YUV
.. _RGB: http://en.wikipedia.org/wiki/RGB
.. _numpy: http://www.numpy.org/
.. _ring buffer: http://en.wikipedia.org/wiki/Circular_buffer


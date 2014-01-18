#!/usr/bin/python

from __future__ import division
import io, os, time, datetime, cv2, sys, picamera
import numpy as np

class PiEye():
  def __init__(self):
    self.debug = True
    self.image_directory = "images"
    self.last_report = None
    self.prev_image = None
    self.width = 288
    self.height = 192
    self.frame = 0
    self.frac = 0.15
    self.avg_diff = None
    self.calibration_frames = 20
    self.diffs = []
    self.threshold = .2

  # http://www.raspberrypi.org/phpBB3/viewtopic.php?t=56478&p=461637
  def diff(self, image):
    if self.prev_image is None:
      self.prev_image = image
      return False
    else:
      matrix_diff = abs(self.prev_image - image)
      avg_matrix_diff = np.average(matrix_diff)
      self.diffs.append(avg_matrix_diff)

      if self.frame <= self.calibration_frames:
        if self.avg_diff is None:
          self.avg_diff = avg_matrix_diff
        else:
          self.avg_diff = (self.avg_diff * (1 - self.frac)) + (avg_matrix_diff * self.frac)

      has_motion = avg_matrix_diff > (self.avg_diff * (1 + self.threshold))

      if self.debug:
        print "frame: %s, avg_diff: %.05f, this diff: %.05f, motion: %s" % (self.frame, self.avg_diff, avg_matrix_diff, has_motion)
      
      self.prev_image = image

      if self.frame <= self.calibration_frames:
        print "calibrating..."
        return False
      else:
        if self.frame == self.calibration_frames + 1:
          print "done calibrating. avg_diff set at %.06f" % (self.avg_diff)
        return has_motion

  def push_image(self, image, motion):
    if self.debug:
      path = "%s/%s-%s.jpg" % (self.image_directory, self.frame, motion)
      cv2.imwrite(path, image)
    else:
      # push to S3 here, send SQS
      sys.exit()

  def start(self):
    self.time_started = datetime.datetime.now()
    stream = io.BytesIO()
    with picamera.PiCamera() as camera:
        camera.resolution = (self.width, self.height)
        camera.raw_format = 'rgb'
        time.sleep(3) # let camera adjust
        while True:
          self.frame += 1
          camera.capture(stream, 'raw')
          stream.seek(0)

          fwidth = (self.width + 31) // 32 * 32
          fheight = (self.height + 15) // 16 * 16

          image = np.fromstring(stream.getvalue(), dtype=np.uint8).\
                reshape((fheight, fwidth, 3))[:self.height, :self.width, :]

          image_float = image.astype(np.float) / 255.0
          
          if self.diff(image_float):
            self.push_image(image, motion=True)
            self.last_report = datetime.datetime.now()
          else:
            self.push_image(image, motion=False)

          if self.frame == 40:
            sys.exit()

          # an hour has passed
          #if self.last_report is None or (datetime.datetime.now() - datetime.timedelta(minutes=60)) > self.last_report:
            #self.push_image(image, motion=False)
            #self.last_report = datetime.datetime.now()

          time.sleep(.2)

if __name__ == "__main__":
  eye = PiEye()
  eye.start()
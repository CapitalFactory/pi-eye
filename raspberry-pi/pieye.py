#!/usr/bin/python

import io, os, time, datetime, cv2, sys
import numpy as np

sys.path.append('picamera')
import picamera

class PiEye():
  def __init__(self):
    self.debug = True
    self.image_directory = "images"
    self.last_report = None
    self.prev_image = None
    self.width = 288
    self.height = 192
    self.frame = 0
    self.frac = 0.1       # fraction to update long-term average on each pass
    self.a_thresh = 16.0  # amplitude change detection threshold for any pixel
    self.pc_thresh = 20   # number of pixels required to exceed threshold
    self.avgmax = 3       # long-term average of maximum-pixel-change-value
    self.tfactor = 2      # threshold above max.average diff per frame for motion detect
    self.avgcol = None    # ongoing average of image channel
    self.avgdiff = None   # ongoing average of the image differences

  # http://www.raspberrypi.org/phpBB3/viewtopic.php?t=56478&p=461637
  def diff(self, image):
    if self.prev_image is None:
      self.avgcol = image[:,:,1] # green channel
      self.avgdiff = self.avgcol / 20.0 # obviously a coarse estimate
      self.prev_image = image
      return False
    else:
      newcol = image[:,:,1] # green channel
      self.avgcol = (self.avgcol * (1.0 - self.frac)) + (newcol * self.frac) # average green channel

      matrix_diff = abs(newcol - self.avgcol) # matrix of difference-from-average pixel values
      self.avgdiff = ((1 - self.frac) * self.avgdiff) + (self.frac * matrix_diff)  # long-term average difference

      self.a_thresh = self.tfactor * self.avgmax # adaptive amplitude-of-change threshold
      changed = np.extract(matrix_diff > self.a_thresh, matrix_diff) # extract pixels that have changed past threshold
      count_change = changed.size # get number of changed pixels

      max = np.amax(matrix_diff) # find the biggest (single-pixel) change
      self.avgmax = ((1 - self.frac) * self.avgmax) + (max * self.frac)

      print "a_thresh: %s, avg matrix_diff: %s, different pixels: %s" % (self.a_thresh, np.average(matrix_diff), count_change)
      return count_change > self.pc_thresh # notable change of enough pixels => motion!

  def push_image(self, image):
    if self.debug:
      path = "%s/%s.jpg" % (self.image_directory, self.frame)
      cv2.imwrite(path, image)
    else:
      # push to S3 here, send SQS
      sys.exit()

  def start(self):
    self.time_started = datetime.datetime.now()
    stream = io.BytesIO()
    with picamera.PiCamera() as camera:
        camera.resolution = (self.width, self.height)
        while True:
          self.frame += 1
          camera.capture(stream, format='jpeg', use_video_port=True)
          time.sleep(3)
          stream.seek(0)
          data = np.fromstring(stream.getvalue(), dtype=np.uint8)
          image = cv2.imdecode(data, 1)
          image = image.astype(np.float32)
          self.push_image(image)
          
          if self.diff(image):
            self.last_report = datetime.datetime.now()

          if self.frame > 10:
            sys.exit()

          # an hour has passed
          if self.last_report is None or (datetime.datetime.now() - datetime.timedelta(minutes=60)) > self.last_report:
            self.push_image(image)
            self.last_report = datetime.datetime.now()

if __name__ == "__main__":
  eye = PiEye()
  eye.start()

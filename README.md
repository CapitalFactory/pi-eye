# pi-eye

Raspberry PI-based camera-based instrumentation

Initially, we are building a service that detects when a conference room is in use at the Capital Factory and makes that information available to members.  Because we are using images instead of motion detectors, we can do a lot more interesting things in the future.

Development starts 1/13/14.

Initial Team:

- Joshua Ellinger (CTO/Exemplar Technologies)
- Chris Brown (UT Grad Student)
- Connor Smith (UT CS Student)

# Configuration

**AWS connection**

The script uses boto, so the usual [boto config](http://code.google.com/p/boto/wiki/BotoConfig) locations (`~/.boto`, `/etc/boto.cfg`) are used.
This also means that environment variables `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` with precedence as defined by boto.


# Commands

1. `pi-eye timelapse` (run from this package on the Raspberry Pi) will upload a picture to S3 with ID "pi2" every 15 seconds. Option examples:

        --interval 60   # Upload every 60 seconds
        --rotation 180  # Rotate the camera output by 180° before uploading
        --id pi3        # Use id "pi3" (thus, upload to /images/pi3 instead)

  Currently this is lazy and does not actually upload X seconds, but X seconds + how long it takes to capture and upload the image.

2. `pi-eye app`

    Assuming that you cloned this repo like into `/www/pi-eye`, and installed nginx, you should link in the config file so that you don't have to run the Bottle app as root, but still listen on :80, by having nginx back-proxy requests to the Bottle app listening on :8091 (the default). Run this: `ln -sf /www/pi-eye/proxy.nginx /etc/nginx/sites-enabled/pi-eye`

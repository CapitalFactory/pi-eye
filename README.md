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

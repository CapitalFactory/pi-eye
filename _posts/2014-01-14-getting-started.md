---
published: true
layout: post
title: 'Getting started'
author: Chris Brown
---

This is a quickstart tutorial intended to get your Raspberry Pi up and running as quickly as possible, including:

* Raspbian (the Debian-for-Pi linux distribution)
* Wifi
* Pi camera
* AWS config
* eye-pi


## Raspbian

We'll start with an SD card loaded with [NOOBS Raspbian](http://www.raspberrypi.org/downloads).

In addition to the Raspberry Pi and SD card, you'll need:

* A USB power source (5V, at least 1.0A).

    Many phone chargers, and Apple iPod/iPad/iPhone chargers, will do just fine.

* USB (normal, Type A) to [USB 2.0 Micro B](http://en.wikipedia.org/wiki/File:Micro_USB_phone_charger.jpg) cable.
* USB wifi, like the Edimax EW-7811Un.

    The EW-7811Un is really handy because it doesn't need an external power source, and the Ras Pi distro has the required drivers already)

And, temporarily, you'll need (to borrow) these:

* USB keyboard
* Monitor and HDMI cable

Hook these all up and plug it in.

It'll boot up and send you to an OS config page. The important settings are:

* `3 Enable Boot to Desktop/Scratch`

    You want the "Console Text console" boot option.
    Do **not** boot to the graphical desktop, which requires a mouse.

* `5 Enable Camera`

    Select `<Enable>`

Once you select `<Finish>`, it'll install and start up and should have you enter a password for the `pi` user.

Once you've done that, it'll leave you at a basic shell prompt.

If you selected "boot to graphical desktop" ... find a mouse and a USB hub.


## Wifi

Raspbian has WPA supplicant enabled by default. To configure:

    sudo vim /etc/wpa_supplicant/wpa_supplicant.conf

This snippet should already be at the top:

    ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
    update_config=1

And add this snippet:

    network={
      ssid="My wifi's name"
      psk="keepitsecretkeepit123456"
      proto=RSN
      key_mgmt=WPA-PSK
      pairwise=CCMP
      auth_alg=OPEN
    }

Troubleshooting. In case _your_ Raspberry Pi doesn't have WPA supplicant setup already, you can add it:

    sudo vim /etc/network/interfaces

And make sure it has all of these lines, generally at the end:

    allow-hotplug wlan0
    iface wlan0 inet dhcp
    wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
    iface default inet dhcp

The easiest way to let all these changes sink in and create the connection is to restart the Pi:

    sudo reboot


## Package update

Because the Pi camera is somewhat new, the pre-installed NOOBS setup you got on the SD card may not have all of the required support / drivers. So just to ensure that you're up to date, run:

    sudo apt-get update
    sudo apt-get upgrade -y

(The `-y` option mean "yes I really do want to upgrade packages", as if sudo weren't enough of an indicator.)

This may take a while, 15 minutes or so, depending on your internet connection.

If you have a really old setup distribution and `Enable Camera` wasn't available before, run this:

    sudo raspi-config

Go to `5 Enable Camera`, select `<Enable>`, then `<Finish>`, and reboot again.


**Other packages**

You'll also want to install some other packages:

    sudo apt-get -y install git python-setuptools python-numpy python-opencv


## SSH access

On the pi, run `ifconfig` to show the configured interfaces.

Look for something like `inet addr:192.168.1.150`, though this may be different, based on your wifi.
Usually, though, it'll be something that starts with `192.168.1.` (but not the one that ends with `.255`).

This displays your LAN IP address, which is important. I'll assume it's `192.168.1.150`, for the steps below.


## AWS credentials

**[AWS config](http://code.google.com/p/boto/wiki/BotoConfig), for [boto](http://docs.pythonboto.org/)**

`eye-pi` needs Boto configuration variables to be available in a predictable place. `~/.boto` is one such place.

Create a file like this:

    [Credentials]
    aws_access_key_id = AKASOMETHINGA11INH3X
    aws_secret_access_key = But4hisC4nB3AllK1nds0fCharact3rs/YouKn0

And either scp it:

    scp botoconfig.txt pi@192.168.1.150:.boto

Or create and save it directly on your Pi:

    sudo vim ~/.boto # etc.


## pi-eye package

To get a sane `/usr/local` directory, so that we can install the `pi-eye` console command without root:

    sudo chown -R pi /usr/local

We'll install directly from the source (and not as root!):

    cd ~
    git clone https://github.com/CapitalFactory/pi-eye.git
    cd pi-eye/
    python setup.py develop

The `pi-eye` script should now be on your `PATH`, so that you can run:

    pi-eye timelapse --verbose --interval 60 --id pi-01

This will start up a process that will take a snapshot with your Pi's camera every 60 seconds, immediately uploading them to S3. (That's what the AWS+boto part is for.)

You can run `pi-eye --help` to show other commands, or see the [README](https://github.com/CapitalFactory/pi-eye) for more extensive documentation.

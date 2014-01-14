.. _install3:

========================
Python 3.2+ Installation
========================

There are several ways to install picamera under Python 3.2 (or above), each
with their own advantages and disadvantages. Have a read of the sections below
and select an installation method which conforms to your needs.


.. _raspbian_install3:

Raspbian installation
=====================

If you are using the Raspbian distro, it is best to install picamera using the
system's package manager: apt. This will ensure that picamera is easy to keep
up to date, and easy to remove should you wish to do so. It will also make
picamera available for all users on the system. To install picamera
using apt simply::

    $ sudo apt-get install python3-picamera

To upgrade your installation when new releases are made you can simply use apt's
normal upgrade procedure::

    $ sudo apt-get update
    $ sudo apt-get upgrade

If you ever need to remove your installation::

    $ sudo apt-get remove python3-picamera


.. _user_install3:

User installation
=================

This is the simplest (non-apt) form of installation (though it's also complex
to uninstall should you wish to do so later), but bear in mind that it will
only work for the user you install under. For example, if you install as the
``pi`` user, you will only be able to use picamera as the ``pi`` user. If you
run python as root (e.g. with ``sudo python3``) it will not find the module.
See :ref:`system_install3` below if you require a root installation.

To install as your current user::

    $ sudo apt-get install python3-setuptools
    $ easy_install3 --user picamera

Note that ``easy_install3`` is **not** run with sudo; this is deliberate. To
upgrade your installation when new releases are made::

    $ easy_install3 --user -U picamera

If you ever need to remove your installation::

    $ rm -fr ~/.local/lib/python3.*/site-packages/picamera-*
    $ sed -i -e '/^\.\/picamera-/d' ~/.local/lib/python3.*/site-packages/easy-install.pth

.. note::
    If the removal looks horribly complex, that's because it is! This is the
    reason Python devs tend to prefer virtualenvs. However, I suspect it's
    unlikely that most users will actually care about removing picamera - it's
    a tiny package and has no dependencies so leaving it lying around shouldn't
    cause any issues even if you don't use it anymore.


.. _system_install3:

System installation
===================

A system installation will make picamera accessible to all users (in contrast
to the user installation). It is as simple to perform as the user installation
and equally easy to keep updated but unfortunately, is also difficult to
remove. To perform the installation::

    $ sudo apt-get install python3-setuptools
    $ sudo easy_install3 picamera

To upgrade your installation when new releases are made::

    $ sudo easy_install3 -U picamera

If you ever need to remove your installation::

    $ sudo rm -fr /usr/local/lib/python3.*/dist-packages/picamera-*
    $ sudo sed -i -e '/^\.\/picamera-/d' /usr/local/lib/python3.*/dist-packages/easy-install.pth

.. warning::
    Please be careful when running commands like ``rm -fr`` as root. With a
    simple slip (e.g. changing the final "-" to a space), such a command will
    very quickly delete a lot of things you probably don't want deleted
    (including most of your operating system if you're unlucky enough to be in
    the root directory). Double check what you've typed before hitting Enter!


.. _virtualenv_install3:

Virtualenv installation
=======================

If you wish to install picamera within a virtualenv (useful if you're working
on several Python projects with potentially conflicting dependencies, or you
just like keeping things separate and easily removable)::

    $ sudo apt-get install python3-setuptools python-virtualenv
    $ virtualenv -p python3 sandbox
    $ source sandbox/bin/activate
    (sandbox) $ easy_install picamera

Bear in mind that each time you want to use picamera you will need to activate
the virtualenv before running Python::

    $ source sandbox/bin/activate
    (sandbox) $ python
    >>> import picamera

To upgrade your installation, make sure the virtualenv is activated and just
use easy_install::

    $ source sandbox/bin/activate
    (sandbox) $ easy_install -U picamera

To remove your installation simply blow away the virtualenv::

    $ rm -fr ~/sandbox/


.. _dev_install3:

Development installation
========================

If you wish to develop picamera itself, it is easiest to obtain the source by
cloning the GitHub repository and then use the "develop" target of the Makefile
which will install the package as a link to the cloned repository allowing
in-place development (it also builds a tags file for use with vim/emacs with
exuberant's ctags utility).  The following example demonstrates this method
within a virtual Python environment::

    $ sudo apt-get install build-essential git git-core exuberant-ctags \
        python-virtualenv
    $ virtualenv -p python3 sandbox
    $ source sandbox/bin/activate
    (sandbox) $ git clone https://github.com/waveform80/picamera.git
    (sandbox) $ cd picamera
    (sandbox) $ make develop

To pull the latest changes from git into your clone and update your
installation::

    $ source sandbox/bin/activate
    (sandbox) $ cd picamera
    (sandbox) $ git pull
    (sandbox) $ make develop

To remove your installation blow away the sandbox and the checkout::

    $ rm -fr ~/sandbox/ ~/picamera/

For anybody wishing to hack on the project please understand that although it
is technically written in pure Python, heavy use of :mod:`ctypes` is involved
so the code really doesn't look much like Python - more a sort of horrid
mish-mash of C and Python. The project currently consists of a class
(:class:`PiCamera`) which is a re-implementation of high-level bits of the
``raspistill`` and ``raspivid`` commands using the :mod:`ctypes` based
``libmmal`` header conversion, plus a set of (currently undocumented) encoder
classes which re-implement the encoder callback configuration in the
aforementioned binaries.

Even if you don't feel up to hacking on the code, I'd love to hear suggestions
from people of what you'd like the API to look like (even if the code itself
isn't particularly pythonic, the interface should be)!



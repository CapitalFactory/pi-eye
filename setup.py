from setuptools import setup, find_packages

# helpful things to run before installing: (TODO: make this optional / built-in)
#   sudo apt-get install -qq python-setuptools python-numpy python-opencv
#   easy_install -U picamera ipython

setup(
    name='pi-eye',
    version='0.0.2',
    author='',
    author_email='pi@exemplartech.com',
    url='https://github.com/CapitalFactory/pi-eye',
    keywords='raspberry-pi rpi motion detect image diff classification',
    description='Raspberry PI-based camera-based instrumentation',
    long_description=open('README.md').read(),
    license=open('LICENSE').read(),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Topic :: Multimedia :: Graphics :: Capture :: Digital Camera',
        'Topic :: Scientific/Engineering :: Image Recognition',
    ],
    # setup instructions
    install_requires=[
        'numpy',
        # 'cv2', # aptitude install is not currently recognized
        'picamera',
        'boto',
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'pi-eye = eye.cli:main'
        ],
    },
    include_package_data=True,
)

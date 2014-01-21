import os
import pkg_resources

__version__ = pkg_resources.get_distribution('pi-eye').version
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

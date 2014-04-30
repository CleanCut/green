from green.plugin import Green
from green.cmdline import main
import os.path

__version__ = open(os.path.join(os.path.dirname(__file__), 'VERSION')).read().strip()

# So pyflakes will stop complaining about disuse...
Green
main

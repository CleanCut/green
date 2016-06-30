from __future__ import unicode_literals # progma nocover
import os.path # progma nocover
import sys # progma nocover

try: # progma nocover
    import coverage
except: # pragma nocover
    coverage = None

__version__ = open(os.path.join(os.path.dirname(__file__), 'VERSION')).read().strip() # progma nocover
if sys.version_info[0] == 2: # pragma nocover
    from __builtin__ import unicode  # just so the linter stops complaining
    __version__ = unicode(__version__)


def pretty_version(): # progma nocover
    python_version = ".".join([str(x) for x in sys.version_info[0:3]])
    ver_str = "Green {}".format(__version__)
    if coverage:
        ver_str = "{}, Coverage {}".format(ver_str, coverage.__version__)
    ver_str = "{}, Python {}".format(ver_str, python_version)
    return ver_str

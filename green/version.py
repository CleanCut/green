from __future__ import unicode_literals  # pragma: no cover
import os.path  # pragma nocover
import sys  # pragma nocover

import coverage  # pragma: no cover

with open(
    os.path.join(os.path.dirname(__file__), "VERSION")
) as vfile:  # pragma nocover
    __version__ = vfile.read().strip()
if sys.version_info[0] == 2:  # pragma nocover
    from __builtin__ import unicode  # just so the linter stops complaining

    __version__ = unicode(__version__)


def pretty_version():  # pragma nocover
    python_version = ".".join([str(x) for x in sys.version_info[0:3]])
    ver_str = "Green {}, Coverage {}, Python {}".format(
        __version__, coverage.__version__, python_version
    )
    return ver_str

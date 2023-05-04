import pathlib  # pragma nocover
import sys  # pragma nocover

import coverage  # pragma: no cover


__version__ = (
    (pathlib.Path(__file__).parent / "VERSION").read_text(encoding="utf-8").strip()
)


def pretty_version():  # pragma nocover
    python_version = ".".join([str(x) for x in sys.version_info[0:3]])
    ver_str = "Green {}, Coverage {}, Python {}".format(
        __version__, coverage.__version__, python_version
    )
    return ver_str

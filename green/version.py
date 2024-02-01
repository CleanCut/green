from __future__ import annotations  # pragma: no cover

import pathlib  # pragma: no cover
import sys  # pragma: no cover

import coverage  # pragma: no cover

__version__ = (
    (pathlib.Path(__file__).parent / "VERSION").read_text(encoding="utf-8").strip()
)  # pragma: no cover


def pretty_version():  # pragma: no cover
    python_version = ".".join(str(x) for x in sys.version_info[0:3])
    return (
        f"Green {__version__}, Coverage {coverage.__version__}, Python {python_version}"
    )

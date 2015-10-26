import os
import shlex
import struct
import platform
import subprocess

# This module was adapted from https://gist.github.com/jtriley/1108174 as it was
# on 2015-10-26


def getTerminalSize(): # pragma: no cover
    """
    Get width and height of console. Works on Linux, OS X, Windows, and Cygwin.

    Returns (width, height) tuple, or (None, None) if size can't be determined.

    """
    current_os = platform.system()
    tuple_xy = None
    if current_os == 'Windows':
        tuple_xy = _getTerminalSizeWindows()
        if tuple_xy is None:
            tuple_xy = _getTerminalSizeTput()
            # needed for window's python in cygwin's xterm!
    if current_os in ['Linux', 'Darwin'] or current_os.startswith('CYGWIN'):
        tuple_xy = _getTerminalSizeLinux()
    if tuple_xy is None:
        return (None, None)
    return tuple_xy


def _getTerminalSizeWindows(): # pragma: no cover
    try:
        from ctypes import windll, create_string_buffer
        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12
        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (bufx, bufy, curx, cury, wattr, left, top, right, bottom, maxx,
                    maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            sizex = right - left + 1
            sizey = bottom - top + 1
            return sizex, sizey
    except:
        pass


def _getTerminalSizeTput(): # pragma: no cover
    try:
        cols = int(subprocess.check_call(shlex.split('tput cols')))
        rows = int(subprocess.check_call(shlex.split('tput lines')))
        return (cols, rows)
    except:
        pass


def _getTerminalSizeLinux(): # pragma: no cover
    def ioctl_GWINSZ(fd):
        try:
            import fcntl
            import termios
            cr = struct.unpack('hh',
                               fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
            return cr
        except:
            pass
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (os.environ['LINES'], os.environ['COLUMNS'])
        except:
            return None
    return int(cr[1]), int(cr[0])

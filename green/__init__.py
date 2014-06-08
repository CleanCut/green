from .cmdline import main
import os

try:
    import coverage
    os.environ['COVERAGE_PROCESS_START'] = "TRUE"
    coverage.process_startup()
except: # pragma: no cover
    pass

main

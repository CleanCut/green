from __future__ import unicode_literals
from __future__ import print_function

from unittest.signals import (
        registerResult, installHandler, removeResult)
import warnings

try: # pragma: no cover
    import coverage
except: # pragma: no cover
    coverage = None

from green.loader import toProtoTestList, toParallelTestTargets
from green.output import GreenStream
from green.result import GreenTestResult
from green.subprocess import LoggingDaemonlessPool, poolRunner

from collections import defaultdict, namedtuple

import multiprocessing


_AsyncChunk = namedtuple("_AsyncChunk", "suite_name queue")


def run(suite, stream, args):
    """
    Run the given test case or test suite with the specified arguments.

    Any args.stream passed in will be wrapped in a GreenStream
    """
    if not issubclass(GreenStream, type(stream)):
        stream = GreenStream(stream)
    result = GreenTestResult(args, stream)

    # Note: Catching SIGINT isn't supported by Python on windows (python
    # "WONTFIX" issue 18040)
    installHandler()
    registerResult(result)

    with warnings.catch_warnings():
        if args.warnings:
            # if args.warnings is set, use it to filter all the warnings
            warnings.simplefilter(args.warnings)
            # if the filter is 'default' or 'always', special-case the
            # warnings from the deprecated unittest methods to show them
            # no more than once per module, because they can be fairly
            # noisy.  The -Wd and -Wa flags can be used to bypass this
            # only when args.warnings is None.
            if args.warnings in ['default', 'always']:
                warnings.filterwarnings('module',
                        category=DeprecationWarning,
                        message='Please use assert\w+ instead.')

        result.startTestRun()

        tests = [_AsyncChunk(t, multiprocessing.Manager().Queue()) for t in toParallelTestTargets(suite, args.targets)]
        pool = LoggingDaemonlessPool(processes=args.subprocesses or None)
        if tests:
            async_responses = []
            for index, test_chunk in enumerate(tests):
                if args.run_coverage:
                    coverage_number = index + 1
                else:
                    coverage_number = None
                pool.apply_async(
                    poolRunner,
                    (test_chunk.suite_name, test_chunk.queue, coverage_number, args.omit_patterns))
            pool.close()
            for test_chunk in tests:
                while True:
                    msg = test_chunk.queue.get()

                    # Sentinel value, we're done
                    if not msg:
                        break
                    else:
                        # Result guarunteed after this message
                        result.startTest(msg)
                        result.addProtoTestResult(test_chunk.queue.get())

                if result.shouldStop:
                    break

                # Prints out the white 'processing...' version of the output
                # result.startTest(test)
                # This blocks until the worker who is processing this
                # particular test actually finishes
                # try:
                #     for response in async_response.get():
                #         result.addProtoTestResult(response)
                # except KeyboardInterrupt: # pragma: no cover
                #     result.shouldStop = True
                # if result.shouldStop:
                #     break
        pool.terminate()
        pool.join()

        result.stopTestRun()

    removeResult(result)

    return result

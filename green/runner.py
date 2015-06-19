from __future__ import unicode_literals
from __future__ import print_function

from sys import modules
from unittest.signals import (
        registerResult, installHandler, removeResult)
import warnings

try: # pragma: no cover
    import coverage
except: # pragma: no cover
    coverage = None

from green.exceptions import InitializerOrFinalizerError
from green.loader import toProtoTestList
from green.output import GreenStream
from green.process import LoggingDaemonlessPool, poolRunner
from green.result import GreenTestResult



class InitializerOrFinalizer:
    """
    I represent a command that will be run as either the initializer or the
    finalizer for a worker process.  The only reason I'm a class instead of a
    function is so that I can be instantiated at the creation time of the Pool
    (with the user's customized command to run), but actually run at the
    appropriate time.
    """
    def __init__(self, dotted_function):
        self.module_part = '.'.join(dotted_function.split('.')[:-1])
        self.function_part = '.'.join(dotted_function.split('.')[-1:])


    def __call__(self, *args):
        if not self.module_part:
            return
        try:
            __import__(self.module_part)
            loaded_function = getattr(modules[self.module_part], self.function_part, None)
        except Exception as e:
            raise InitializerOrFinalizerError("Couldn't load '{}' - got: {}"
                    .format(self.function_part, str(e)))
        if not loaded_function:
            raise InitializerOrFinalizerError(
                    "Loaded module '{}', but couldn't find function '{}'"
                    .format(self.module_part, self.function_part))
        try:
            loaded_function()
        except Exception as e:
            raise InitializerOrFinalizerError("Error running '{}' - got: {}"
                    .format(self.function_part, str(e)))



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
        if args.warnings: # pragma: no cover
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

        tests = toProtoTestList(suite)
        pool = LoggingDaemonlessPool(processes=args.processes or None,
                initializer=InitializerOrFinalizer(args.initializer),
                finalizer=InitializerOrFinalizer(args.finalizer))
        if tests:
            async_responses = []
            for index, test in enumerate(tests):
                if args.run_coverage:
                    coverage_number = index + 1
                else:
                    coverage_number = None
                async_responses.append(pool.apply_async(
                    poolRunner,
                    (test.dotted_name, coverage_number, args.omit_patterns)))
            pool.close()
            for test, async_response in zip(tests, async_responses):
                # Prints out the white 'processing...' version of the output
                result.startTest(test)
                # This blocks until the worker who is processing this
                # particular test actually finishes
                try:
                    result.addProtoTestResult(async_response.get())
                except KeyboardInterrupt: # pragma: no cover
                    result.shouldStop = True
                if result.shouldStop: # pragma: no cover
                    break
        pool.terminate()
        pool.join()

        result.stopTestRun()

    removeResult(result)

    return result

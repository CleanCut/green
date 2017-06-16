from __future__ import unicode_literals

import unittest



class TestLoadTests(unittest.TestCase):
    def _test_that_will_fail(self):
        self.fail("load_tests was not executed.")
    test_load_tests = _test_that_will_fail

def load_tests(loader, tests, pattern):
    setattr(TestLoadTests, 'test_load_tests', lambda self: None)
    return loader.loadTestsFromTestCase(TestLoadTests)

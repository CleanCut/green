import unittest

from green.version import __version__



class TestVersion(unittest.TestCase):

    def test_version_type(self):
        "__version__ is a string"
        self.assertEqual(type(__version__), type(''))


    def test_version_set(self):
        "__version__ is not blank"
        self.assertTrue(len(__version__) > 0)

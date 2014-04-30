import unittest

from green import __version__



class TestVersion(unittest.TestCase):

    def test_version_type(self):
        self.assertEqual(type(__version__), type(''))


    def test_version_set(self):
        self.assertTrue(len(__version__) > 0)

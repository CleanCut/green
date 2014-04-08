import unittest

from green.version import version



class TestVersion(unittest.TestCase):


    def test_version_type(self):
        self.assertEqual(type(version), type(''))


    def test_version_set(self):
        self.assertTrue(len(version) > 0)

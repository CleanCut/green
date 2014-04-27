import unittest
#try:
#    from unittest.mock import MagicMock
#except:
#    from mock import MagicMock

from green.plugin import Green


class TestNose2Plugin(unittest.TestCase):


    def testGreenExists(self):
        Green

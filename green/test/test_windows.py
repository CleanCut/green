import platform
import unittest



class TestWindows(unittest.TestCase):


    def setUp(self):
        if platform.system() != 'Windows':
            self.skipTest('This test is for windows-specific behavior.')


    def test_colorOutput(self):
        """
        Color output functions on windows
        """
        self.assertTrue(False)


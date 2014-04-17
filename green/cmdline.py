import nose
import os
import sys
from green import Green

def main():
    os.environ['NOSE_WITH_GREEN'] = '1'
    nose.main(addplugins=[Green()], argv=sys.argv)

import copy
import multiprocessing
import os
from pathlib import PurePath
import subprocess
import sys
import tempfile
from textwrap import dedent
import unittest

try:
    from unittest.mock import MagicMock
except:
    from mock import MagicMock

from green import cmdline


class TestFinalizer(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def test_finalizer(self):
        """
        Test that the finalizer works on Python 3.8+
        """
        sub_tmpdir = tempfile.mkdtemp(dir=self.tmpdir)
        for i in range(multiprocessing.cpu_count() * 2):
            fh = open(os.path.join(sub_tmpdir, f"test_finalizer{i}.py"), "w")
            fh.write(
                dedent(
                    f"""
                import unittest
                class Pass{i}(unittest.TestCase):
                    def test_pass{i}(self):
                        pass
                def msg():
                    print("finalizer worked")
                """
                )
            )
            fh.close()
        args = [
            sys.executable,
            "-m",
            "green.cmdline",
            "--finalizer=test_finalizer0.msg",
            "--maxtasksperchild=1",
        ]
        pythonpath = str(PurePath(__file__).parent.parent.parent)

        env = copy.deepcopy(os.environ)
        env["PYTHONPATH"] = pythonpath

        output = subprocess.run(
            args,
            cwd=sub_tmpdir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            timeout=10,
        ).stdout.decode("utf-8")
        self.assertIn("finalizer worked", output)

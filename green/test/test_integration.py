import copy
import multiprocessing
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from textwrap import dedent
import unittest


class TestFinalizer(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_finalizer(self) -> None:
        """
        Test that the finalizer works on Python 3.8+.
        """
        sub_tmpdir = pathlib.Path(tempfile.mkdtemp(dir=self.tmpdir))
        for i in range(multiprocessing.cpu_count() * 2):
            finalizer_path = sub_tmpdir / f"test_finalizer{i}.py"
            finalizer_path.write_text(
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
        args = [
            sys.executable,
            "-m",
            "green.cmdline",
            "--finalizer=test_finalizer0.msg",
            "--maxtasksperchild=1",
        ]
        pythonpath = str(pathlib.Path(__file__).parent.parent.parent)

        env = copy.deepcopy(os.environ)
        env["PYTHONPATH"] = pythonpath

        output = subprocess.run(
            args,
            cwd=str(sub_tmpdir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            timeout=10,
            encoding="utf-8",
            check=True,
        ).stdout
        self.assertIn("finalizer worked", output)

import sys
from subprocess import PIPE, STDOUT, Popen


def test_circdeploy_help():
    p = Popen(
        [sys.executable, "-m", "circdeploy", "--help"], stdout=PIPE, stderr=STDOUT
    )
    out, _ = p.communicate()
    assert "Usage: python -m circdeploy" in out.decode("utf-8", "replace")

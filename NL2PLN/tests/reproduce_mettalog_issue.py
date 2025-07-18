"""
Utility script to reproduce the intermittent ``kb_ref == ''`` failure
in MettalogHandler by forcing very small reads from the mettalog pipe.

Run:
    python NL2PLN/tests/reproduce_mettalog_issue.py
"""

import os
from NL2PLN.metta.mettalog_handler import MettalogHandler

# ---------------------------------------------------------------------------
# Monkey-patch os.read so that each call returns at most 3 bytes.
# This splits the ``metta+>`` prompt into several chunks, making the
# leftover-bytes race condition appear almost every time.
# ---------------------------------------------------------------------------
_original_read = os.read


def _slow_read(fd: int, n: int) -> bytes:      # noqa: D401
    """Patched version of os.read that returns ≤ 3 bytes per call."""
    return _original_read(fd, min(n, 3))


os.read = _slow_read  # type: ignore

# ---------------------------------------------------------------------------
# Test loop
# ---------------------------------------------------------------------------


def run_test(runs: int = 500) -> None:
    failures = 0
    for i in range(runs):
        h = MettalogHandler(read_only=False)   # init-kb is executed here
        if not h.kb_ref:                       # '' means the bug has surfaced
            print(f"FAIL on run {i}")
            failures += 1
        h.close()
    print(f"{failures} / {runs} runs failed")


if __name__ == "__main__":
    try:
        run_test()
    finally:
        # restore original behaviour
        os.read = _original_read  # type: ignore

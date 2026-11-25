"""Publish the drawn front page into the make.fun output directory.

Copies entry.png (which sits next to this script) into $MAKEFUN_OUTPUT_DIR,
defaulting to /output, then reports the written file's size and sha256 and
verifies the copy is byte-identical to the source.
"""

import hashlib
import os
import shutil
import sys


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main():
    source = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    source_size = os.path.getsize(source)
    print("entry:", os.path.basename(source), source_size, "bytes")
    if source_size >= 1048576:
        print("too large")
        return 1
    target_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(target_dir, exist_ok=True)
    target = os.path.join(target_dir, os.path.basename(source))
    shutil.copyfile(source, target)
    size = os.path.getsize(target)
    copied = digest(target)
    print("wrote", target, size, "bytes")
    print("sha256", copied)
    if copied != digest(source):
        print("checksum mismatch")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

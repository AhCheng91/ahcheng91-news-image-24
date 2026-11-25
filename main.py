"""Publish the drawn front page to the make.fun output directory.

entry.png sits beside this script; it is refused when 1 MiB or larger, else
copied into $MAKEFUN_OUTPUT_DIR (/output by default, created when missing).
The copy's size and sha256 are printed and checked against the source:
identical exits 0, different exits 1.
"""
import hashlib
import os
import shutil
import sys


def digest(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    size = os.path.getsize(src)
    print("entry:", os.path.basename(src), size, "bytes")
    if size >= 1048576:
        print("too large")
        return 1
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    dst = os.path.join(outdir, os.path.basename(src))
    shutil.copyfile(src, dst)
    print("wrote", dst, os.path.getsize(dst), "bytes")
    print("sha256", digest(dst))
    if digest(dst) != digest(src):
        print("sha256 mismatch")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

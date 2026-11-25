"""Check the front page entry.png and the files the repository keeps.

Run from the repository root:

    python3 tools/check_entry.py

Prints one line per check and exits 0 only when every check passes.
"""

import os
import struct
import subprocess
import sys
import tempfile
import zlib

from PIL import Image

MAX_SIDE = 1024
MAX_BYTES = 1048576
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
REQUIRED_FILES = ("entry.png", "main.py", "README.md")

failures = []


def report(name, ok, detail):
    print("%-4s %-22s %s" % ("ok" if ok else "FAIL", name, detail))
    if not ok:
        failures.append(name)


def check_image():
    try:
        with Image.open("entry.png") as image:
            size = image.size
            mode = image.mode
    except Exception as exc:
        report("image", False, "cannot open entry.png: %s" % exc)
        return
    print("     size=%dx%d mode=%s" % (size[0], size[1], mode))
    ok = size[0] <= MAX_SIDE and size[1] <= MAX_SIDE and mode == "RGB"
    report("image", ok, "size and mode within limits" if ok else
           "want at most %dx%d in RGB" % (MAX_SIDE, MAX_SIDE))


def check_file_size():
    size = os.path.getsize("entry.png")
    print("     %d bytes" % size)
    report("file size", size <= MAX_BYTES, "at most %d bytes" % MAX_BYTES)


def check_chunks():
    with open("entry.png", "rb") as handle:
        data = handle.read()
    pos = 0
    problems = []
    seen_iend = False
    seen_ihdr = False
    while pos < len(data):
        if data[pos:pos + 8] != PNG_SIGNATURE:
            problems.append("bad signature at byte %d" % pos)
            break
        offset = 8
        while offset < len(data):
            if offset + 8 > len(data):
                problems.append("truncated chunk header at byte %d" % offset)
                break
            length, ctype = struct.unpack(">I4s", data[offset:offset + 8])
            try:
                name = ctype.decode("ascii")
            except UnicodeDecodeError:
                problems.append("non-ASCII chunk type at byte %d" % offset)
                break
            if not name.isalpha() or not name.isupper():
                problems.append("bad chunk type %r at byte %d" % (name, offset))
                break
            if offset + 12 + length > len(data):
                problems.append("chunk %s runs past end of file" % name)
                break
            body = data[offset + 8:offset + 8 + length]
            stored = struct.unpack(
                ">I", data[offset + 8 + length:offset + 12 + length]
            )[0]
            actual = zlib.crc32(ctype + body) & 0xFFFFFFFF
            if stored != actual:
                problems.append(
                    "bad CRC-32 for chunk %s at byte %d" % (name, offset)
                )
                break
            if not seen_ihdr and name != "IHDR":
                problems.append("first chunk is %s, not IHDR" % name)
                break
            seen_ihdr = seen_ihdr or name == "IHDR"
            if name == "IEND":
                seen_iend = True
                offset += 12 + length
                break
            offset += 12 + length
        pos = len(data)
    if not seen_iend:
        problems.append("no IEND chunk")
    report("png chunks", not problems,
           "signature, lengths, types and CRCs good, IEND present"
           if not problems else "; ".join(problems))


def check_files():
    on_disk = set()
    for root, dirs, files in os.walk("."):
        dirs[:] = sorted(d for d in dirs if d != ".git")
        for name in files:
            on_disk.add(os.path.relpath(os.path.join(root, name), "."))
    listed = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    in_git = set(listed)
    print("     disk: %s" % ", ".join(sorted(on_disk)))
    print("     git:  %s" % ", ".join(sorted(in_git)))
    missing_disk = [f for f in REQUIRED_FILES if f not in on_disk]
    missing_git = [f for f in REQUIRED_FILES if f not in in_git]
    problems = ["%s not on disk" % f for f in missing_disk]
    problems += ["%s not in git" % f for f in missing_git]
    report("files", not problems,
           "entry.png, main.py and README.md on disk and in git"
           if not problems else "; ".join(problems))


def check_copy():
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, MAKEFUN_OUTPUT_DIR=tmp)
        result = subprocess.run(
            [sys.executable, "main.py"], capture_output=True, text=True, env=env
        )
        written = os.path.join(tmp, "entry.png")
        if result.returncode != 0:
            report("program copy", False,
                   "main.py exited %d: %s" % (
                       result.returncode, result.stderr.strip() or result.stdout.strip()))
            return
        if not os.path.isfile(written):
            report("program copy", False, "main.py wrote no entry.png")
            return
        with open(written, "rb") as handle:
            copy = handle.read()
        with open("entry.png", "rb") as handle:
            original = handle.read()
        ok = copy == original
        report("program copy", ok,
               "main.py's PNG is byte-identical to entry.png" if ok
               else "main.py's PNG differs from entry.png")


def main():
    check_image()
    check_file_size()
    check_chunks()
    check_files()
    check_copy()
    if failures:
        print("failed:", ", ".join(failures))
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

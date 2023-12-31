#!/usr/bin/env python3
"""
EPUB reader for the command line.

Usage:
    reader.py <file> | less

References:

    epub spec -- https://www.w3.org/TR/epub-overview-33/

    ebooklib -- https://github.com/aerkalov/ebooklib
    epy -- https://github.com/wustho/epy

"""

# from pprint import pprint
import subprocess
import sys
import textwrap
import xml.etree.ElementTree as ET
import zipfile

# FULL_WIDTH, FULL_HEIGHT = os.get_terminal_size()

# shutil allows piping output (e.g. to less), but just uses the fallback dims
# FULL_WIDTH, FULL_HEIGHT = shutil.get_terminal_size()

# https://stackoverflow.com/a/943921
# only subprocess (or os.popen) can do this reliably
FULL_HEIGHT, FULL_WIDTH = subprocess.check_output(["stty", "size"]).split()
FULL_HEIGHT = int(FULL_HEIGHT)
FULL_WIDTH = int(FULL_WIDTH)

# main_scr = curses.initscr()
# curses.curs_set(0)
# self.height, self.width = main_scr.getmaxyx()

HORIZ_PADDING = 0.2
HORIZ_PADDING = int(FULL_WIDTH * HORIZ_PADDING)
WIDTH = FULL_WIDTH - 2 * HORIZ_PADDING

# VERT_PADDING = HORIZ_PADDING
# VERT_PADDING = int(FULL_HEIGHT * VERT_PADDING)
# HEIGHT = FULL_HEIGHT - 2 * VERT_PADDING

file = sys.argv[1]

LINES = []

# https://github.com/aerkalov/ebooklib/blob/1cb3d2c251f82c4702c2aff0ed7aea375babf251/ebooklib/epub.py#L1716C30-L1716C30
with zipfile.ZipFile(
    file,
    "r",
    compression=zipfile.ZIP_DEFLATED,
    allowZip64=True,
) as zf:
    # pprint(zf.namelist())
    xml_bytes = zf.read("OPS/main0.xml")

    # fromstring returns str; force it into a Tree order to be able to iterate
    tree = ET.ElementTree(ET.fromstring(xml_bytes.decode()))

    LINES.append("-" * FULL_WIDTH)
    LINES.append("")
    for c in tree.iter():
        if c.text and c.text.strip():
            LINES.append(
                textwrap.fill(
                    # in an epub, lines are broken for you. we discard them and
                    # reflow to suit our terminal size
                    " ".join(c.text.split("\n")),
                    # indent adds the left pad while maintaining width
                    # (essentially doubling the right pad); correct this by
                    # reclaiming from the right pad
                    WIDTH + HORIZ_PADDING,
                    initial_indent=" " * HORIZ_PADDING,
                    subsequent_indent=" " * HORIZ_PADDING,
                )
            )
            LINES.append("")
    LINES.append("-" * FULL_WIDTH)

print("\n".join(LINES))

# TODO:
# parse arbitrary zip structure
# parse arbitrary xml/html
# argparse (padding)
# keybinds
# cache (by file hash)
# link navigation

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
import subprocess
import sys
import textwrap
import zipfile

from bs4 import BeautifulSoup

# import xml.etree.ElementTree as ET
# from pprint import pprint

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

IGNORED_CLASSES = {
    "preface",
    "otherbooks",
    "style",
    # "span",
    # "p",
    # "em",
}


class Reader:
    def __init__(self, file):
        self.file = file

    @staticmethod
    def is_xml(f: str):
        """Check if path looks like a document to be parsed. Does not check xml
        contents."""
        return f.startswith("O") and (f.endswith("ml") or f.endswith(".htm"))

    def display_xml_tree(self, xml_tree: BeautifulSoup):
        lines = [x.text for x in xml_tree.find_all("p")]
        for line in lines:
            line = " ".join(line.split("\n"))
            print(
                textwrap.fill(
                    # in an epub, lines are broken for you. we discard them and
                    # reflow to suit our terminal size
                    line,
                    # indent adds the left pad while maintaining width (essentially
                    # doubling the right pad); correct this by reclaiming from the
                    # right pad
                    WIDTH + HORIZ_PADDING,
                    initial_indent=" " * HORIZ_PADDING,
                    subsequent_indent=" " * HORIZ_PADDING,
                )
            )
            print()

    def read(self):
        # https://github.com/aerkalov/ebooklib/blob/1cb3d2c251f82c4702c2aff0ed7aea375babf251/ebooklib/epub.py#L1716C30-L1716C30
        with zipfile.ZipFile(
            self.file,
            "r",
            compression=zipfile.ZIP_DEFLATED,
            allowZip64=True,
        ) as zf:
            # pprint(zf.namelist())
            xmls = [f for f in zf.namelist() if self.is_xml(f)]
            for i, xml_path in enumerate(xmls):
                xml_str = zf.read(xml_path)
                xml_tree = BeautifulSoup(xml_str, features="xml")

                if xml_tree.div["class"] in IGNORED_CLASSES:
                    continue

                self.display_xml_tree(xml_tree)
                # print(xml_tree.div["class"])
                break
                input(f"Next ({i+2}) -> ")


reader = Reader(sys.argv[1])
reader.read()

# TODO:
# argparse (user-defined padding)
# keybinds (potentially curses)
# cache (by file hash + xml file + position (fraction))
# link navigation

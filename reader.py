#!/usr/bin/env python3
"""
EPUB reader for the command line.

Usage:
    reader.py <file>

References:

    epub spec -- https://www.w3.org/TR/epub-overview-33/

    ebooklib -- https://github.com/aerkalov/ebooklib
    epy -- https://github.com/wustho/epy

"""
# import subprocess
import os
import sys
import textwrap
import zipfile

from bs4 import BeautifulSoup
from readchar import readchar

# os is simplest, but cannot be piped
FULL_WIDTH, FULL_HEIGHT = os.get_terminal_size()

# shutil allows piping output (e.g. to less), but just uses the fallback dims
# FULL_WIDTH, FULL_HEIGHT = shutil.get_terminal_size()

# # https://stackoverflow.com/a/943921
# # only subprocess (or os.popen) can do this reliably
# FULL_HEIGHT, FULL_WIDTH = subprocess.check_output(["stty", "size"]).split()

FULL_HEIGHT = int(FULL_HEIGHT)
FULL_WIDTH = int(FULL_WIDTH)

# main_scr = curses.initscr()
# curses.curs_set(0)
# self.height, self.width = main_scr.getmaxyx()

HORIZ_PADDING = 0.2
HORIZ_PADDING = int(FULL_WIDTH * HORIZ_PADDING)
WIDTH = FULL_WIDTH - 2 * HORIZ_PADDING

# VERT_PADDING = 0.1
# VERT_PADDING = int(FULL_HEIGHT * VERT_PADDING)
# HEIGHT = FULL_HEIGHT - 2 * VERT_PADDING

VERT_PADDING = 1
HEIGHT = FULL_HEIGHT - 2 * VERT_PADDING

IGNORED_CLASSES = {
    "preface",
    "otherbooks",
    "style",
    # "span",
    # "p",
    # "em",
}


class Reader:
    def __init__(self, file: str):
        self.file: str = file

        self.xml_pos: int = 0
        self.curr_xml_path: str = ""

        self.line_pos: int = 0  # can be float, if restored from cache
        self.xml_change: int = 0
        self.xml_lines: list[str] = []

        self.wide_spacing: bool = False
        self.debug: bool = True

    def __len__(self) -> int:
        return len(self.xml_lines)

    @staticmethod
    def is_xml(f: str):
        """Check if path looks like a document to be parsed. Does not check xml
        contents."""
        return f.startswith("O") and (f.endswith("ml") or f.endswith(".htm"))

    @staticmethod
    def format_para(para) -> str:
        para = " ".join(para.split("\n"))
        return textwrap.fill(
            # in an epub, lines are broken for you. we discard them and reflow
            # to suit our terminal size
            text=para,
            # indent adds the left pad while maintaining width (essentially
            # doubling the right pad); correct this by reclaiming from the
            # right pad
            width=WIDTH + HORIZ_PADDING,
            initial_indent=" " * HORIZ_PADDING,
            subsequent_indent=" " * HORIZ_PADDING,
        )

    def restore_line_pos(self):
        self.line_pos = int(self.line_pos * len(self))

    def navigate(self, char: str):
        match char:
            case "n":
                self.xml_change = 1
            case "p":
                self.xml_change = -1
            case "g":
                self.line_pos = 0
            case "G":
                self.line_pos = len(self) - HEIGHT
            case "j":
                self.line_pos = min(self.line_pos + 1, len(self) - HEIGHT)
            case "k":
                self.line_pos = max(self.line_pos - 1, 0)
            case "J":
                self.line_pos = min(self.line_pos + HEIGHT // 2, len(self) - HEIGHT)
            case "K":
                self.line_pos = max(self.line_pos - HEIGHT // 2, 0)
            case "x":
                self.zf.close()
                # TODO: cache (file hash + xml file + position (fraction))
                print(self.curr_xml_path, self.line_pos, len(self))
                sys.exit()

            # case _:
            #     print(char)
            #     raise ValueError

    def display(self):
        print("\n".join(self.xml_lines[self.line_pos : self.line_pos + HEIGHT]))
        if self.debug:
            print(self.file, self.line_pos, self.line_pos + HEIGHT)
        else:
            print()

    def display_xml_tree(
        self,
        xml_tree: BeautifulSoup,
    ):
        """Extract the complete text content of an xml file, format as a single
        reflowed string, then divide into lines to be scrolled."""
        paragraphs: list[str] = [x.text for x in xml_tree.find_all("p")]
        self.xml_lines = [""] * VERT_PADDING
        for para in paragraphs:
            # split -again-, because we want to be able to scroll
            self.xml_lines += self.format_para(para).split("\n")
            if self.wide_spacing:
                self.xml_lines += ["\n"]
            else:
                self.xml_lines += [""]

        # restore line_pos from fraction; can only be done after xml_lines is
        # prepared
        if isinstance(self.line_pos, float):
            self.restore_line_pos()

        self.display()
        while self.xml_change == 0:
            char = readchar()
            self.navigate(char)
            self.display()
        self.line_pos = 0
        self.xml_pos += self.xml_change
        self.xml_change = 0

    def read(self):
        # https://github.com/aerkalov/ebooklib/blob/1cb3d2c251f82c4702c2aff0ed7aea375babf251/ebooklib/epub.py#L1716C30-L1716C30
        os.system("clear")
        self.zf = zipfile.ZipFile(
            self.file,
            "r",
            compression=zipfile.ZIP_DEFLATED,
            allowZip64=True,
        )  # as zf:
        xmls = [f for f in self.zf.namelist() if self.is_xml(f)]

        if self.curr_xml_path:
            self.xml_pos = xmls.index(self.curr_xml_path)
        else:
            self.xml_pos = 0

        # iterators in python -cannot- go backwards, so there is no point in
        # using them

        while 0 <= self.xml_pos < len(xmls):
            self.curr_xml_path = xmls[self.xml_pos]
            xml_str = self.zf.read(self.curr_xml_path)
            xml_tree = BeautifulSoup(xml_str, features="xml")

            # TODO: potentially means that any ignored xml between normal xmls
            # will prevent backward iteration
            if (
                hasattr(xml_tree, "div")
                and xml_tree.div.get("class") in IGNORED_CLASSES
                or not xml_tree.find_all("p")
            ):
                self.xml_pos += 1
                continue

            self.display_xml_tree(xml_tree)

        print("end")
        # remove cache


reader = Reader(sys.argv[1])
reader.read()

# TODO:
# argparse (user-defined padding)
# link navigation (out of scope?)

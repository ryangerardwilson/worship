#!/usr/bin/env python3
"""Entry point for the worship CLI."""

from __future__ import annotations

import os
from pathlib import Path
import sys

from _version import __version__
from rgw_cli_contract import AppSpec, resolve_install_script_path, run_app

INSTALL_SCRIPT = resolve_install_script_path(__file__)
HELP_TEXT = """worship

flags:
  worship -h
    show this help
  worship -v
    print the installed version
  worship -u
    upgrade the installed app

features:
  launch the course selector in doc mode
  # worship
  worship

  list, open, and delete saved bookmarks
  # worship -b -l | worship -b <number> | worship -b -d <number>
  worship -b -l
  worship -b 2
  worship -b -d 2
"""


def _run_app(argv: list[str]) -> int:
    import curses

    from modules.course_parser import CourseParser
    from modules.flag_handler import handle_bookmark_flags
    from modules.menu import Menu

    os.environ.setdefault("TERM", "xterm-256color")
    os.environ.setdefault("ESCDELAY", "25")

    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)
    courses_dir = os.path.join(script_dir, "courses")

    parser = CourseParser(courses_dir)
    courses = parser.parse_courses()
    if not courses:
        print("No valid courses found in the courses directory.")
        return 1

    handle_bookmark_flags(courses)

    doc_mode = True
    if "-d" in argv or "--doc" in argv:
        doc_mode = True

    menu = Menu(courses, doc_mode=doc_mode)
    try:
        curses.wrapper(menu.run)
    except KeyboardInterrupt:
        return 0
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    spec = AppSpec(
        app_name="worship",
        version=__version__,
        help_text=HELP_TEXT,
        install_script_path=INSTALL_SCRIPT,
        no_args_mode="dispatch",
    )
    return run_app(spec, args, _run_app)


if __name__ == "__main__":
    raise SystemExit(main())

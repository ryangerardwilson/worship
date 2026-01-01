# ~/Apps/rtutor/main.py
#!/usr/bin/env python3
import curses
import sys
import os
from modules.menu import Menu
from modules.course_parser import CourseParser
from modules.flag_handler import handle_bookmark_flags

# Set TERM explicitly for consistent color support
os.environ['TERM'] = 'xterm-256color'

def main():
    # Set ESCDELAY early, before any curses initialization
    # 25ms gives very snappy Esc response while still allowing most Alt+key and escape sequences to work reliably
    os.environ.setdefault('ESCDELAY', '25')

    # Get the actual directory of main.py, resolving any symlinks
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)
    courses_dir = os.path.join(script_dir, "courses")

    parser = CourseParser(courses_dir)
    courses = parser.parse_courses()
    if not courses:
        print("No valid courses found in the courses directory.")
        sys.exit(1)

    handle_bookmark_flags(courses)

    # Otherwise, proceed with menus.
    # Doc mode is now the default. -d/--doc flags are still accepted but redundant.
    doc_mode = True
    if ("-d" in sys.argv) or ("--doc" in sys.argv):
        doc_mode = True  # Explicitly requested (no change needed)

    menu = Menu(courses, doc_mode=doc_mode)
    try:
        curses.wrapper(menu.run)
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()

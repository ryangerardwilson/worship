# ~/Apps/rtutor/modules/flag_handler.py
import sys
import curses
from .bookmarks import Bookmarks
from .lesson_sequencer import LessonSequencer


def handle_bookmark_flags(courses):
    flags = ["-b", "--bookmark"]
    idx = -1
    for f in flags:
        if f in sys.argv:
            idx = sys.argv.index(f)
            break
    if idx == -1:
        return

    args = []
    for a in sys.argv[idx + 1 :]:
        if a.strip():
            args.append(a)

    bookmarks = Bookmarks()
    items = bookmarks._parse_bookmarks()
    if not items:
        print("No bookmarks.")
        sys.exit(0)

    if len(args) == 1 and args[0] == "-l":
        for i, (display, *_) in enumerate(items, 1):
            print(f"{i}: {display}")
        sys.exit(0)
    elif len(args) == 1 and args[0].isdigit():
        num = int(args[0]) - 1
        if 0 <= num < len(items):
            display, course_name, part_name, section_name, lesson_name = items[num]
            course = next((c for c in courses if c.name == course_name), None)
            if not course:
                print("Course not found.")
                sys.exit(1)

            if section_name:
                part = next((p for p in course.parts if p.name == part_name), None)
                if not part:
                    print("Part not found.")
                    sys.exit(1)
                section = next(
                    (s for s in part.sections if s.name == section_name), None
                )
                if not section:
                    print("Section not found.")
                    sys.exit(1)
                lessons = section.lessons
                seq_name = f"{course_name}: {part_name}: {section_name}"
            elif part_name:
                part = next((p for p in course.parts if p.name == part_name), None)
                if not part:
                    print("Part not found.")
                    sys.exit(1)
                lessons = []
                for s in part.sections:
                    lessons.extend(s.lessons)
                seq_name = f"{course_name}: {part_name}"
            else:
                lessons = []
                for p in course.parts:
                    for s in p.sections:
                        lessons.extend(s.lessons)
                seq_name = course_name

            target_idx = next(
                (i for i, l in enumerate(lessons) if l.name == lesson_name), None
            )
            if target_idx is None:
                print("Lesson not found.")
                sys.exit(1)

            def _run_bookmark(stdscr):
                sequencer = LessonSequencer(
                    seq_name, lessons, doc_mode=True, source_file=course.source_file
                )
                sequencer.target_lesson_name = lesson_name
                sequencer.run(stdscr)

            try:
                curses.wrapper(_run_bookmark)
            except KeyboardInterrupt:
                sys.exit(0)
            sys.exit(0)
        else:
            print("Invalid bookmark number.")
            sys.exit(1)
    elif len(args) == 2 and args[0] == "-d" and args[1].isdigit():
        num = int(args[1]) - 1
        if 0 <= num < len(items):
            display, *_ = items[num]
            bookmarks.remove(display)
            print("Bookmark deleted.")
            sys.exit(0)
        else:
            print("Invalid bookmark number.")
            sys.exit(1)
    else:
        print("Usage: -b -l to list, -b <num> to open, -b -d <num> to delete")
        sys.exit(1)

# ~/Apps/rtutor/modules/menu.py
import curses
from .ascii import title_ascii_art
from .key_utils import is_quit_request


class Menu:
    def __init__(self, courses, doc_mode=False):
        self.courses = sorted(courses, key=lambda c: c.name.lower())
        self.title_ascii_art = title_ascii_art
        self.doc_mode = doc_mode

    def run(self, stdscr):
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_WHITE, -1)
        stdscr.bkgd(" ", curses.color_pair(2))
        stdscr.nodelay(True)

        selected = 0
        need_redraw = True

        while True:
            max_y, max_x = stdscr.getmaxyx()
            total_items = len(self.courses)
            if total_items == 0:
                return

            title_lines = self.title_ascii_art.count("\n")
            menu_start_y = title_lines + 4

            art_lines = self.title_ascii_art.split("\n")
            content_width = max((len(line) for line in art_lines), default=0)
            menu_width = max((len(f"> {c.name}") for c in self.courses), default=0)

            if need_redraw:
                stdscr.clear()

                # ASCII title
                for i, line in enumerate(art_lines):
                    if line:
                        x_pos = max((max_x - content_width) // 2, 0)
                        try:
                            stdscr.addstr(i, x_pos, line[:max_x], curses.color_pair(2))
                        except curses.error:
                            pass

                # Author
                author_text = "By Ryan Gerard Wilson"
                try:
                    stdscr.addstr(
                        title_lines + 1,
                        (max_x - len(author_text)) // 2,
                        author_text,
                        curses.color_pair(2),
                    )
                except curses.error:
                    pass

                # Courses
                menu_x_pos = (max_x - menu_width) // 2 if menu_width < max_x else 0
                for i, course in enumerate(self.courses):
                    prefix = "> " if i == selected else "  "
                    text = f"{prefix}{course.name}"
                    try:
                        stdscr.addstr(
                            menu_start_y + i,
                            menu_x_pos,
                            text,
                            curses.color_pair(1)
                            if i == selected
                            else curses.color_pair(2),
                        )
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                stdscr.refresh()
                need_redraw = False

            changed = False
            while True:
                key = stdscr.getch()
                if key == -1:
                    break
                changed = True

                if key in (curses.KEY_UP, ord("k")):
                    selected = (selected - 1) % total_items
                elif key in (curses.KEY_DOWN, ord("j")):
                    selected = (selected + 1) % total_items
                elif key in (curses.KEY_LEFT, ord("h")):
                    curses.flash()
                elif is_quit_request(key):
                    stdscr.nodelay(False)
                    if key in (ord("q"), ord("Q")):
                        raise SystemExit
                    return
                elif key in (curses.KEY_RIGHT, ord("l")):
                    course = self.courses[selected]

                    if len(course.parts) == 1 and course.parts[0].name == "Main":
                        part = course.parts[0]
                        if len(part.sections) == 1 and part.sections[0].name == "Main":
                            from modules.lesson_sequencer import LessonSequencer

                            sequencer = LessonSequencer(
                                course.name,
                                part.sections[0].lessons,
                                doc_mode=self.doc_mode,
                                source_file=course.source_file,
                            )
                            sequencer.run(stdscr)
                        else:
                            self.run_section_menu(stdscr, course, part)
                    else:
                        self.run_part_menu(stdscr, course)

                    stdscr.nodelay(True)
                    curses.curs_set(0)
                    need_redraw = True

                elif key == ord("b") and self.doc_mode:
                    from .bookmarks import Bookmarks

                    bookmarks = Bookmarks()
                    result = bookmarks.show_menu_and_jump(stdscr, self.courses)
                    if result:
                        (
                            target_course_name,
                            target_part,
                            target_section,
                            target_lesson,
                        ) = result

                        found = False
                        for course in self.courses:
                            if course.name != target_course_name:
                                continue

                            # Case 1: Full hierarchy known — launch directly at section level
                            if target_part and target_section:
                                for part in course.parts:
                                    if part.name != target_part:
                                        continue
                                    for section in part.sections:
                                        if section.name != target_section:
                                            continue
                                        from .lesson_sequencer import LessonSequencer

                                        sequencer = LessonSequencer(
                                            f"{course.name}: {part.name}: {section.name}",
                                            section.lessons,
                                            doc_mode=True,
                                            source_file=course.source_file,
                                        )
                                        sequencer.target_lesson_name = target_lesson
                                        sequencer.run(stdscr)
                                        found = True
                                        break
                                    if found:
                                        break
                                if found:
                                    break

                            # Case 2: Only part known — open part menu
                            elif target_part:
                                for part in course.parts:
                                    if part.name != target_part:
                                        continue
                                    if (
                                        len(part.sections) == 1
                                        and part.sections[0].name == "Main"
                                    ):
                                        from .lesson_sequencer import LessonSequencer

                                        sequencer = LessonSequencer(
                                            f"{course.name}: {part.name}",
                                            part.sections[0].lessons,
                                            doc_mode=True,
                                            source_file=course.source_file,
                                        )
                                        sequencer.target_lesson_name = target_lesson
                                        sequencer.run(stdscr)
                                    else:
                                        self.run_section_menu(stdscr, course, part)
                                    found = True
                                    break
                                if found:
                                    break

                            # Case 3: Only course — open course normally
                            else:
                                if (
                                    len(course.parts) == 1
                                    and course.parts[0].name == "Main"
                                ):
                                    part = course.parts[0]
                                    if (
                                        len(part.sections) == 1
                                        and part.sections[0].name == "Main"
                                    ):
                                        from .lesson_sequencer import LessonSequencer

                                        sequencer = LessonSequencer(
                                            course.name,
                                            part.sections[0].lessons,
                                            doc_mode=True,
                                            source_file=course.source_file,
                                        )
                                        sequencer.target_lesson_name = target_lesson
                                        sequencer.run(stdscr)
                                    else:
                                        self.run_section_menu(stdscr, course, part)
                                else:
                                    self.run_part_menu(stdscr, course)
                                found = True
                                break

                        # After doc mode ends, return to main menu
                        need_redraw = True

                    else:
                        need_redraw = True

                elif is_quit_request(key):
                    stdscr.nodelay(False)
                    return

            if changed:
                need_redraw = True

    def run_part_menu(self, stdscr, course):
        curses.curs_set(0)
        stdscr.nodelay(True)

        selected = 0
        need_redraw = True

        while True:
            max_y, max_x = stdscr.getmaxyx()
            total_items = len(course.parts)
            menu_start_y = 2
            menu_width = max((len(f"> {p.name}") for p in course.parts), default=0)

            if need_redraw:
                stdscr.clear()

                title = f"> {course.name}"
                try:
                    stdscr.addstr(0, 0, title, curses.color_pair(2))
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                try:
                    stdscr.move(1, 0)
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                menu_x_pos = (max_x - menu_width) // 2 if menu_width < max_x else 0
                for i, part in enumerate(course.parts):
                    prefix = "> " if i == selected else "  "
                    text = f"{prefix}{part.name}"
                    try:
                        stdscr.addstr(
                            menu_start_y + i,
                            menu_x_pos,
                            text,
                            curses.color_pair(1)
                            if i == selected
                            else curses.color_pair(2),
                        )
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                stdscr.refresh()
                need_redraw = False

            changed = False
            while True:
                key = stdscr.getch()
                if key == -1:
                    break
                changed = True

                if key in (curses.KEY_UP, ord("k")):
                    selected = (selected - 1) % total_items
                elif key in (curses.KEY_DOWN, ord("j")):
                    selected = (selected + 1) % total_items
                elif key in (curses.KEY_LEFT, ord("h")):
                    return
                elif is_quit_request(key):
                    stdscr.nodelay(False)
                    if key in (ord("q"), ord("Q")):
                        raise SystemExit
                    return
                elif key in (curses.KEY_RIGHT, ord("l")):
                    part = course.parts[selected]

                    if len(part.sections) == 1 and part.sections[0].name == "Main":
                        from modules.lesson_sequencer import LessonSequencer

                        sequencer = LessonSequencer(
                            f"{course.name}: {part.name}",
                            part.sections[0].lessons,
                            doc_mode=self.doc_mode,
                            source_file=course.source_file,
                        )
                        sequencer.run(stdscr)
                    else:
                        self.run_section_menu(stdscr, course, part)

                    stdscr.nodelay(True)
                    curses.curs_set(0)
                    need_redraw = True

            if changed:
                need_redraw = True

    def run_section_menu(self, stdscr, course, part):
        curses.curs_set(0)
        stdscr.nodelay(True)

        selected = 0
        need_redraw = True

        while True:
            max_y, max_x = stdscr.getmaxyx()
            total_items = len(part.sections)
            menu_start_y = 2
            menu_width = max((len(f"> {s.name}") for s in part.sections), default=0)

            if need_redraw:
                stdscr.clear()

                title = f"> {course.name} > {part.name}"
                try:
                    stdscr.addstr(0, 0, title, curses.color_pair(2))
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                try:
                    stdscr.move(1, 0)
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                menu_x_pos = (max_x - menu_width) // 2 if menu_width < max_x else 0
                for i, section in enumerate(part.sections):
                    prefix = "> " if i == selected else "  "
                    text = f"{prefix}{section.name}"
                    try:
                        stdscr.addstr(
                            menu_start_y + i,
                            menu_x_pos,
                            text,
                            curses.color_pair(1)
                            if i == selected
                            else curses.color_pair(2),
                        )
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                stdscr.refresh()
                need_redraw = False

            changed = False
            while True:
                key = stdscr.getch()
                if key == -1:
                    break
                changed = True

                if key in (curses.KEY_UP, ord("k")):
                    selected = (selected - 1) % total_items
                elif key in (curses.KEY_DOWN, ord("j")):
                    selected = (selected + 1) % total_items
                elif key in (curses.KEY_LEFT, ord("h")):
                    return
                elif is_quit_request(key):
                    stdscr.nodelay(False)
                    if key in (ord("q"), ord("Q")):
                        raise SystemExit
                    return
                elif key in (curses.KEY_RIGHT, ord("l")):
                    section = part.sections[selected]
                    from modules.lesson_sequencer import LessonSequencer

                    sequencer = LessonSequencer(
                        f"{course.name}: {part.name}: {section.name}",
                        section.lessons,
                        doc_mode=self.doc_mode,
                        source_file=course.source_file,
                    )
                    sequencer.run(stdscr)
                    stdscr.nodelay(True)
                    curses.curs_set(0)
                    need_redraw = True

            if changed:
                need_redraw = True

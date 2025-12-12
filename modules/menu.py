# ~/Apps/rtutor/modules/menu.py
import curses
from .ascii import title_ascii_art


class Menu:
    def __init__(self, courses, doc_mode=False):
        self.courses = courses
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
            if not self.courses:
                return

            max_y, max_x = stdscr.getmaxyx()
            title_lines = self.title_ascii_art.count("\n")
            menu_start_y = title_lines + 4

            art_lines = self.title_ascii_art.split("\n")
            content_width = max((len(l) for l in art_lines if l), default=0)
            menu_width = max((len(f"> {c.name}") for c in self.courses), default=0)

            if need_redraw:
                stdscr.clear()

                # Title art
                for i, line in enumerate(art_lines):
                    if line:
                        x = max((max_x - content_width) // 2, 0)
                        stdscr.addstr(i, x, line[:max_x], curses.color_pair(2))

                # Author
                author = "By Ryan Gerard Wilson"
                stdscr.addstr(title_lines + 1, (max_x - len(author)) // 2, author, curses.color_pair(2))

                # Menu items
                mx = (max_x - menu_width) // 2 if menu_width < max_x else 0
                for i, course in enumerate(self.courses):
                    prefix = "> " if i == selected else "  "
                    stdscr.addstr(menu_start_y + i, mx, f"{prefix}{course.name}",
                                  curses.color_pair(1) if i == selected else curses.color_pair(2))
                    stdscr.clrtoeol()

                stdscr.refresh()
                need_redraw = False

            key = stdscr.getch()
            if key == -1:
                continue

            if key == curses.KEY_UP:
                selected = (selected - 1) % len(self.courses)
                need_redraw = True

            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(self.courses)
                need_redraw = True

            elif key in (curses.KEY_RIGHT, ord('\n'), ord('\r'), curses.KEY_ENTER):
                course = self.courses[selected]

                # Case 1: single part "Main" → single section "Main" → go straight to lessons
                if (len(course.parts) == 1 and course.parts[0].name == "Main" and
                    len(course.parts[0].sections) == 1 and course.parts[0].sections[0].name == "Main"):
                    from modules.lesson_sequencer import LessonSequencer
                    sequencer = LessonSequencer(course.name, course.parts[0].sections[0].lessons,
                                               doc_mode=self.doc_mode)
                    sequencer.run(stdscr)

                # Case 2: single part "Main" → show its sections
                elif len(course.parts) == 1 and course.parts[0].name == "Main":
                    self.run_section_menu(stdscr, course, course.parts[0])

                # Case 3: multiple parts → show part menu
                else:
                    self.run_part_menu(stdscr, course)

                need_redraw = True

            elif key in (curses.KEY_LEFT, 27):  # Left or Esc → exit
                return

    # -------------------------------------------------------------------------
    def run_part_menu(self, stdscr, course):
        curses.curs_set(0)
        stdscr.nodelay(True)
        selected = 0
        need_redraw = True

        while True:
            parts = course.parts
            max_y, max_x = stdscr.getmaxyx()
            menu_width = max((len(f"> {p.name}") for p in parts), default=0)

            if need_redraw:
                stdscr.clear()
                stdscr.addstr(0, 0, f"> {course.name}", curses.color_pair(2))
                stdscr.clrtoeol()
                stdscr.move(1, 0)
                stdscr.clrtoeol()

                mx = (max_x - menu_width) // 2 if menu_width < max_x else 0
                for i, part in enumerate(parts):
                    prefix = "> " if i == selected else "  "
                    stdscr.addstr(2 + i, mx, f"{prefix}{part.name}",
                                  curses.color_pair(1) if i == selected else curses.color_pair(2))
                    stdscr.clrtoeol()
                stdscr.refresh()
                need_redraw = False

            key = stdscr.getch()
            if key == -1:
                continue

            if key == curses.KEY_UP:
                selected = (selected - 1) % len(parts)
                need_redraw = True
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(parts)
                need_redraw = True
            elif key in (curses.KEY_RIGHT, ord('\n'), ord('\r'), curses.KEY_ENTER):
                part = parts[selected]
                if len(part.sections) == 1 and part.sections[0].name == "Main":
                    from modules.lesson_sequencer import LessonSequencer
                    sequencer = LessonSequencer(f"{course.name}: {part.name}",
                                               part.sections[0].lessons, doc_mode=self.doc_mode)
                    sequencer.run(stdscr)
                else:
                    self.run_section_menu(stdscr, course, part)
                need_redraw = True
            elif key in (curses.KEY_LEFT, 27):
                return

    # -------------------------------------------------------------------------
    def run_section_menu(self, stdscr, course, part):
        curses.curs_set(0)
        stdscr.nodelay(True)
        selected = 0
        need_redraw = True

        while True:
            sections = part.sections
            max_y, max_x = stdscr.getmaxyx()
            menu_width = max((len(f"> {s.name}") for s in sections), default=0)

            if need_redraw:
                stdscr.clear()
                stdscr.addstr(0, 0, f"> {course.name} > {part.name}", curses.color_pair(2))
                stdscr.clrtoeol()
                stdscr.move(1, 0)
                stdscr.clrtoeol()

                mx = (max_x - menu_width) // 2 if menu_width < max_x else 0
                for i, section in enumerate(sections):
                    prefix = "> " if i == selected else "  "
                    stdscr.addstr(2 + i, mx, f"{prefix}{section.name}",
                                  curses.color_pair(1) if i == selected else curses.color_pair(2))
                    stdscr.clrtoeol()
                stdscr.refresh()
                need_redraw = False

            key = stdscr.getch()
            if key == -1:
                continue

            if key == curses.KEY_UP:
                selected = (selected - 1) % len(sections)
                need_redraw = True
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(sections)
                need_redraw = True
            elif key in (curses.KEY_RIGHT, ord('\n'), ord('\r'), curses.KEY_ENTER):
                from modules.lesson_sequencer import LessonSequencer
                sequencer = LessonSequencer(f"{course.name}: {part.name}: {sections[selected].name}",
                                           sections[selected].lessons, doc_mode=self.doc_mode)
                sequencer.run(stdscr)
                need_redraw = True
            elif key in (curses.KEY_LEFT, 27):
                return

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

                for i, line in enumerate(art_lines):
                    if line:
                        x_pos = max((max_x - content_width) // 2, 0)
                        try:
                            stdscr.addstr(i, x_pos, line[:max_x], curses.color_pair(2))
                        except curses.error:
                            pass

                author_text = "By Ryan Gerard Wilson"
                try:
                    stdscr.addstr(title_lines + 1, (max_x - len(author_text)) // 2, author_text, curses.color_pair(2))
                except curses.error:
                    pass

                menu_x_pos = (max_x - menu_width) // 2 if menu_width < max_x else 0
                for i, course in enumerate(self.courses):
                    prefix = "> " if i == selected else "  "
                    text = f"{prefix}{course.name}"
                    try:
                        stdscr.addstr(
                            menu_start_y + i,
                            menu_x_pos,
                            text,
                            curses.color_pair(1) if i == selected else curses.color_pair(2),
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

                kn = curses.keyname(key).lower()

                # EMACS OR DEATH
                if kn == b"^p" or key == curses.KEY_UP:          # Previous line
                    selected = (selected - 1) % total_items
                elif kn == b"^n" or key == curses.KEY_DOWN:      # Next line
                    selected = (selected + 1) % total_items
                elif kn == b"^a":                                # Beginning of list
                    selected = 0
                elif kn == b"^e":                                # End of list
                    selected = total_items - 1
                elif kn in (b"^f", b"^l"):                       # Forward → enter menu
                    course = self.courses[selected]
                    if len(course.parts) == 1 and course.parts[0].name == "Main":
                        part = course.parts[0]
                        if len(part.sections) == 1 and part.sections[0].name == "Main":
                            from modules.lesson_sequencer import LessonSequencer
                            sequencer = LessonSequencer(course.name, part.sections[0].lessons, doc_mode=self.doc_mode)
                            sequencer.run(stdscr)
                        else:
                            self.run_section_menu(stdscr, course, part)
                    else:
                        self.run_part_menu(stdscr, course)
                    stdscr.nodelay(True)
                    curses.curs_set(0)
                    need_redraw = True

                elif kn in (b"^b", b"^h") or key == 27:           # Back or ESC
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
            total_items = len(course.parts)
            menu_start_y = 2
            menu_width = max((len(f"> {p.name}") for p in course.parts), default=0)
            max_y, max_x = stdscr.getmaxyx()

            if need_redraw:
                stdscr.clear()
                stdscr.addstr(0, 0, f"> {course.name}", curses.color_pair(2))
                stdscr.clrtoeol()
                stdscr.move(1, 0)
                stdscr.clrtoeol()

                menu_x_pos = (max_x - menu_width) // 2 if menu_width < max_x else 0
                for i, part in enumerate(course.parts):
                    prefix = "> " if i == selected else "  "
                    stdscr.addstr(menu_start_y + i, menu_x_pos, f"{prefix}{part.name}",
                                  curses.color_pair(1) if i == selected else curses.color_pair(2))
                    stdscr.clrtoeol()
                stdscr.refresh()
                need_redraw = False

            changed = False
            while True:
                key = stdscr.getch()
                if key == -1:
                    break
                changed = True

                kn = curses.keyname(key).lower()

                if kn == b"^p" or key == curses.KEY_UP:
                    selected = (selected - 1) % total_items
                elif kn == b"^n" or key == curses.KEY_DOWN:
                    selected = (selected + 1) % total_items
                elif kn == b"^a":
                    selected = 0
                elif kn == b"^e":
                    selected = total_items - 1
                elif kn in (b"^f", b"^l"):  # Forward → enter
                    part = course.parts[selected]
                    if len(part.sections) == 1 and part.sections[0].name == "Main":
                        from modules.lesson_sequencer import LessonSequencer
                        sequencer = LessonSequencer(f"{course.name}: {part.name}", part.sections[0].lessons, doc_mode=self.doc_mode)
                        sequencer.run(stdscr)
                    else:
                        self.run_section_menu(stdscr, course, part)
                    stdscr.nodelay(True)
                    curses.curs_set(0)
                    need_redraw = True
                elif kn in (b"^b", b"^h") or key == 27:
                    return

            if changed:
                need_redraw = True

    def run_section_menu(self, stdscr, course, part):
        curses.curs_set(0)
        stdscr.nodelay(True)
        selected = 0
        need_redraw = True

        while True:
            total_items = len(part.sections)
            menu_start_y = 2
            menu_width = max((len(f"> {s.name}") for s in part.sections), default=0)
            max_y, max_x = stdscr.getmaxyx()

            if need_redraw:
                stdscr.clear()
                stdscr.addstr(0, 0, f"> {course.name} > {part.name}", curses.color_pair(2))
                stdscr.clrtoeol()
                stdscr.move(1, 0)
                stdscr.clrtoeol()

                menu_x_pos = (max_x - menu_width) // 2 if menu_width < max_x else 0
                for i, section in enumerate(part.sections):
                    prefix = "> " if i == selected else "  "
                    stdscr.addstr(menu_start_y + i, menu_x_pos, f"{prefix}{section.name}",
                                  curses.color_pair(1) if i == selected else curses.color_pair(2))
                    stdscr.clrtoeol()
                stdscr.refresh()
                need_redraw = False

            changed = False
            while True:
                key = stdscr.getch()
                if key == -1:
                    break
                changed = True

                kn = curses.keyname(key).lower()

                if kn == b"^p" or key == curses.KEY_UP:
                    selected = (selected - 1) % total_items
                elif kn == b"^n" or key == curses.KEY_DOWN:
                    selected = (selected + 1) % total_items
                elif kn == b"^a":
                    selected = 0
                elif kn == b"^e":
                    selected = total_items - 1
                elif kn in (b"^f", b"^l"):  # Forward → start lesson
                    section = part.sections[selected]
                    from modules.lesson_sequencer import LessonSequencer
                    sequencer = LessonSequencer(f"{course.name}: {part.name}: {section.name}", section.lessons, doc_mode=self.doc_mode)
                    sequencer.run(stdscr)
                    stdscr.nodelay(True)
                    curses.curs_set(0)
                    need_redraw = True
                elif kn in (b"^b", b"^h") or key == 27:
                    return

            if changed:
                need_redraw = True

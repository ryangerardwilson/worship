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
        stdscr.bkgd(
            " ", curses.color_pair(2)
        )  # Background to default with white fg (for spaces)
        stdscr.nodelay(True)  # Non-blocking for batching keys

        max_y, max_x = stdscr.getmaxyx()
        title_lines = self.title_ascii_art.count("\n")
        menu_start_y = title_lines + 4  # Gap: 1 for author, 2 blank lines, 1 extra

        # Calculate content width for centering title art (use max raw line len)
        art_lines = self.title_ascii_art.split("\n")
        content_width = max(len(line) for line in art_lines)

        # Calculate menu width for centering the block
        menu_width = max(
            max(len(f"> {course.name}") for course in self.courses), len("> Quit")
        )

        selected = 0
        need_redraw = True  # Initial draw

        while True:
            if need_redraw:
                stdscr.clear()  # Clear once at start; overwrites after
                # Render title ASCII art as is
                for i, line in enumerate(art_lines):
                    if line:  # Render raw line, including all spaces
                        x_pos = (max_x - content_width) // 2
                        if x_pos < 0:
                            line = line[:max_x]
                            x_pos = 0
                        try:
                            stdscr.addstr(i, x_pos, line, curses.color_pair(2))
                        except curses.error:
                            pass

                # Render author text
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

                # Clear lines between author and menu
                for row in range(title_lines + 2, menu_start_y):
                    try:
                        stdscr.move(row, 0)
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                # Render menu items, left-aligned but centered as a block
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
                        stdscr.move(menu_start_y + i, menu_x_pos + len(text))
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                # Render Quit option
                quit_text = "> Quit" if selected == len(self.courses) else "  Quit"
                try:
                    stdscr.addstr(
                        menu_start_y + len(self.courses),
                        menu_x_pos,
                        quit_text,
                        curses.color_pair(1)
                        if selected == len(self.courses)
                        else curses.color_pair(2),
                    )
                    stdscr.move(
                        menu_start_y + len(self.courses), menu_x_pos + len(quit_text)
                    )
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                # Clear any extra lines below menu
                for row in range(menu_start_y + len(self.courses) + 1, max_y):
                    try:
                        stdscr.move(row, 0)
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                stdscr.refresh()
                need_redraw = False

            # Batch process all queued keys
            changed = False
            while True:
                key = stdscr.getch()
                if key == -1:
                    break
                changed = True
                if key in (curses.KEY_UP, ord("k")):
                    selected = max(0, selected - 1)
                elif key in (curses.KEY_DOWN, ord("j")):
                    selected = min(len(self.courses), selected + 1)
                elif key in (curses.KEY_LEFT, ord("h")):
                    selected = 0
                elif key in (curses.KEY_RIGHT, ord("l")):
                    selected = len(self.courses)
                elif key in (curses.KEY_ENTER, 10, 13):
                    if selected == len(self.courses):
                        stdscr.nodelay(False)
                        return
                    course = self.courses[selected]
                    # Check if flat to "Main" part
                    if len(course.parts) == 1 and course.parts[0].name == "Main":
                        part = course.parts[0]
                        if len(part.sections) == 1 and part.sections[0].name == "Main":
                            from modules.lesson_sequencer import LessonSequencer

                            sequencer = LessonSequencer(
                                course.name, part.sections[0].lessons, doc_mode=self.doc_mode
                            )
                            sequencer.run(stdscr)
                            stdscr.nodelay(True)  # Reset after lesson
                            curses.curs_set(0)  # Reset cursor after lesson
                        else:
                            self.run_section_menu(stdscr, course, part)
                            stdscr.nodelay(True)  # Reset after sub-menu
                            curses.curs_set(0)  # Reset cursor
                    else:
                        self.run_part_menu(stdscr, course)
                        stdscr.nodelay(True)  # Reset after sub-menu
                        curses.curs_set(0)  # Reset cursor
                    need_redraw = True  # Force redraw after sub-menu/lesson
                elif key == 27:  # ESC
                    stdscr.nodelay(False)
                    return

            if changed:
                need_redraw = True

    def run_part_menu(self, stdscr, course):
        curses.curs_set(0)
        stdscr.nodelay(True)  # Non-blocking for batching keys

        max_y, max_x = stdscr.getmaxyx()
        menu_start_y = 2  # Simple, no big title here

        # Calculate menu width
        menu_width = max(
            max(len(f"> {part.name}") for part in course.parts), len("> Back")
        )

        selected = 0
        need_redraw = True  # Initial draw

        while True:
            if need_redraw:
                stdscr.clear()  # Clear once at start; overwrites after
                # Course title
                title = f"> {course.name}"
                try:
                    stdscr.addstr(0, 0, title, curses.color_pair(2))
                    stdscr.move(0, len(title))
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                # Clear line 1 if needed
                try:
                    stdscr.move(1, 0)
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                # Render parts
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
                        stdscr.move(menu_start_y + i, menu_x_pos + len(text))
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                # Back option
                back_text = "> Back" if selected == len(course.parts) else "  Back"
                try:
                    stdscr.addstr(
                        menu_start_y + len(course.parts),
                        menu_x_pos,
                        back_text,
                        curses.color_pair(1)
                        if selected == len(course.parts)
                        else curses.color_pair(2),
                    )
                    stdscr.move(
                        menu_start_y + len(course.parts), menu_x_pos + len(back_text)
                    )
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                # Clear extra lines below menu
                for row in range(menu_start_y + len(course.parts) + 1, max_y):
                    try:
                        stdscr.move(row, 0)
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                stdscr.refresh()
                need_redraw = False

            # Batch process all queued keys
            changed = False
            while True:
                key = stdscr.getch()
                if key == -1:
                    break
                changed = True
                if key in (curses.KEY_UP, ord("k")):
                    selected = max(0, selected - 1)
                elif key in (curses.KEY_DOWN, ord("j")):
                    selected = min(len(course.parts), selected + 1)
                elif key in (curses.KEY_LEFT, ord("h")):
                    selected = 0
                elif key in (curses.KEY_RIGHT, ord("l")):
                    selected = len(course.parts)
                elif key in (curses.KEY_ENTER, 10, 13):
                    if selected == len(course.parts):
                        return  # Just return, no nodelay(False)
                    part = course.parts[selected]
                    if len(part.sections) == 1 and part.sections[0].name == "Main":
                        from modules.lesson_sequencer import LessonSequencer

                        sequencer = LessonSequencer(
                            f"{course.name}: {part.name}", part.sections[0].lessons, doc_mode=self.doc_mode
                        )
                        sequencer.run(stdscr)
                        stdscr.nodelay(True)  # Reset after lesson
                        curses.curs_set(0)  # Reset cursor after lesson
                    else:
                        self.run_section_menu(stdscr, course, part)
                        stdscr.nodelay(True)  # Reset after sub-menu
                        curses.curs_set(0)  # Reset cursor
                    need_redraw = True  # Force redraw after lesson
                elif key == 27:  # ESC
                    return  # Just return, no nodelay(False)

            if changed:
                need_redraw = True

    def run_section_menu(self, stdscr, course, part):
        curses.curs_set(0)
        stdscr.nodelay(True)  # Non-blocking for batching keys

        max_y, max_x = stdscr.getmaxyx()
        menu_start_y = 2  # Simple, no big title here

        # Calculate menu width
        menu_width = max(
            max(len(f"> {section.name}") for section in part.sections), len("> Back")
        )

        selected = 0
        need_redraw = True  # Initial draw

        while True:
            if need_redraw:
                stdscr.clear()  # Clear once at start; overwrites after
                # Course and part title
                title = f"> {course.name} > {part.name}"
                try:
                    stdscr.addstr(0, 0, title, curses.color_pair(2))
                    stdscr.move(0, len(title))
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                # Clear line 1 if needed
                try:
                    stdscr.move(1, 0)
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                # Render sections
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
                        stdscr.move(menu_start_y + i, menu_x_pos + len(text))
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                # Back option
                back_text = "> Back" if selected == len(part.sections) else "  Back"
                try:
                    stdscr.addstr(
                        menu_start_y + len(part.sections),
                        menu_x_pos,
                        back_text,
                        curses.color_pair(1)
                        if selected == len(part.sections)
                        else curses.color_pair(2),
                    )
                    stdscr.move(
                        menu_start_y + len(part.sections), menu_x_pos + len(back_text)
                    )
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                # Clear extra lines below menu
                for row in range(menu_start_y + len(part.sections) + 1, max_y):
                    try:
                        stdscr.move(row, 0)
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                stdscr.refresh()
                need_redraw = False

            # Batch process all queued keys
            changed = False
            while True:
                key = stdscr.getch()
                if key == -1:
                    break
                changed = True
                if key in (curses.KEY_UP, ord("k")):
                    selected = max(0, selected - 1)
                elif key in (curses.KEY_DOWN, ord("j")):
                    selected = min(len(part.sections), selected + 1)
                elif key in (curses.KEY_LEFT, ord("h")):
                    selected = 0
                elif key in (curses.KEY_RIGHT, ord("l")):
                    selected = len(part.sections)
                elif key in (curses.KEY_ENTER, 10, 13):
                    if selected == len(part.sections):
                        return  # Just return, no nodelay(False)
                    section = part.sections[selected]
                    from modules.lesson_sequencer import LessonSequencer

                    sequencer = LessonSequencer(
                        f"{course.name}: {part.name}: {section.name}", section.lessons, doc_mode=self.doc_mode
                    )
                    sequencer.run(stdscr)
                    stdscr.nodelay(True)  # Reset after lesson
                    curses.curs_set(0)  # Reset cursor after lesson
                    need_redraw = True  # Force redraw after lesson
                elif key == 27:  # ESC
                    return  # Just return, no nodelay(False)

            if changed:
                need_redraw = True

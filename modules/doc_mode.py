# ~/Apps/rtutor/modules/doc_mode.py
import curses
import sys
from .structs import Lesson
from .rote_mode import RoteMode
from .jump_mode import JumpMode
from .doc_editor import DocEditor
from .bookmarks import Bookmarks


class DocMode:
    def __init__(self, sequencer):
        self.sequencer = sequencer
        self.idx = 0
        self.offset = 0
        self.bookmarks = Bookmarks()

        if hasattr(sequencer, 'target_lesson_name'):
            for i, lesson in enumerate(sequencer.lessons):
                if lesson.name == sequencer.target_lesson_name:
                    self.idx = i
                    break

    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)
        source_file = getattr(self.sequencer, "source_file", None)
        need_redraw = True

        while True:
            current_lesson = self.sequencer.lessons[self.idx]
            # lines = current_lesson.content.rstrip().splitlines()
            lines = current_lesson.content.splitlines()  
            total_lines = len(lines)

            max_y, max_x = stdscr.getmaxyx()
            header_rows = 2
            footer_rows = 2
            available_height = max(0, max_y - header_rows - footer_rows)

            # Clamp offset
            if total_lines <= available_height:
                self.offset = 0
            else:
                self.offset = max(0, min(self.offset, total_lines - available_height))

            if need_redraw:
                stdscr.clear()

                # Title
                title = f"{self.sequencer.name} | {current_lesson.name}"
                try:
                    stdscr.addstr(0, 0, title[:max_x], curses.color_pair(1) | curses.A_BOLD)
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                # Empty line
                try:
                    stdscr.move(1, 0)
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                # Render visible lines
                start_line = self.offset
                end_line = min(start_line + available_height, total_lines)
                visible_lines = lines[start_line:end_line]

                for i, line in enumerate(visible_lines):
                    row = header_rows + i
                    disp = line.replace("\t", "    ")
                    try:
                        stdscr.addstr(row, 0, disp[:max_x], curses.color_pair(1))
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                # Simple clear below content
                for row in range(header_rows + len(visible_lines), max_y - footer_rows):
                    try:
                        stdscr.move(row, 0)
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                # Footer
                counter = f"Lesson {self.idx + 1}/{len(self.sequencer.lessons)}"
                scroll_info = ""
                if total_lines > available_height:
                    top = self.offset + 1
                    bottom = self.offset + len(visible_lines)
                    scroll_info = f"  [{top}-{bottom}/{total_lines}]"

                try:
                    stdscr.addstr(max_y - 2, 0, counter + scroll_info, curses.color_pair(1))
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                instr = "l=next h=prev r=rote t=teleport i=edit b=mark k↑ j↓=scroll esc=back"
                try:
                    stdscr.addstr(max_y - 1, 0, instr, curses.color_pair(1))
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                stdscr.refresh()
                need_redraw = False

            key = stdscr.getch()
            if key == -1:
                continue

            redraw_needed = False

            if key == 3:
                sys.exit(0)
            elif key == 27:
                return False
            elif key in (ord("l"), ord("L"), curses.KEY_RIGHT):
                if self.idx < len(self.sequencer.lessons) - 1:
                    self.idx += 1
                    self.offset = 0
                    redraw_needed = True
            elif key in (ord("h"), ord("H"), curses.KEY_LEFT):
                if self.idx > 0:
                    self.idx -= 1
                    self.offset = 0
                    redraw_needed = True
            elif key in (ord("j"), curses.KEY_DOWN):
                if self.offset < max(0, total_lines - available_height):
                    self.offset += 1
                    redraw_needed = True
            elif key in (ord("k"), curses.KEY_UP):
                if self.offset > 0:
                    self.offset -= 1
                    redraw_needed = True
            elif key == ord("b"):
                import os
                script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                courses_dir = os.path.join(script_dir, "courses")
                from modules.course_parser import CourseParser
                parser = CourseParser(courses_dir)
                all_courses = parser.parse_courses()
                self.bookmarks.add(all_courses, self.sequencer.name, current_lesson.name)
                try:
                    stdscr.addstr(max_y - 1, 0, "Bookmarked!           ", curses.A_BOLD)
                    stdscr.refresh()
                    curses.napms(800)
                except:
                    pass
                redraw_needed = True
            elif key in (ord("r"), ord("R")):
                rote = RoteMode(self.sequencer.name, current_lesson)
                rote.run(stdscr)
                redraw_needed = True
            elif key in (ord("t"), ord("T")):
                jump = JumpMode(self.sequencer.name, self.sequencer.lessons, self.idx)
                final_idx = jump.run(stdscr)
                if final_idx is not None:
                    if final_idx >= len(self.sequencer.lessons):
                        return True
                    self.idx = final_idx
                    self.offset = 0
                redraw_needed = True
            elif key in (ord("i"), ord("I")):
                editor = DocEditor(source_file)
                result = editor.edit_lesson(stdscr, current_lesson.name, self.idx)
                if result:
                    reloaded_lessons, course_name, new_idx = result
                    self.sequencer.lessons = reloaded_lessons
                    self.sequencer.name = course_name
                    self.idx = new_idx
                    self.offset = 0
                redraw_needed = True

            if redraw_needed:
                need_redraw = True

        return False

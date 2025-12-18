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
        self.bookmarks = Bookmarks()  # Single instance for all operations

        # If launched from bookmark, auto-advance to matching lesson
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

            if need_redraw:
                stdscr.clear()
                title = f"{self.sequencer.name} | {current_lesson.name}"
                try:
                    stdscr.addstr(0, 0, title, curses.color_pair(1))
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                try:
                    stdscr.move(1, 0)
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                lines = current_lesson.content.strip().splitlines()
                max_y, max_x = stdscr.getmaxyx()
                row = 2
                for line in lines:
                    disp = line.replace("\t", "    ")
                    try:
                        stdscr.addstr(row, 0, disp[:max_x], curses.color_pair(1))
                        stdscr.clrtoeol()
                    except curses.error:
                        pass
                    row += 1
                    if row >= max_y - 2:
                        break

                for r in range(row, max_y - 2):
                    try:
                        stdscr.move(r, 0)
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                footer_left = f"Lesson {self.idx + 1}/{len(self.sequencer.lessons)}"
                instr = "Doc mode: l-next | h-prev | r-rote | j-jump | i-edit | b-bookmark | esc-back"
                try:
                    stdscr.addstr(max_y - 2, 0, footer_left, curses.color_pair(1))
                except:
                    pass
                try:
                    stdscr.addstr(max_y - 1, 0, instr, curses.color_pair(1))
                except:
                    pass

                stdscr.refresh()
                need_redraw = False

            key = stdscr.getch()
            if key == -1:
                continue

            if key == 3:  # Ctrl+C
                sys.exit(0)
            elif key == 27:  # ESC
                return False
            elif key in (ord("l"), ord("L")):
                if self.idx < len(self.sequencer.lessons) - 1:
                    self.idx += 1
                    need_redraw = True
            elif key in (ord("h"), ord("H")):
                if self.idx > 0:
                    self.idx -= 1
                    need_redraw = True
            elif key == ord("b"):
                import os
                # Add current lesson to bookmarks with full hierarchy
                # We need the parsed courses to resolve Part/Section
                script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                courses_dir = os.path.join(script_dir, "courses")
                from modules.course_parser import CourseParser
                parser = CourseParser(courses_dir)
                all_courses = parser.parse_courses()

                self.bookmarks.add(all_courses, self.sequencer.name, current_lesson.name)
                max_y, _ = stdscr.getmaxyx()
                try:
                    stdscr.addstr(max_y - 1, 0, "Bookmarked!", curses.A_BOLD)
                    stdscr.clrtoeol()
                    stdscr.refresh()
                    curses.napms(800)
                except:
                    pass
                need_redraw = True
            elif key in (ord("r"), ord("R")):
                rote = RoteMode(self.sequencer.name, current_lesson)
                rote.run(stdscr)
                need_redraw = True
            elif key in (ord("j"), ord("J")):
                jump = JumpMode(self.sequencer.name, self.sequencer.lessons, self.idx)
                final_idx = jump.run(stdscr)
                if final_idx is not None:
                    if final_idx >= len(self.sequencer.lessons):
                        return True
                    self.idx = final_idx
                need_redraw = True
            elif key in (ord("i"), ord("I")):
                editor = DocEditor(source_file)
                result = editor.edit_lesson(stdscr, current_lesson.name, self.idx)
                if result:
                    reloaded_lessons, course_name, new_idx = result
                    self.sequencer.lessons = reloaded_lessons
                    self.sequencer.name = course_name
                    self.idx = new_idx
                need_redraw = True

        return False

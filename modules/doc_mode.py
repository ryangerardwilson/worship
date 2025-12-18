import curses
import sys
import os
import re
from .structs import Lesson
from .rote_mode import RoteMode
from .jump_mode import JumpMode
from .doc_editor import DocEditor


class DocMode:
    def __init__(self, sequencer):
        self.sequencer = sequencer

    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)

        idx = 0
        need_redraw = True
        source_file = getattr(self.sequencer, "source_file", None)

        while True:
            if need_redraw:
                stdscr.clear()
                try:
                    title = f"{self.sequencer.name} | {self.sequencer.lessons[idx].name}"
                    stdscr.addstr(0, 0, title, curses.color_pair(1))
                    stdscr.move(0, len(title))
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                try:
                    stdscr.move(1, 0)
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                lines = self.sequencer.lessons[idx].content.strip().splitlines()
                max_y, max_x = stdscr.getmaxyx()
                row = 2
                for line in lines:
                    disp = line.replace("\t", "    ")
                    try:
                        stdscr.addstr(row, 0, disp[:max_x], curses.color_pair(1))
                        stdscr.move(row, min(len(disp), max_x))
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

                footer_left = f"Lesson {idx + 1}/{len(self.sequencer.lessons)}"
                instr = "Doc mode: l-next | h-prev | r-rote | j-jump | i-edit | esc-back"
                try:
                    stdscr.addstr(max_y - 2, 0, footer_left, curses.color_pair(1))
                except curses.error:
                    pass
                try:
                    stdscr.addstr(max_y - 1, 0, instr, curses.color_pair(1))
                except curses.error:
                    pass

                stdscr.refresh()
                need_redraw = False

            changed = False
            while True:
                try:
                    key = stdscr.getch()
                    if key == -1:
                        break
                    changed = True

                    if key == 3:  # Ctrl+C
                        sys.exit(0)
                    elif key == 27:  # ESC
                        return False
                    elif key in (ord("l"), ord("L")):
                        if idx < len(self.sequencer.lessons) - 1:
                            idx += 1
                    elif key in (ord("h"), ord("H")):
                        if idx > 0:
                            idx -= 1
                    elif key in (ord("r"), ord("R")):
                        rote = RoteMode(self.sequencer.name, self.sequencer.lessons[idx])
                        rote.run(stdscr)
                        stdscr.nodelay(True)
                        curses.curs_set(0)
                        need_redraw = True
                    elif key in (ord("j"), ord("J")):
                        jump = JumpMode(self.sequencer.name, self.sequencer.lessons, idx)
                        final_idx = jump.run(stdscr)
                        if final_idx is not None:
                            if final_idx >= len(self.sequencer.lessons):
                                return True
                            idx = final_idx
                        stdscr.nodelay(True)
                        curses.curs_set(0)
                        need_redraw = True
                    elif key in (ord("i"), ord("I")):
                        # delegate editing to DocEditor
                        source_file = getattr(self.sequencer, "source_file", None)
                        editor = DocEditor(source_file)
                        result = editor.edit_lesson(stdscr, self.sequencer.lessons[idx].name, idx)

                        # restore curses state after vim
                        stdscr.nodelay(True)
                        curses.curs_set(0)

                        if result:
                            reloaded_lessons, course_name, new_idx = result
                            self.sequencer.lessons = reloaded_lessons
                            self.sequencer.name = course_name
                            idx = new_idx

                        # ensure redraw whether or not edit succeeded
                        stdscr.touchwin()
                        stdscr.refresh()
                        need_redraw = True
                        break

                except KeyboardInterrupt:
                    sys.exit(0)
                except curses.error:
                    pass

            if changed:
                need_redraw = True

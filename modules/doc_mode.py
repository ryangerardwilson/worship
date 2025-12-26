# ~/Apps/rtutor/modules/doc_mode.py
import curses
import sys
import time
import re
import subprocess
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
        self.cursor_line = 0
        self.cursor_col = 0
        self.desired_display_col = 0
        self.mode = 'normal'
        self.visual_start_line = None
        self.visual_start_col = None
        self.bookmarks = Bookmarks()

        if hasattr(sequencer, 'target_lesson_name'):
            for i, lesson in enumerate(sequencer.lessons):
                if lesson.name == sequencer.target_lesson_name:
                    self.idx = i
                    break

        # For comma-then-j/k
        self.last_comma_time = 0
        self.COMMA_TIMEOUT = 0.35

        # For search - Vim style
        self.search_mode = False
        self.search_term = ""          # current term being typed
        self.last_search_term = ""     # last successful search term
        self.match_lines = []          # list of line indices that match the last successful term
        self.current_match_idx = -1    # index in match_lines of currently highlighted match
        self.search_direction_forward = True  # True = n goes forward, False = backward

    def get_display_col(self, line, char_idx):
        col = 0
        for i in range(min(char_idx, len(line))):
            if line[i] == '\t':
                col += 4
            else:
                col += 1
        return col

    def set_col_to_desired(self, line):
        line_len = len(line)
        display = 0
        col = 0
        for i in range(line_len):
            if display > self.desired_display_col:
                break
            col = i
            if line[i] == '\t':
                display += 4
            else:
                display += 1
        else:
            col = line_len
        self.cursor_col = col
        self.desired_display_col = self.get_display_col(line, col)

    def move_left(self, lines, total_lines):
        if self.cursor_col > 0:
            self.cursor_col -= 1
        elif self.cursor_line > 0:
            self.cursor_line -= 1
            self.cursor_col = len(lines[self.cursor_line])
        self.desired_display_col = self.get_display_col(lines[self.cursor_line], self.cursor_col)

    def move_right(self, lines, total_lines):
        line_len = len(lines[self.cursor_line])
        if self.cursor_col < line_len:
            self.cursor_col += 1
        elif self.cursor_line < total_lines - 1:
            self.cursor_line += 1
            self.cursor_col = 0
        self.desired_display_col = self.get_display_col(lines[self.cursor_line], self.cursor_col)

    def move_down(self, lines, total_lines):
        if self.cursor_line < total_lines - 1:
            self.cursor_line += 1
            self.set_col_to_desired(lines[self.cursor_line])

    def move_up(self, lines, total_lines):
        if self.cursor_line > 0:
            self.cursor_line -= 1
            self.set_col_to_desired(lines[self.cursor_line])

    def adjust_offset(self, total_lines, available_height):
        visible_top = self.offset
        visible_bottom = self.offset + available_height - 1
        if self.cursor_line < visible_top:
            self.offset = self.cursor_line
        elif self.cursor_line > visible_bottom:
            self.offset = self.cursor_line - available_height + 1
        self.offset = max(0, min(self.offset, total_lines - available_height))

    def get_selected_text(self, lines):
        if self.visual_start_line is None:
            return ""
        start_l = min(self.visual_start_line, self.cursor_line)
        end_l = max(self.visual_start_line, self.cursor_line)
        start_c = self.visual_start_col if self.visual_start_line <= self.cursor_line else self.cursor_col
        end_c = self.cursor_col if self.visual_start_line <= self.cursor_line else self.visual_start_col
        selected = []
        for l in range(start_l, end_l + 1):
            line = lines[l]
            if l == start_l and l == end_l:
                frag = line[start_c:end_c]
            elif l == start_l:
                frag = line[start_c:]
            elif l == end_l:
                frag = line[:end_c]
            else:
                frag = line
            selected.append(frag)
        return '\n'.join(selected)

    def _show_msg(self, stdscr, msg, delay_sec=0.8):
        max_y, max_x = stdscr.getmaxyx()
        try:
            stdscr.addstr(max_y - 1, 0, msg[:max_x], curses.A_BOLD)
            stdscr.clrtoeol()
            stdscr.refresh()
            time.sleep(delay_sec)
        except Exception:
            pass

    def run(self, stdscr):
        curses.curs_set(1)
        stdscr.nodelay(True)
        source_file = getattr(self.sequencer, "source_file", None)
        need_redraw = True

        while True:
            current_lesson = self.sequencer.lessons[self.idx]
            lines = current_lesson.content.splitlines()
            total_lines = len(lines)

            max_y, max_x = stdscr.getmaxyx()
            header_rows = 2
            footer_rows = 2
            available_height = max(0, max_y - header_rows - footer_rows)
            max_allowed_offset = max(0, total_lines - available_height)

            # Clamp offset
            self.offset = max(0, min(self.offset, max_allowed_offset))
            self.adjust_offset(total_lines, available_height)

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

                # Render content
                start_line = self.offset
                end_line = min(start_line + available_height, total_lines)
                for row_idx in range(start_line, end_line):
                    row = header_rows + (row_idx - start_line)
                    line = lines[row_idx]
                    display_pos = 0
                    for char_idx, char in enumerate(line):
                        is_selected = False
                        if self.mode == 'visual' and self.visual_start_line is not None:
                            start_l = min(self.visual_start_line, self.cursor_line)
                            end_l = max(self.visual_start_line, self.cursor_line)
                            start_c = min(self.visual_start_col, self.cursor_col) if start_l == end_l else (self.visual_start_col if row_idx == self.visual_start_line else 0)
                            end_c = max(self.visual_start_col, self.cursor_col) if start_l == end_l else (self.cursor_col if row_idx == self.cursor_line else len(line))
                            if start_l <= row_idx <= end_l:
                                if start_l < row_idx < end_l or (start_l == row_idx and char_idx >= start_c) or (end_l == row_idx and char_idx < end_c) or (start_l == end_l and start_c <= char_idx < end_c):
                                    is_selected = True
                        attr = curses.A_REVERSE if is_selected else 0
                        if char == '\t':
                            for _ in range(4):
                                if display_pos >= max_x:
                                    break
                                try:
                                    stdscr.addch(row, display_pos, ' ', curses.color_pair(1) | attr)
                                except curses.error:
                                    pass
                                display_pos += 1
                        else:
                            if display_pos >= max_x:
                                break
                            try:
                                stdscr.addch(row, display_pos, char, curses.color_pair(1) | attr)
                            except curses.error:
                                pass
                            display_pos += 1
                    try:
                        stdscr.move(row, display_pos)
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                # Clear below content
                for row in range(header_rows + (end_line - start_line), max_y - footer_rows):
                    try:
                        stdscr.move(row, 0)
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                # Footer info
                counter = f"Lesson {self.idx + 1}/{len(self.sequencer.lessons)}"
                scroll_info = ""
                if total_lines > available_height:
                    top = self.offset + 1
                    bottom = min(self.offset + available_height, total_lines)
                    scroll_info = f"  [{top}-{bottom}/{total_lines}]"

                try:
                    stdscr.addstr(max_y - 2, 0, counter + scroll_info, curses.color_pair(1))
                    stdscr.clrtoeol()
                except curses.error:
                    pass

                # Bottom line
                if self.search_mode:
                    prompt = f"/{self.search_term}"
                    try:
                        stdscr.addstr(max_y - 1, 0, prompt[:max_x], curses.color_pair(1))
                        stdscr.clrtoeol()
                    except curses.error:
                        pass
                else:
                    instr = "n=next p=prev r=rote t=teleport i=edit b=mark Ctrl+j/k=½page ,j=end ,k=top /=search n/N=next/prev match v=visual hjkl=nav y=copy Alt+Enter=back"
                    try:
                        stdscr.addstr(max_y - 1, 0, instr, curses.color_pair(1))
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                # Set cursor position
                if not self.search_mode:
                    cursor_row = header_rows + (self.cursor_line - self.offset)
                    cursor_display_col = self.get_display_col(lines[self.cursor_line], self.cursor_col)
                    if cursor_row >= header_rows and cursor_row < max_y - footer_rows and cursor_display_col < max_x:
                        stdscr.move(cursor_row, cursor_display_col)
                    curses.curs_set(1)
                else:
                    curses.curs_set(1)

                stdscr.refresh()
                need_redraw = False

            key = stdscr.getch()
            if key == -1:
                continue

            current_time = time.time()

            # === ENTER / EXIT SEARCH MODE ===
            if key == ord('/'):
                if self.search_mode:
                    self.search_mode = False
                    curses.curs_set(1)
                    stdscr.nodelay(True)
                    need_redraw = True
                else:
                    self.search_mode = True
                    self.search_term = ""
                    curses.curs_set(1)
                    stdscr.nodelay(False)
                    need_redraw = True
                continue

            # === KEYS IN SEARCH MODE ===
            if self.search_mode:
                if key in (curses.KEY_ENTER, ord('\n'), ord('\r'), 10, 13):
                    term = self.search_term.strip()

                    if not term:
                        self.search_mode = False
                        curses.curs_set(1)
                        stdscr.nodelay(True)
                        need_redraw = True
                        continue

                    if self.last_search_term != term:
                        pattern = re.compile(re.escape(term), re.IGNORECASE)
                        self.match_lines = [i for i, line in enumerate(lines) if pattern.search(line)]
                        self.last_search_term = term
                        self.current_match_idx = -1

                    if not self.match_lines:
                        self._show_msg(stdscr, f"No match for '{term}'")
                        self.search_mode = False
                        curses.curs_set(1)
                        stdscr.nodelay(True)
                        need_redraw = True
                        continue

                    # Advance forward
                    self.search_direction_forward = True
                    self.current_match_idx = (self.current_match_idx + 1) % len(self.match_lines)
                    match_line = self.match_lines[self.current_match_idx]

                    # Place match at the very top of the screen
                    self.offset = max(0, match_line)

                    # Set cursor to the start of the match
                    pattern = re.compile(re.escape(term), re.IGNORECASE)
                    match = pattern.search(lines[match_line])
                    if match:
                        self.cursor_col = match.start()
                    else:
                        self.cursor_col = 0
                    self.cursor_line = match_line
                    self.desired_display_col = self.get_display_col(lines[match_line], self.cursor_col)
                    self.adjust_offset(total_lines, available_height)

                    need_redraw = True

                    # Exit search mode after successful jump
                    self.search_mode = False
                    curses.curs_set(1)
                    stdscr.nodelay(True)

                elif key == 27:  # ESC
                    self.search_mode = False
                    curses.curs_set(1)
                    stdscr.nodelay(True)
                    need_redraw = True

                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    if self.search_term:
                        self.search_term = self.search_term[:-1]
                        need_redraw = True

                elif 32 <= key <= 126:
                    self.search_term += chr(key)
                    need_redraw = True

                continue

            # === NORMAL AND VISUAL MODE KEYS ===
            redraw_needed = False

            if self.mode == 'visual':
                if key == ord('y'):
                    text = self.get_selected_text(lines)
                    try:
                        subprocess.run(['wl-copy'], input=text.encode(), check=True)
                        self._show_msg(stdscr, "Copied to clipboard!")
                    except Exception:
                        self._show_msg(stdscr, "Failed to copy (wl-copy not available?)")
                    self.mode = 'normal'
                    self.visual_start_line = None
                    self.visual_start_col = None
                    redraw_needed = True
                elif key == ord('h') or key == curses.KEY_LEFT:
                    self.move_left(lines, total_lines)
                    self.adjust_offset(total_lines, available_height)
                    redraw_needed = True
                elif key == ord('l') or key == curses.KEY_RIGHT:
                    self.move_right(lines, total_lines)
                    self.adjust_offset(total_lines, available_height)
                    redraw_needed = True
                elif key == ord('j') or key == curses.KEY_DOWN:
                    if (current_time - self.last_comma_time) < self.COMMA_TIMEOUT:
                        self.cursor_line = total_lines - 1
                        self.cursor_col = 0
                        self.desired_display_col = 0
                    else:
                        self.move_down(lines, total_lines)
                    self.adjust_offset(total_lines, available_height)
                    redraw_needed = True
                elif key == ord('k') or key == curses.KEY_UP:
                    if (current_time - self.last_comma_time) < self.COMMA_TIMEOUT:
                        self.cursor_line = 0
                        self.cursor_col = 0
                        self.desired_display_col = 0
                    else:
                        self.move_up(lines, total_lines)
                    self.adjust_offset(total_lines, available_height)
                    redraw_needed = True
                elif key == 27:  # ESC
                    self.mode = 'normal'
                    self.visual_start_line = None
                    self.visual_start_col = None
                    redraw_needed = True
                # Ignore other keys in visual mode
            else:  # normal mode
                if key in (ord('n'), ord('N')) and self.match_lines and self.last_search_term:
                    direction = 1 if key == ord('n') else -1
                    self.current_match_idx = (self.current_match_idx + direction) % len(self.match_lines)
                    match_line = self.match_lines[self.current_match_idx]
                    self.offset = max(0, match_line)
                    pattern = re.compile(re.escape(self.last_search_term), re.IGNORECASE)
                    match = pattern.search(lines[match_line])
                    if match:
                        self.cursor_col = match.start()
                    else:
                        self.cursor_col = 0
                    self.cursor_line = match_line
                    self.desired_display_col = self.get_display_col(lines[match_line], self.cursor_col)
                    self.adjust_offset(total_lines, available_height)
                    redraw_needed = True
                    continue
                if key == ord('v'):
                    self.mode = 'visual'
                    self.visual_start_line = self.cursor_line
                    self.visual_start_col = self.cursor_col
                    redraw_needed = True
                elif key == ord('h') or key == curses.KEY_LEFT:
                    self.move_left(lines, total_lines)
                    self.adjust_offset(total_lines, available_height)
                    redraw_needed = True
                elif key == ord('l') or key == curses.KEY_RIGHT:
                    self.move_right(lines, total_lines)
                    self.adjust_offset(total_lines, available_height)
                    redraw_needed = True
                elif key == ord('j') or key == curses.KEY_DOWN:
                    if (current_time - self.last_comma_time) < self.COMMA_TIMEOUT:
                        self.cursor_line = total_lines - 1
                        self.cursor_col = 0
                        self.desired_display_col = 0
                    else:
                        self.move_down(lines, total_lines)
                    self.adjust_offset(total_lines, available_height)
                    redraw_needed = True
                elif key == ord('k') or key == curses.KEY_UP:
                    if (current_time - self.last_comma_time) < self.COMMA_TIMEOUT:
                        self.cursor_line = 0
                        self.cursor_col = 0
                        self.desired_display_col = 0
                    else:
                        self.move_up(lines, total_lines)
                    self.adjust_offset(total_lines, available_height)
                    redraw_needed = True
                elif key == 10:  # Ctrl+J
                    half_page = max(1, available_height // 2)
                    for _ in range(half_page):
                        self.move_down(lines, total_lines)
                    self.adjust_offset(total_lines, available_height)
                    redraw_needed = True
                elif key == 11:  # Ctrl+K
                    half_page = max(1, available_height // 2)
                    for _ in range(half_page):
                        self.move_up(lines, total_lines)
                    self.adjust_offset(total_lines, available_height)
                    redraw_needed = True
                elif key == ord(','):
                    self.last_comma_time = current_time
                elif key == ord('n'):
                    if self.idx < len(self.sequencer.lessons) - 1:
                        self.idx += 1
                        self.offset = 0
                        self.cursor_line = 0
                        self.cursor_col = 0
                        self.desired_display_col = 0
                        self.match_lines = []
                        self.last_search_term = ""
                        redraw_needed = True
                elif key == ord('p'):
                    if self.idx > 0:
                        self.idx -= 1
                        self.offset = 0
                        self.cursor_line = 0
                        self.cursor_col = 0
                        self.desired_display_col = 0
                        self.match_lines = []
                        self.last_search_term = ""
                        redraw_needed = True
                elif key == 3:  # Ctrl+C
                    sys.exit(0)
                elif key == 27:  # Esc/Alt
                    return False
                elif key == ord("b"):
                    import os
                    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    courses_dir = os.path.join(script_dir, "courses")
                    from modules.course_parser import CourseParser
                    parser = CourseParser(courses_dir)
                    all_courses = parser.parse_courses()
                    self.bookmarks.add(all_courses, self.sequencer.name, current_lesson.name)
                    self._show_msg(stdscr, "Bookmarked!")
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
                        self.cursor_line = 0
                        self.cursor_col = 0
                        self.desired_display_col = 0
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
                        self.cursor_line = 0
                        self.cursor_col = 0
                        self.desired_display_col = 0
                    redraw_needed = True

            if redraw_needed:
                need_redraw = True

        return False

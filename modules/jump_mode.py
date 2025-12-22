# ~/Apps/rtutor/modules/jump_mode.py

import curses
import sys
from .structs import Lesson
from .boom import Boom


class JumpMode:
    def __init__(self, sequencer_name, lessons, start_idx):
        self.sequencer_name = sequencer_name
        self.lessons = lessons
        self.current_idx = start_idx

    def run(self, stdscr):
        stdscr.nodelay(True)
        curses.curs_set(2)

        while self.current_idx < len(self.lessons):
            lesson = self.lessons[self.current_idx]
            lines = lesson.content.splitlines() or [""]
            total_lines = len(lines)

            processed_lines = []
            is_skip = []
            for line in lines:
                non_tabs = [c for c in line if c != "\t"]
                processed_lines.append(non_tabs)
                is_skip.append(line.lstrip().startswith(("#!", "//!", "--!")))

            # Virtual scrolling state
            offset = 0
            min_lines_below = 3
            current_line = 0
            user_inputs = [[] for _ in lines]
            lesson_finished = False
            need_redraw = True
            completed = False

            while not completed:
                max_y, max_x = stdscr.getmaxyx()
                available_height = max(0, max_y - 4)  # header 2 + footer 2
                content_start_y = 2

                # Smart offset adjustment
                if total_lines > available_height:
                    visible_top = offset
                    visible_bottom = offset + available_height - 1
                    lines_below = total_lines - 1 - current_line

                    if lines_below < min_lines_below and current_line > visible_bottom - min_lines_below:
                        offset = max(0, current_line - (available_height - min_lines_below - 1))
                    elif current_line < visible_top:
                        offset = current_line
                    elif current_line >= visible_top + available_height:
                        offset = current_line - available_height + 1

                    offset = max(0, min(offset, total_lines - available_height))
                else:
                    offset = 0

                start_idx = offset
                end_idx = min(offset + available_height, total_lines)
                visible_range = range(start_idx, end_idx)

                if need_redraw:
                    # Title
                    title = f"Jump Mode: {self.sequencer_name} | {lesson.name}"
                    try:
                        stdscr.addstr(0, 0, title[:max_x], curses.color_pair(1))
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                    # Clear row 1
                    try:
                        stdscr.move(1, 0)
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                    # Render visible lines only
                    for local_i, global_i in enumerate(visible_range):
                        row = content_start_y + local_i
                        line = lines[global_i]
                        user_input = user_inputs[global_i]
                        display_pos = 0
                        input_pos = 0

                        for char in line:
                            if char == "\t":
                                for _ in range(4):
                                    try:
                                        stdscr.addch(row, display_pos, " ", curses.color_pair(1))
                                    except:
                                        pass
                                    display_pos += 1
                            else:
                                ch = char
                                if input_pos < len(user_input):
                                    if (input_pos < len(processed_lines[global_i]) and
                                        user_input[input_pos] == processed_lines[global_i][input_pos]):
                                        ch = user_input[input_pos]
                                    else:
                                        ch = "█"
                                    input_pos += 1
                                if ch == "\n":
                                    ch = "↵"
                                try:
                                    stdscr.addch(row, display_pos, ch, curses.color_pair(1))
                                except:
                                    pass
                                display_pos += 1

                        while input_pos < len(user_input):
                            try:
                                stdscr.addch(row, display_pos, "█", curses.color_pair(1))
                            except:
                                pass
                            display_pos += 1
                            input_pos += 1

                        try:
                            stdscr.move(row, display_pos)
                            stdscr.clrtoeol()
                        except:
                            pass

                    # Clear leftover rows
                    for r in range(content_start_y + (end_idx - start_idx), max_y - 2):
                        try:
                            stdscr.move(r, 0)
                            stdscr.clrtoeol()
                        except:
                            pass

                    # Stats
                    typed = sum(len(ui) for i, ui in enumerate(user_inputs) if not is_skip[i])
                    total = sum(len(p) for i, p in enumerate(processed_lines) if not is_skip[i])
                    stats = f"Typed {typed}/{total} chars"

                    scroll_info = ""
                    if total_lines > available_height:
                        top = offset + 1
                        bottom = offset + (end_idx - start_idx)
                        scroll_info = f"  [{top}-{bottom}/{total_lines}]"

                    try:
                        stdscr.addstr(max_y - 2, 0, stats + scroll_info, curses.color_pair(1))
                        stdscr.clrtoeol()
                    except:
                        pass

                    # Instructions
                    instr = "Lesson complete! Hit n for next or esc to exit" if lesson_finished else "Ctrl+R → restart | ESC → quit"
                    try:
                        stdscr.addstr(max_y - 1, 0, instr, curses.color_pair(1))
                        stdscr.clrtoeol()
                    except:
                        pass

                    # Cursor
                    if not lesson_finished:
                        cursor_row = content_start_y + (current_line - offset)
                        cursor_col = 0
                        input_pos = 0
                        for char in lines[current_line]:
                            if char == "\t":
                                cursor_col += 4
                            else:
                                if input_pos < len(user_inputs[current_line]):
                                    input_pos += 1
                                    cursor_col += 1
                                else:
                                    break
                        cursor_col += len(user_inputs[current_line]) - input_pos
                        try:
                            stdscr.move(cursor_row, cursor_col)
                        except:
                            pass
                    else:
                        curses.curs_set(0)

                    stdscr.refresh()
                    need_redraw = False

                # Input handling
                changed = False
                while True:
                    key = stdscr.getch()
                    if key == -1:
                        break
                    changed = True

                    if key == 3:  # Ctrl+C
                        sys.exit(0)

                    if lesson_finished:
                        if key in (ord("n"), ord("N")):
                            completed = True
                        elif key == 27:
                            return self.current_idx
                    else:
                        if key == 18:  # Ctrl+R
                            user_inputs = [[] for _ in lines]
                            current_line = 0
                            lesson_finished = False
                        elif key == 27:
                            next_key = stdscr.getch()
                            if next_key == -1:
                                return self.current_idx
                            else:
                                key = next_key
                        elif is_skip[current_line]:
                            if key in (curses.KEY_ENTER, 10, 13):
                                if current_line < total_lines - 1:
                                    current_line += 1
                        else:
                            if key in (curses.KEY_BACKSPACE, 127, 8):
                                if user_inputs[current_line]:
                                    user_inputs[current_line].pop()
                            elif key in (curses.KEY_ENTER, 10, 13):
                                if user_inputs[current_line] == processed_lines[current_line]:
                                    if current_line < total_lines - 1:
                                        current_line += 1
                            elif key == 9:  # Tab
                                cur_len = len(user_inputs[current_line])
                                req_len = len(processed_lines[current_line])
                                if cur_len < req_len:
                                    remaining = "".join(processed_lines[current_line][cur_len:])
                                    if remaining.startswith("    "):
                                        user_inputs[current_line].extend([" ", " ", " ", " "])
                            else:
                                if 32 <= key <= 126:
                                    ch = chr(key)
                                    if len(user_inputs[current_line]) < len(processed_lines[current_line]):
                                        user_inputs[current_line].append(ch)

                # Check completion
                if all(is_skip[i] or user_inputs[i] == processed_lines[i] for i in range(total_lines)):
                    lesson_finished = True
                    changed = True

                if changed:
                    need_redraw = True

            # Next lesson
            self.current_idx += 1

        # All done
        boom = Boom("Press any key to return to doc mode.")
        boom.display(stdscr)
        stdscr.getch()
        curses.curs_set(0)
        return len(self.lessons)

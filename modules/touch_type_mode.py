# ~/Apps/worship/modules/touch_type_mode.py
# ~/Apps/rtutor/modules/jump_mode.py
import curses
import sys
from .boom import Boom


class TouchTypeMode:
    def __init__(self, sequencer_name, lessons, start_idx):
        self.sequencer_name = sequencer_name
        self.lessons = lessons
        self.current_idx = start_idx

    def run(self, stdscr):
        stdscr.nodelay(True)

        def safe_curs_set(val):
            try:
                curses.curs_set(val)
            except curses.error:
                pass

        safe_curs_set(2)

        while self.current_idx < len(self.lessons):
            lesson = self.lessons[self.current_idx]
            stdscr.clear()
            stdscr.refresh()
            safe_curs_set(2)
            lines = lesson.content.splitlines() or [""]
            total_lines = len(lines)

            processed_lines = []
            is_skip = []
            for line in lines:
                non_tabs = [c for c in line if c != "\t"]
                processed_lines.append(non_tabs)
                is_skip.append(line.lstrip().startswith(("#!", "//!", "--!")))

            offset = 0
            current_line = 0
            user_inputs = [[] for _ in lines]
            lesson_finished = False
            need_redraw = True
            completed = False

            while not completed:
                max_y, max_x = stdscr.getmaxyx()
                header_rows = 3
                footer_rows = 2
                available_height = max(0, max_y - header_rows - footer_rows)
                content_start_y = header_rows

                # === Smooth, early scrolling + extra lookahead near end ===
                if total_lines > available_height:
                    visible_top = offset
                    visible_bottom = offset + available_height - 1
                    current_visible_row = current_line - offset

                    scroll_trigger_row = int(available_height * 0.6)

                    if current_visible_row > scroll_trigger_row:
                        scroll_amount = current_visible_row - scroll_trigger_row
                        offset += scroll_amount

                    lines_below = total_lines - 1 - current_line
                    if lines_below <= 20:
                        desired_offset = max(
                            0, current_line - int(available_height * 0.3)
                        )
                        offset = max(offset, desired_offset)

                    offset = max(0, min(offset, total_lines - available_height))
                else:
                    offset = 0

                start_idx = offset
                end_idx = min(offset + available_height, total_lines)
                visible_range = range(start_idx, end_idx)

                if need_redraw:
                    # Title on two lines
                    line1 = self.sequencer_name
                    line2 = f"TOUCH_TYPE_MODE: {lesson.name}"
                    try:
                        stdscr.addstr(
                            0, 0, line1[:max_x], curses.color_pair(1) | curses.A_BOLD
                        )
                        stdscr.addstr(
                            1, 0, line2[:max_x], curses.color_pair(1) | curses.A_BOLD
                        )
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                    # Empty line
                    try:
                        stdscr.move(2, 0)
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                    # Render visible lines
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
                                        stdscr.addch(
                                            row, display_pos, " ", curses.color_pair(1)
                                        )
                                    except:
                                        pass
                                    display_pos += 1
                            else:
                                ch = char
                                if input_pos < len(user_input):
                                    if (
                                        input_pos < len(processed_lines[global_i])
                                        and user_input[input_pos]
                                        == processed_lines[global_i][input_pos]
                                    ):
                                        ch = user_input[input_pos]
                                    else:
                                        ch = "█"
                                    input_pos += 1
                                if ch == "\n":
                                    ch = "↵"
                                try:
                                    stdscr.addch(
                                        row, display_pos, ch, curses.color_pair(1)
                                    )
                                except:
                                    pass
                                display_pos += 1

                        while input_pos < len(user_input):
                            try:
                                stdscr.addch(
                                    row, display_pos, "█", curses.color_pair(1)
                                )
                            except:
                                pass
                            display_pos += 1
                            input_pos += 1

                        try:
                            stdscr.move(row, display_pos)
                            stdscr.clrtoeol()
                        except:
                            pass

                    # Clear remaining lines below content to footer
                    content_end_row = content_start_y + (end_idx - start_idx)
                    clear_start = content_end_row
                    clear_end = max_y - footer_rows

                    for r in range(clear_start, clear_end):
                        try:
                            stdscr.move(r, 0)
                            stdscr.clrtoeol()
                        except curses.error:
                            pass

                    # Stats
                    typed = sum(
                        len(ui) for i, ui in enumerate(user_inputs) if not is_skip[i]
                    )
                    total = sum(
                        len(p) for i, p in enumerate(processed_lines) if not is_skip[i]
                    )
                    stats = f"Typed {typed}/{total} chars"

                    scroll_info = ""
                    if total_lines > available_height:
                        top = offset + 1
                        bottom = offset + (end_idx - start_idx)
                        scroll_info = f"  [{top}-{bottom}/{total_lines}]"

                    footer_line = (stats + scroll_info)[:max_x]
                    try:
                        stdscr.addstr(max_y - 2, 0, footer_line, curses.color_pair(1))
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                    # Updated instructions
                    if lesson_finished:
                        instr = "Lesson complete! Hit n for next | Esc/Q to return"
                    else:
                        instr = "Ctrl+R → restart | Esc/Q → return"

                    try:
                        stdscr.addstr(max_y - 1, 0, instr[:max_x], curses.color_pair(1))
                        stdscr.clrtoeol()
                    except curses.error:
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
                        safe_curs_set(2)
                        try:
                            stdscr.move(cursor_row, cursor_col)
                        except:
                            pass
                    else:
                        safe_curs_set(0)

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

                    # === NEW: Proper ESC handling ===
                    if key == 27:  # ESC
                        next_key = stdscr.getch()
                        if next_key == -1:
                            return self.current_idx
                        elif next_key in (curses.KEY_ENTER, 10, 13):
                            return self.current_idx
                        continue

                    if lesson_finished:
                        if key in (ord("n"), ord("N")):
                            completed = True
                        elif key in (ord("q"), ord("Q")):
                            return self.current_idx
                    else:
                        if key == 18:  # Ctrl+R
                            user_inputs = [[] for _ in lines]
                            current_line = 0
                            lesson_finished = False
                        elif is_skip[current_line]:
                            if key in (curses.KEY_ENTER, 10, 13):
                                if current_line < total_lines - 1:
                                    current_line += 1
                        else:
                            if key in (curses.KEY_BACKSPACE, 127, 8):
                                if user_inputs[current_line]:
                                    user_inputs[current_line].pop()
                            elif key in (curses.KEY_ENTER, 10, 13):
                                if (
                                    user_inputs[current_line]
                                    == processed_lines[current_line]
                                ):
                                    if current_line < total_lines - 1:
                                        current_line += 1
                            elif key == 9:  # Tab
                                cur_len = len(user_inputs[current_line])
                                req_len = len(processed_lines[current_line])
                                if cur_len < req_len:
                                    remaining = "".join(
                                        processed_lines[current_line][cur_len:]
                                    )
                                    if remaining.startswith("    "):
                                        user_inputs[current_line].extend(
                                            [" ", " ", " ", " "]
                                        )
                            else:
                                if 32 <= key <= 126:
                                    ch = chr(key)
                                    if len(user_inputs[current_line]) < len(
                                        processed_lines[current_line]
                                    ):
                                        user_inputs[current_line].append(ch)

                # Check completion
                if all(
                    is_skip[i] or user_inputs[i] == processed_lines[i]
                    for i in range(total_lines)
                ):
                    lesson_finished = True
                    changed = True

                if changed:
                    need_redraw = True

            # Advance to next lesson after completing this one with 'n'
            self.current_idx += 1

        # All lessons completed in touch type mode
        boom = Boom("Press any key to return to doc mode.")
        boom.display(stdscr)
        stdscr.getch()
        curses.curs_set(0)
        return len(self.lessons)

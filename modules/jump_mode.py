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
        curses.curs_set(2)  # Visible blinking block cursor

        while self.current_idx < len(self.lessons):
            lesson = self.lessons[self.current_idx]

            # Preprocess lesson once
            lines = lesson.content.strip().splitlines()
            processed_lines = []
            tab_positions = []
            is_skip = []
            for line in lines:
                non_tabs = [c for c in line if c != "\t"]
                tabs = [i for i, c in enumerate(line) if c == "\t"]
                processed_lines.append(non_tabs)
                tab_positions.append(tabs)
                is_skip.append(line.lstrip().startswith(("#!", "//!")))

            # Just one run, no rep nonsense
            stdscr.clear()
            stdscr.refresh()
            curses.curs_set(2)  # Reset cursor visibility for each new lesson
            current_line = 0
            user_inputs = [[] for _ in lines]
            lesson_finished = False
            need_redraw = True
            completed = False  # Track lesson completion like in sequencer

            while not completed:
                if need_redraw:
                    # Draw title without rep count—keep it simple
                    title = f"Jump Mode: {self.sequencer_name} | {lesson.name}"
                    try:
                        stdscr.addstr(0, 0, title, curses.color_pair(1))
                        stdscr.move(0, len(title))
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                    # Clear line 1
                    try:
                        stdscr.move(1, 0)
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                    # Display lines (reused logic, no changes needed)
                    display_row = 2
                    for i, line in enumerate(lines):
                        target_text = line
                        user_input = user_inputs[i]
                        display_pos = 0
                        input_pos = 0
                        for j, char in enumerate(target_text):
                            if char == "\t":
                                for _ in range(4):
                                    try:
                                        stdscr.addch(
                                            display_row,
                                            display_pos,
                                            " ",
                                            curses.color_pair(1),
                                        )
                                    except curses.error:
                                        pass
                                    display_pos += 1
                            else:
                                display_char = char
                                if input_pos < len(user_input):
                                    if (
                                        input_pos < len(processed_lines[i])
                                        and user_input[input_pos]
                                        == processed_lines[i][input_pos]
                                    ):
                                        display_char = user_input[input_pos]
                                    else:
                                        display_char = "█"
                                    input_pos += 1
                                if display_char == "\n":
                                    display_char = "↵"
                                try:
                                    stdscr.addch(
                                        display_row,
                                        display_pos,
                                        display_char,
                                        curses.color_pair(1),
                                    )
                                except curses.error:
                                    pass
                                display_pos += 1
                        while input_pos < len(user_input):
                            try:
                                stdscr.addch(
                                    display_row, display_pos, "█", curses.color_pair(1)
                                )
                            except curses.error:
                                pass
                            display_pos += 1
                            input_pos += 1
                        try:
                            stdscr.move(display_row, display_pos)
                            stdscr.clrtoeol()
                        except curses.error:
                            pass
                        display_row += 1

                    max_y, max_x = stdscr.getmaxyx()

                    for row in range(display_row, max_y - 2):
                        try:
                            stdscr.move(row, 0)
                            stdscr.clrtoeol()
                        except curses.error:
                            pass

                    typed_count = sum(
                        len(user_inputs[i]) for i in range(len(lines)) if not is_skip[i]
                    )
                    total_count = sum(
                        len(processed_lines[i])
                        for i in range(len(lines))
                        if not is_skip[i]
                    )
                    stats = f"Typed {typed_count}/{total_count} chars"
                    try:
                        stdscr.addstr(max_y - 2, 0, stats, curses.color_pair(1))
                        stdscr.move(max_y - 2, len(stats))
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                    if lesson_finished:
                        instr = "Lesson complete! Hit n for next lesson or esc to exit"
                    else:
                        instr = "Ctrl+R -> restart | ESC -> quit"
                    try:
                        stdscr.addstr(max_y - 1, 0, instr, curses.color_pair(1))
                        stdscr.move(max_y - 1, len(instr))
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                    if not lesson_finished:
                        cursor_col = 0
                        input_pos = 0
                        if current_line < len(lines):
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
                        display_row = 2 + current_line
                        try:
                            stdscr.move(display_row, cursor_col)
                        except curses.error:
                            pass
                    else:
                        curses.curs_set(0)

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
                        if lesson_finished:
                            if key == ord("n") or key == ord("N"):
                                completed = True
                            elif key == 27:  # ESC or Alt prefix
                                next_key = stdscr.getch()
                                if next_key == -1:
                                    # Bare ESC, back to doc mode
                                    return self.current_idx
                                else:
                                    # Alt + something, ignore in finished state
                                    pass
                            # Ignore other keys
                        else:
                            if key == 18:  # Ctrl+R
                                user_inputs = [[] for _ in lines]
                                current_line = 0
                                lesson_finished = False
                            elif key == 27:  # ESC or Alt prefix
                                next_key = stdscr.getch()
                                if next_key == -1:
                                    # Bare ESC, get the hell out
                                    return self.current_idx
                                else:
                                    # Alt + next_key, pretend it's just the key (no Alt modifier)
                                    key = next_key
                                    # Fall through to process this key as normal input
                            elif is_skip[current_line]:
                                if key in (curses.KEY_ENTER, 10, 13):
                                    if current_line < len(lines) - 1:
                                        current_line += 1
                                # Ignore backspace, tab, typing, etc.
                            else:
                                if key in (curses.KEY_BACKSPACE, 127, 8):
                                    if user_inputs[current_line]:
                                        user_inputs[current_line].pop()
                                elif key in (curses.KEY_ENTER, 10, 13):
                                    if (
                                        user_inputs[current_line]
                                        == processed_lines[current_line]
                                    ):
                                        if current_line < len(lines) - 1:
                                            current_line += 1
                                elif key == 9:  # Tab
                                    if processed_lines[current_line]:
                                        required_len = len(
                                            processed_lines[current_line]
                                        )
                                        current_len = len(user_inputs[current_line])
                                        if current_len < required_len:
                                            next_chars = "".join(
                                                processed_lines[current_line][
                                                    current_len:
                                                ]
                                            )
                                            if next_chars.startswith("    "):
                                                user_inputs[current_line].extend(
                                                    [" ", " ", " ", " "]
                                                )
                                else:
                                    typed_char = None
                                    if 32 <= key <= 126:
                                        typed_char = chr(key)
                                    if typed_char:
                                        required_len = len(
                                            processed_lines[current_line]
                                        )
                                        current_len = len(user_inputs[current_line])
                                        if current_len < required_len:
                                            user_inputs[current_line].append(typed_char)

                        # Check if lesson is finished after key (only if not already finished)
                        if not lesson_finished:
                            all_lines_typed = all(
                                is_skip[i] or user_inputs[i] == processed_lines[i]
                                for i in range(len(lines))
                            )
                            if all_lines_typed:
                                lesson_finished = True

                    except KeyboardInterrupt:
                        sys.exit(0)
                    except curses.error:
                        pass

                if changed or lesson_finished:
                    need_redraw = True

            # Lesson done, move to next
            self.current_idx += 1

        # All lessons done, do the "boom" thing
        boom = Boom("Press any key to return to doc mode.")
        boom.display(stdscr)
        stdscr.getch()  # Wait for key to acknowledge
        curses.curs_set(0)
        return len(self.lessons)  # Signal full completion

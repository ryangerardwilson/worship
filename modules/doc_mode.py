import curses
import sys
from .structs import Lesson
from .rote_mode import RoteMode
from .jump_mode import JumpMode


class DocMode:
    def __init__(self, sequencer):
        self.sequencer = sequencer

    def run(self, stdscr):
        curses.curs_set(0)
        stdscr.nodelay(True)

        idx = 0
        need_redraw = True

        while True:
            if need_redraw:
                stdscr.clear()
                try:
                    title = (
                        f"{self.sequencer.name} | {self.sequencer.lessons[idx].name}"
                    )
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

                # Draw content
                lines = self.sequencer.lessons[idx].content.strip().splitlines()
                max_y, max_x = stdscr.getmaxyx()
                row = 2
                for line in lines:
                    disp = line.replace("\t", "    ")
                    # Safely draw within screen width
                    try:
                        stdscr.addstr(row, 0, disp[:max_x], curses.color_pair(1))
                        stdscr.move(row, min(len(disp), max_x))
                        stdscr.clrtoeol()
                    except curses.error:
                        pass
                    row += 1
                    if row >= max_y - 2:
                        break

                # Clear between content and status
                for r in range(row, max_y - 2):
                    try:
                        stdscr.move(r, 0)
                        stdscr.clrtoeol()
                    except curses.error:
                        pass

                # Footer
                footer_left = f"Lesson {idx + 1}/{len(self.sequencer.lessons)}"
                instr = "Doc mode: n-next | p-prev | r-rote | j-jump | esc-back"
                try:
                    stdscr.addstr(max_y - 2, 0, footer_left, curses.color_pair(1))
                    stdscr.move(max_y - 2, len(footer_left))
                    stdscr.clrtoeol()
                except curses.error:
                    pass
                try:
                    stdscr.addstr(max_y - 1, 0, instr, curses.color_pair(1))
                    stdscr.move(max_y - 1, len(instr))
                    stdscr.clrtoeol()
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
                    elif key in (ord("n"), ord("N")):
                        if idx < len(self.sequencer.lessons) - 1:
                            idx += 1
                    elif key in (ord("p"), ord("P")):
                        if idx > 0:
                            idx -= 1
                    elif key in (ord("r"), ord("R")):
                        # Enter rote mode for current lesson
                        rote = RoteMode(
                            self.sequencer.name, self.sequencer.lessons[idx]
                        )
                        rote_completed = rote.run(stdscr)
                        # No boom here anymore; rote handles it
                        # Reset nodelay and curs_set after rote
                        stdscr.nodelay(True)
                        curses.curs_set(0)
                        need_redraw = True
                    elif key in (ord("j"), ord("J")):
                        # Enter jump mode starting from current lesson index
                        jump = JumpMode(
                            self.sequencer.name, self.sequencer.lessons, idx
                        )
                        final_idx = jump.run(stdscr)
                        if final_idx is not None:
                            if final_idx >= len(self.sequencer.lessons):
                                return True  # Sequence completed, exit to higher menu
                            idx = (
                                final_idx  # Update the doc index to where jump left off
                            )
                        # Reset nodelay and curs_set after jump
                        stdscr.nodelay(True)
                        curses.curs_set(0)
                        need_redraw = True
                except KeyboardInterrupt:
                    sys.exit(0)
                except curses.error:
                    pass

            if changed:
                need_redraw = True

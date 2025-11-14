import curses
from .ascii import boom_art


class Boom:
    def __init__(self, message="Press any key to exit."):
        self.message = message

    def display(self, stdscr):
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        art_lines = boom_art.splitlines()
        content_width = max(len(line) for line in art_lines)
        start_y = 2
        for i, line in enumerate(art_lines):
            if line:
                x_pos = (max_x - content_width) // 2
                if x_pos < 0:
                    line = line[:max_x]
                    x_pos = 0
                try:
                    stdscr.addstr(start_y + i, x_pos, line, curses.color_pair(1))
                except curses.error:
                    pass
        try:
            stdscr.addstr(
                max_y - 1,
                0,
                self.message,
                curses.color_pair(1),
            )
        except curses.error:
            pass
        stdscr.refresh()
        stdscr.nodelay(False)
        stdscr.getch()

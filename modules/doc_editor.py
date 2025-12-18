import os
import re
import subprocess
import curses

class DocEditor:
    """
    Encapsulates logic to edit a lesson in the source markdown using Vim.
    Usage: instantiate with source_file path, then call edit_lesson(stdscr, lesson_name, current_idx).
    Returns (reloaded_lessons, course_name, new_idx) on success, or None on failure/no-change.
    """

    def __init__(self, source_file):
        self.source_file = source_file

    def _show_msg(self, stdscr, msg, max_y, max_x, delay_ms=1500):
        try:
            stdscr.addstr(max_y - 1, 0, msg[:max_x], curses.A_BOLD)
            stdscr.clrtoeol()
            stdscr.refresh()
            curses.napms(delay_ms)
        except Exception:
            pass

    def edit_lesson(self, stdscr, lesson_name, current_idx):
        # Validate
        if not self.source_file or not os.path.exists(self.source_file):
            max_y, max_x = stdscr.getmaxyx()
            self._show_msg(stdscr, "Error: No source file", max_y, max_x)
            return None

        lesson_name = (lesson_name or "").strip()
        if not lesson_name:
            return None

        # Quick Python check so we don't launch vim needlessly
        try:
            with open(self.source_file, "r", encoding="utf-8") as fh:
                body = fh.read()
        except Exception:
            max_y, max_x = stdscr.getmaxyx()
            self._show_msg(stdscr, "Error: Cannot read source file", max_y, max_x)
            return None

        heading_rx = re.compile(rf"^####[ \t]*{re.escape(lesson_name)}[ \t]*$", re.MULTILINE)
        if not heading_rx.search(body):
            max_y, max_x = stdscr.getmaxyx()
            self._show_msg(stdscr, "Error: Heading not found in source file", max_y, max_x)
            return None

        # Build a Vim literal search: use \V (very nomagic), only escape backslashes and slashes
        # (slashes are the search delimiter). This avoids using Python's re.escape for Vim.
        vim_literal = r'\V' + lesson_name.replace('\\', r'\\').replace('/', r'\/')

        # Exit curses mode, run vim, then return
        try:
            curses.endwin()
        except Exception:
            pass

        try:
            # Run vim without a shell to avoid quoting issues
            subprocess.run(['vim', self.source_file, f'+/{vim_literal}'])
        except Exception:
            # If launching vim fails, try to restore curses and show message
            try:
                stdscr.refresh()
            except Exception:
                pass
            return None

        # === RELOAD COURSE AFTER EDITING ===
        try:
            from modules.course_parser import CourseParser
            parser = CourseParser(os.path.dirname(self.source_file))
            new_course = parser._parse_md_file(self.source_file)
            if not new_course:
                return None

            reloaded_lessons = []
            for part in new_course.parts:
                for section in part.sections:
                    reloaded_lessons.extend(section.lessons)

            # Try to stay on the same lesson name if possible
            for new_idx, lesson in enumerate(reloaded_lessons):
                if lesson.name.strip() == lesson_name:
                    return reloaded_lessons, new_course.name, new_idx

            # not found: clamp index
            new_idx = min(current_idx, len(reloaded_lessons) - 1) if reloaded_lessons else 0
            return reloaded_lessons, new_course.name, new_idx

        except Exception:
            return None

        finally:
            # restore the curses screen (DocMode will touchwin/refresh)
            try:
                stdscr.refresh()
            except Exception:
                pass


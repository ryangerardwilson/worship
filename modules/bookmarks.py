# ~/Apps/rtutor/modules/bookmarks.py
import os
from pathlib import Path
import curses


class Bookmarks:
    BOOKMARKS_FILE = Path(os.path.expanduser("~/.config/worship/bookmarks.conf"))

    def __init__(self):
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        self.BOOKMARKS_FILE.parent.mkdir(parents=True, exist_ok=True)

    def add(self, courses, display_name, lesson_name):
        # Find real hierarchy
        course_name = part_name = section_name = ""

        for course in courses:
            if display_name == course.name or display_name.startswith(course.name + ":"):
                for part in course.parts:
                    for section in part.sections:
                        for lesson in section.lessons:
                            if lesson.name == lesson_name:
                                course_name = course.name
                                part_name = part.name
                                section_name = section.name
                                break
                        if course_name: break
                    if course_name: break
                if course_name: break

        if not course_name:
            course_name = display_name.split(":")[0] if ":" in display_name else display_name

        block = (
            f"Course: {course_name}\n"
            f"\tPart: {part_name}\n"
            f"\tSection: {section_name}\n"
            f"\tLesson: {lesson_name}\n"
            "\n"
        )

        with self.BOOKMARKS_FILE.open("a", encoding="utf-8") as f:
            f.write(block)

    def _parse_bookmarks(self):
        if not self.BOOKMARKS_FILE.exists():
            return []

        content = self.BOOKMARKS_FILE.read_text(encoding="utf-8")
        blocks = [b.strip() for b in content.split("\n\n") if b.strip()]

        items = []
        for block in blocks:
            data = {}
            for line in block.splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    data[key.strip()] = value.strip()

            if "Course" in data and "Lesson" in data:
                parts = [data["Course"]]
                if data.get("Part"):
                    parts.append(data["Part"])
                if data.get("Section"):
                    parts.append(data["Section"])
                parts.append(data["Lesson"])
                display = " > ".join(parts)
                items.append((display, data["Course"], data.get("Part", ""), data.get("Section", ""), data["Lesson"]))

        items.sort(key=lambda x: x[0].lower())
        return items

    def remove(self, display_name: str):
        if not self.BOOKMARKS_FILE.exists():
            return

        content = self.BOOKMARKS_FILE.read_text(encoding="utf-8")
        blocks = [b.strip() for b in content.split("\n\n") if b.strip()]

        new_blocks = []
        for block in blocks:
            lines = block.splitlines()
            data = {}
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    data[key.strip()] = value.strip()

            if "Course" in data and "Lesson" in data:
                parts = [data["Course"]]
                if data.get("Part"):
                    parts.append(data["Part"])
                if data.get("Section"):
                    parts.append(data["Section"])
                parts.append(data["Lesson"])
                block_display = " > ".join(parts)

                if block_display != display_name:
                    new_blocks.append(block)

        if new_blocks:
            self.BOOKMARKS_FILE.write_text("\n\n".join(new_blocks) + "\n\n", encoding="utf-8")
        else:
            self.BOOKMARKS_FILE.unlink(missing_ok=True)

    def show_menu_and_jump(self, stdscr, courses):
        items = self._parse_bookmarks()
        if not items:
            max_y, max_x = stdscr.getmaxyx()
            msg = "No bookmarks yet. Press any key..."
            try:
                stdscr.addstr(max_y // 2, (max_x - len(msg)) // 2, msg, curses.A_BOLD)
                stdscr.refresh()
                stdscr.nodelay(False)
                stdscr.getch()
                stdscr.nodelay(True)
            except:
                pass
            return None

        selected = 0
        last_d_time = 0  # Timestamp of last 'd' press
        need_redraw = True
        curses.curs_set(0)

        while True:
            if need_redraw:
                stdscr.clear()
                max_y, max_x = stdscr.getmaxyx()

                try:
                    stdscr.addstr(0, 0, "Bookmarks", curses.color_pair(1))
                    stdscr.clrtoeol()
                except:
                    pass

                # Safe width calculation
                menu_width = 40
                if items:
                    menu_width = max(len(disp) for disp, _, _, _, _ in items) + 4

                menu_x = max((max_x - menu_width) // 2, 0)
                start_y = 2

                for i, (display, _, _, _, _) in enumerate(items):
                    prefix = "> " if i == selected else "  "
                    line = f"{prefix}{display}"
                    try:
                        stdscr.addstr(start_y + i, menu_x, line, curses.color_pair(1))
                        stdscr.clrtoeol()
                    except:
                        pass

                instr = "j/k navigate | Enter/l go | dd delete | esc back"
                try:
                    stdscr.addstr(max_y - 1, 0, instr, curses.color_pair(1))
                except:
                    pass

                stdscr.refresh()
                need_redraw = False

            key = stdscr.getch()
            if key == -1:
                continue

            current_time = curses.getsyx()[1]  # Rough timestamp via curses internal counter

            if key in (ord('j'), curses.KEY_DOWN):
                selected = (selected + 1) % len(items)
                need_redraw = True
            elif key in (ord('k'), curses.KEY_UP):
                selected = (selected - 1) % len(items)
                need_redraw = True
            elif key in (curses.KEY_ENTER, ord('\n'), ord('\r'), ord('l')):
                _, course_name, part_name, section_name, lesson_name = items[selected]
                return (course_name, part_name, section_name, lesson_name)
            elif key == 27:  # ESC
                return None
            elif key == ord('d'):
                # Only accept second 'd' if within ~500ms
                if last_d_time and (current_time - last_d_time < 50):  # adjust sensitivity if needed
                    display, _, _, _, _ = items[selected]
                    self.remove(display)
                    items = self._parse_bookmarks()
                    if not items:
                        # Last bookmark deleted — exit menu cleanly
                        return None
                    if selected >= len(items):
                        selected = len(items) - 1
                    need_redraw = True
                # Always update timestamp on first 'd'
                last_d_time = current_time
            else:
                last_d_time = 0  # Reset on any other key

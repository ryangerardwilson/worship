# ~/Apps/rtutor/modules/course_parser.py
import os
from modules.structs import Course, Part, Section, Lesson


class CourseParser:
    def __init__(self, courses_dir):
        self.courses_dir = os.path.abspath(courses_dir)

    def parse_courses(self):
        """Parse all .md files in the courses_dir into a list of Course objects."""
        courses = []
        if not os.path.isdir(self.courses_dir):
            raise FileNotFoundError(f"Directory {self.courses_dir} does not exist")

        for filename in os.listdir(self.courses_dir):
            if filename.endswith(".md"):
                filepath = os.path.join(self.courses_dir, filename)
                course = self._parse_md_file(filepath)
                if course:
                    courses.append(course)
                else:
                    print(f"Failed to parse course from: {filepath}")
        return courses

    def _parse_md_file(self, filepath):
        """Parse a single .md file into a Course object."""
        course_name = None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return None

        # Detect hierarchy levels
        has_parts = any(line.lstrip().startswith("### ") for line in lines)
        has_sections = any(line.lstrip().startswith("#### ") for line in lines)

        if has_sections:
            # Full hierarchy: # course, ## part, ### section, #### lesson
            parts = []
            current_part = None
            current_section = None
            current_lesson_name = None
            lesson_content = []
            in_code_block = False

            for line in lines:
                line = line.rstrip("\n")

                if line.startswith("# "):
                    if course_name:
                        print(f"Error: Multiple course names in {filepath}")
                        return None
                    course_name = line[2:].strip()
                    continue

                if line.startswith("## "):
                    if current_lesson_name and lesson_content:
                        content = "\n".join(lesson_content) + "\n" * 7
                        current_section.lessons.append(
                            Lesson(current_lesson_name, content)
                        )
                        lesson_content = []
                    if current_section:
                        current_part.sections.append(current_section)
                    if current_part:
                        parts.append(current_part)
                    current_part = Part(line[3:].strip(), [])
                    current_section = None
                    current_lesson_name = None
                    in_code_block = False
                    continue

                if line.startswith("### "):
                    if current_lesson_name and lesson_content:
                        content = "\n".join(lesson_content) + "\n" * 7
                        current_section.lessons.append(
                            Lesson(current_lesson_name, content)
                        )
                        lesson_content = []
                    if current_section:
                        current_part.sections.append(current_section)
                    if not current_part:
                        return None
                    current_section = Section(line[4:].strip(), [])
                    current_lesson_name = None
                    in_code_block = False
                    continue

                if line.startswith("#### "):
                    if current_lesson_name and lesson_content:
                        content = "\n".join(lesson_content) + "\n" * 7
                        current_section.lessons.append(
                            Lesson(current_lesson_name, content)
                        )
                        lesson_content = []
                    if not current_section:
                        print(f"Error: Lesson without section in {filepath}")
                        return None
                    current_lesson_name = line[5:].strip()
                    in_code_block = False
                    continue

                if current_lesson_name and (
                    line.startswith("    ") or line.startswith("\t")
                ):
                    in_code_block = True
                    content_line = line[4:] if line.startswith("    ") else line[1:]
                    lesson_content.append(content_line.rstrip())
                    continue

                if in_code_block and not line.strip():
                    lesson_content.append("")
                    continue

                if (
                    in_code_block
                    and line.strip()
                    and not (line.startswith("    ") or line.startswith("\t"))
                ):
                    in_code_block = False

            # Final save
            if current_lesson_name and lesson_content:
                content = "\n".join(lesson_content) + "\n" * 7
                current_section.lessons.append(Lesson(current_lesson_name, content))
            if current_section:
                current_part.sections.append(current_section)
            if current_part:
                parts.append(current_part)

            if course_name and parts:
                return Course(course_name, parts, source_file=filepath)
            return None

        elif has_parts:
            # Mid hierarchy: # course, ## part, ### lesson
            parts = []
            current_part = None
            current_lesson_name = None
            lesson_content = []
            in_code_block = False

            for line in lines:
                line = line.rstrip("\n")

                if line.startswith("# "):
                    if course_name:
                        print(f"Error: Multiple course names in {filepath}")
                        return None
                    course_name = line[2:].strip()
                    continue

                if line.startswith("## "):
                    if current_lesson_name and lesson_content:
                        content = "\n".join(lesson_content) + "\n" * 7
                        current_part.sections[-1].lessons.append(
                            Lesson(current_lesson_name, content)
                        )
                        lesson_content = []
                    if current_part:
                        parts.append(current_part)
                    current_part = Part(line[3:].strip(), [Section("Main", [])])
                    current_lesson_name = None
                    in_code_block = False
                    continue

                if line.startswith("### "):
                    if current_lesson_name and lesson_content:
                        content = "\n".join(lesson_content) + "\n" * 7
                        current_part.sections[-1].lessons.append(
                            Lesson(current_lesson_name, content)
                        )
                        lesson_content = []
                    if not current_part:
                        print(f"Error: Lesson without part in {filepath}")
                        return None
                    current_lesson_name = line[4:].strip()
                    in_code_block = False
                    continue

                if current_lesson_name and (
                    line.startswith("    ") or line.startswith("\t")
                ):
                    in_code_block = True
                    content_line = line[4:] if line.startswith("    ") else line[1:]
                    lesson_content.append(content_line.rstrip())
                    continue

                if in_code_block and not line.strip():
                    lesson_content.append("")
                    continue

                if (
                    in_code_block
                    and line.strip()
                    and not (line.startswith("    ") or line.startswith("\t"))
                ):
                    in_code_block = False

            # Final save
            if current_lesson_name and lesson_content:
                content = "\n".join(lesson_content) + "\n" * 7
                current_part.sections[-1].lessons.append(
                    Lesson(current_lesson_name, content)
                )
            if current_part:
                parts.append(current_part)

            if course_name and parts:
                return Course(course_name, parts, source_file=filepath)
            return None

        else:
            # Flat structure: # course, ## lesson
            lessons = []
            current_lesson_name = None
            lesson_content = []
            in_code_block = False

            for line in lines:
                line = line.rstrip("\n")

                if line.startswith("# "):
                    if course_name:
                        print(f"Error: Multiple course names in {filepath}")
                        return None
                    course_name = line[2:].strip()
                    continue

                if line.startswith("## "):
                    if current_lesson_name and lesson_content:
                        content = "\n".join(lesson_content) + "\n" * 7
                        lessons.append(Lesson(current_lesson_name, content))
                        lesson_content = []
                    current_lesson_name = line[3:].strip()
                    in_code_block = False
                    continue

                if current_lesson_name and (
                    line.startswith("    ") or line.startswith("\t")
                ):
                    in_code_block = True
                    content_line = line[4:] if line.startswith("    ") else line[1:]
                    lesson_content.append(content_line.rstrip())
                    continue

                if in_code_block and not line.strip():
                    lesson_content.append("")
                    continue

                if (
                    in_code_block
                    and line.strip()
                    and not (line.startswith("    ") or line.startswith("\t"))
                ):
                    in_code_block = False

            # Final save
            if current_lesson_name and lesson_content:
                content = "\n".join(lesson_content) + "\n" * 7
                lessons.append(Lesson(current_lesson_name, content))

            if course_name and lessons:
                sections = [Section("Main", lessons)]
                parts = [Part("Main", sections)]
                return Course(course_name, parts, source_file=filepath)
            return None

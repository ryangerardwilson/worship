# ~/Apps/rtutor/modules/structs.py


class Lesson:
    def __init__(self, name, content):
        self.name = name  # Lesson name, e.g., "Lesson1"
        self.content = content  # Multiline string for typing practice


class Section:
    def __init__(self, name, lessons):
        self.name = name  # Section name, e.g., "Section 1: Basics"
        self.lessons = lessons  # List of Lesson objects


class Part:
    def __init__(self, name, sections):
        self.name = name  # Part name, e.g., "Part IA: Chapter 1"
        self.sections = sections  # List of Section objects


class Course:
    def __init__(self, name, parts, source_file=None):
        self.name = name  # Course name, e.g., "Basic Typing"
        self.parts = parts  # List of Part objects
        self.source_file = source_file  # Path to the original .md file

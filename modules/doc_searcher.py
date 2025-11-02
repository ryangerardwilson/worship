import curses
import re
import sys
from difflib import SequenceMatcher
from modules.structs import Lesson


class DocSearcher:
    def __init__(self, courses, threshold=0.7):
        self.courses = courses
        self.threshold = float(threshold)

    def try_run(self, argv):
        """
        If -c is present with extra tokens, print best match to stdout and exit.
        If -d/--doc is present with extra tokens, run direct doc-mode search and exit.
        Otherwise, return False (let menus handle it).
        """
        # Cat mode takes precedence if both flags are present.
        c_tokens = self._extract_flag_args(argv, ["-c", "--cat"])
        if c_tokens:
            self._cat_best(c_tokens)
            return True

        tokens = self._extract_flag_args(argv, ["-d", "--doc"])
        if not tokens:
            return False  # Not our job

        matches = self._search_lessons(tokens)
        if not matches:
            print(f"No matching lessons found for -d arguments: {' | '.join(tokens)}")
            raise SystemExit(1)

        def _run_direct(stdscr):
            from modules.lesson_sequencer import LessonSequencer

            if len(tokens) == 1:
                seq_name = f"Doc search: {tokens[0]}"
            else:
                hierarchy = " > ".join(tokens[:-1])
                seq_name = f"Doc search: {hierarchy} :: {tokens[-1]}"
            sequencer = LessonSequencer(seq_name, matches, doc_mode=True)
            sequencer.run(stdscr)

        try:
            curses.wrapper(_run_direct)
        except KeyboardInterrupt:
            raise SystemExit(0)
        return True

    # ---- Arg parsing ----

    def _extract_flag_args(self, argv, flags):
        """
        Grab tokens after any of the given flags until the next "-" option or end.
        Returns [] if none of the flags are present.
        """
        idx = -1
        for f in flags:
            if f in argv:
                idx = argv.index(f)
                break
        if idx == -1:
            return []
        args = []
        for a in argv[idx + 1 :]:
            if a.startswith("-"):
                break
            if a.strip():
                args.append(a)
        return args

    # ---- Fuzzy matching helpers ----

    def _tokenize(self, text):
        # Lowercase, alnum word tokens
        return re.findall(r"[a-z0-9]+", text.lower())

    def _fuzzy_score(self, a, b):
        return SequenceMatcher(None, a, b).ratio()

    def _fuzzy_match_by_words(self, target, query):
        """
        n = word count of query.
        - n == 1: compare query to each single word in target (one-word basis).
        - n >= 2: compare query to every consecutive n-word window in target.
        Match if any score >= threshold.
        """
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return False
        t_tokens = self._tokenize(target)
        if not t_tokens:
            return False

        n = len(q_tokens)
        if n == 1:
            q = q_tokens[0]
            for tok in t_tokens:
                if self._fuzzy_score(tok, q) >= self.threshold:
                    return True
            return False

        q = " ".join(q_tokens)
        if len(t_tokens) < n:
            window = " ".join(t_tokens)
            return self._fuzzy_score(window, q) >= self.threshold

        for i in range(len(t_tokens) - n + 1):
            window = " ".join(t_tokens[i : i + n])
            if self._fuzzy_score(window, q) >= self.threshold:
                return True
        return False

    def _best_score_by_words(self, target, query):
        """
        Same token logic as _fuzzy_match_by_words, but return the best similarity score.
        """
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return 0.0
        t_tokens = self._tokenize(target)
        if not t_tokens:
            return 0.0

        n = len(q_tokens)
        best = 0.0
        if n == 1:
            q = q_tokens[0]
            for tok in t_tokens:
                best = max(best, self._fuzzy_score(tok, q))
            return best

        q = " ".join(q_tokens)
        if len(t_tokens) < n:
            window = " ".join(t_tokens)
            return self._fuzzy_score(window, q)

        for i in range(len(t_tokens) - n + 1):
            window = " ".join(t_tokens[i : i + n])
            best = max(best, self._fuzzy_score(window, q))
        return best

    # ---- Search pipeline ----

    def _search_lessons(self, tokens):
        """
        tokens mapping (fuzzy, case-insensitive):
          [L] -> all courses, lesson fuzzy-matches L
          [C, L] -> course fuzzy-matches C, lesson fuzzy-matches L
          [C, P, L] -> course C, part P, lesson L
          [C, P, S, L] -> course C, part P, section S, lesson L
        """
        tokens = [t.strip() for t in tokens if t.strip()]
        if not tokens:
            return []

        lesson_filter = tokens[-1]
        course_filter = part_filter = section_filter = None
        if len(tokens) >= 2:
            course_filter = tokens[0]
        if len(tokens) >= 3:
            part_filter = tokens[1]
        if len(tokens) >= 4:
            section_filter = tokens[2]

        matches = []
        for course in self.courses:
            if course_filter is not None and not self._fuzzy_match_by_words(
                course.name, course_filter
            ):
                continue
            for part in course.parts:
                if part_filter is not None and not self._fuzzy_match_by_words(
                    part.name, part_filter
                ):
                    continue
                for section in part.sections:
                    if section_filter is not None and not self._fuzzy_match_by_words(
                        section.name, section_filter
                    ):
                        continue
                    for lesson in section.lessons:
                        if self._fuzzy_match_by_words(lesson.name, lesson_filter):
                            display_name = f"{course.name} > {part.name} > {section.name} > {lesson.name}"
                            matches.append(Lesson(display_name, lesson.content))
        return matches

    def _best_match(self, tokens):
        """
        Same filters as _search_lessons, but score and pick a single best match.
        Lesson score dominates; hierarchy scores act as tie-breakers.
        """
        tokens = [t.strip() for t in tokens if t.strip()]
        if not tokens:
            return None

        lesson_filter = tokens[-1]
        course_filter = part_filter = section_filter = None
        if len(tokens) >= 2:
            course_filter = tokens[0]
        if len(tokens) >= 3:
            part_filter = tokens[1]
        if len(tokens) >= 4:
            section_filter = tokens[2]

        best = None  # (score, display_name, content)
        for course in self.courses:
            if course_filter is not None and not self._fuzzy_match_by_words(
                course.name, course_filter
            ):
                continue
            course_score = (
                self._best_score_by_words(course.name, course_filter)
                if course_filter
                else 0.0
            )

            for part in course.parts:
                if part_filter is not None and not self._fuzzy_match_by_words(
                    part.name, part_filter
                ):
                    continue
                part_score = (
                    self._best_score_by_words(part.name, part_filter)
                    if part_filter
                    else 0.0
                )

                for section in part.sections:
                    if section_filter is not None and not self._fuzzy_match_by_words(
                        section.name, section_filter
                    ):
                        continue
                    section_score = (
                        self._best_score_by_words(section.name, section_filter)
                        if section_filter
                        else 0.0
                    )

                    for lesson in section.lessons:
                        if not self._fuzzy_match_by_words(lesson.name, lesson_filter):
                            continue
                        lesson_score = self._best_score_by_words(
                            lesson.name, lesson_filter
                        )

                        # Combined score: lesson dominates; hierarchy nudges ties.
                        score = lesson_score + 0.1 * (
                            course_score + part_score + section_score
                        )

                        if (best is None) or (score > best[0]):
                            display_name = f"{course.name} > {part.name} > {section.name} > {lesson.name}"
                            best = (score, display_name, lesson.content)

        return best

    def _cat_best(self, tokens):
        best = self._best_match(tokens)
        if not best:
            print(f"No matching lessons found for -c arguments: {' | '.join(tokens)}")
            raise SystemExit(1)
        _, display_name, content = best
        BOLD_CYAN = "\033[1;36m"
        CYAN = "\033[36m"
        RESET = "\033[0m"
        underline = "-" * 79
        if not content.endswith("\n"):
            content += "\n"
        sys.stdout.write(
            f"{CYAN}{underline}{RESET}\n"
            f"{BOLD_CYAN}{display_name}{RESET}\n"
            f"{CYAN}{underline}{RESET}\n"
            f"{CYAN}{content}{RESET}"
        )
        raise SystemExit(0)

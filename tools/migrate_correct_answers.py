#!/usr/bin/env python3
"""Migrate legacy per-answer `correct` flags to question.correct_answer_id."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def migrate_quiz(quiz: dict, label: str) -> bool:
    changed = False
    for index, question in enumerate(quiz.get("questions", []), 1):
        answers = question.get("answers", [])
        legacy = [answer.get("id") for answer in answers if answer.get("correct") is True]
        selected = question.get("correct_answer_id")
        if selected is None:
            if len(legacy) != 1 or not legacy[0]:
                raise ValueError(f"{label}, вопрос {index}: найдено правильных вариантов: {len(legacy)}")
            question["correct_answer_id"] = legacy[0]
            changed = True
        elif legacy and legacy != [selected]:
            raise ValueError(f"{label}, вопрос {index}: новый и старый правильные ответы не совпадают")
        for answer in answers:
            if "correct" in answer:
                del answer["correct"]
                changed = True
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.paths:
        quiz = json.loads(path.read_text(encoding="utf-8"))
        if migrate_quiz(quiz, str(path)):
            path.write_text(json.dumps(quiz, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

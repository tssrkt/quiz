#!/usr/bin/env python3
"""Validate content and build the static site into _site/ (stdlib only)."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
QUESTION_ID_RE = re.compile(r"^question-\d{2,}$")
ANSWER_ID_RE = re.compile(r"^answer-\d{2,}$")
HTML_FILES = ("index.html", "quizzes.html", "quiz.html", "contacts.html")
COPY_DIRS = ("css", "js")


class ContentError(Exception):
    pass


def read_json(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as error:
        raise ContentError(f"{path.relative_to(ROOT)}: некорректный JSON: {error}") from None
    if not isinstance(value, dict):
        raise ContentError(f"{path.relative_to(ROOT)}: корневое значение должно быть объектом")
    return value


def require_string(data: dict, field: str, label: str, errors: list[str], allow_empty: bool = False) -> str:
    value = data.get(field)
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        errors.append(f"{label}.{field}: требуется непустая строка" if not allow_empty else f"{label}.{field}: требуется строка")
        return ""
    return value.strip()


def validate_slug(value: str, label: str, errors: list[str]) -> None:
    if value and not SLUG_RE.fullmatch(value):
        errors.append(f"{label}: допустимы строчные латинские буквы, цифры и одиночные дефисы")


def validate_local_image(value: object, prefix: str, label: str, errors: list[str]) -> None:
    if value in (None, ""):
        return
    if not isinstance(value, str):
        errors.append(f"{label}: путь должен быть строкой")
        return
    if value.startswith(("/", "\\")) or "\\" in value or ".." in Path(value).parts:
        errors.append(f"{label}: требуется безопасный относительный путь без начального /")
        return
    if not value.startswith(prefix):
        errors.append(f"{label}: путь должен начинаться с {prefix}")
        return
    candidate = (ROOT / value).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        errors.append(f"{label}: путь выходит за пределы проекта")
        return
    if not candidate.is_file():
        errors.append(f"{label}: файл не найден: {value}")


def validate_external_url(value: object, label: str, errors: list[str]) -> None:
    if value in (None, ""):
        return
    if not isinstance(value, str):
        errors.append(f"{label}: ссылка должна быть строкой")
        return
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        errors.append(f"{label}: требуется полный адрес http:// или https://")


def load_tags(data_root: Path) -> tuple[list[dict], dict[str, dict]]:
    errors: list[str] = []
    tags: list[dict] = []
    slugs: dict[str, Path] = {}
    names: dict[str, Path] = {}
    for path in sorted((data_root / "tags").glob("*.json")):
        data = read_json(path)
        label = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        name = require_string(data, "name", label, errors)
        slug = require_string(data, "slug", label, errors)
        validate_slug(slug, f"{label}.slug", errors)
        if slug and path.stem != slug:
            errors.append(f"{label}.slug: должен совпадать с именем файла «{path.stem}»")
        if slug in slugs:
            errors.append(f"{label}.slug: повторяет slug из {slugs[slug].name}")
        elif slug:
            slugs[slug] = path
        folded = name.casefold()
        if folded in names:
            errors.append(f"{label}.name: название повторяет {names[folded].name} без учёта регистра")
        elif name:
            names[folded] = path
        order = data.get("order")
        if isinstance(order, bool) or not isinstance(order, int) or order < 0:
            errors.append(f"{label}.order: требуется целое неотрицательное число")
        if not isinstance(data.get("published"), bool):
            errors.append(f"{label}.published: требуется true или false")
        tags.append(data)
    if errors:
        raise ContentError("\n".join(errors))
    return tags, {tag["slug"]: tag for tag in tags}


def load_quizzes(data_root: Path, known_tags: dict[str, dict]) -> list[dict]:
    errors: list[str] = []
    quizzes: list[dict] = []
    slugs: dict[str, Path] = {}
    for path in sorted((data_root / "quizzes").glob("*.json")):
        data = read_json(path)
        label = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        slug = require_string(data, "slug", label, errors)
        validate_slug(slug, f"{label}.slug", errors)
        if slug and path.stem != slug:
            errors.append(f"{label}.slug: должен совпадать с именем файла «{path.stem}»")
        if slug in slugs:
            errors.append(f"{label}.slug: повторяет slug из {slugs[slug].name}")
        elif slug:
            slugs[slug] = path
        for field in ("title", "short_description", "intro"):
            require_string(data, field, label, errors)
        if not isinstance(data.get("published"), bool):
            errors.append(f"{label}.published: требуется true или false")
        publication_date = require_string(data, "publication_date", label, errors)
        if publication_date:
            try:
                dt.date.fromisoformat(publication_date)
            except ValueError:
                errors.append(f"{label}.publication_date: требуется существующая дата YYYY-MM-DD")
        tags = data.get("tags")
        if not isinstance(tags, list) or not tags or any(not isinstance(tag, str) or not tag for tag in tags):
            errors.append(f"{label}.tags: требуется непустой массив slug тегов")
        else:
            for tag in tags:
                if tag not in known_tags:
                    errors.append(f"{label}.tags: неизвестный тег «{tag}»")
        validate_local_image(data.get("cover", ""), "img/covers/", f"{label}.cover", errors)
        questions = data.get("questions")
        if not isinstance(questions, list) or not questions:
            errors.append(f"{label}.questions: требуется непустой массив")
            questions = []
        question_ids: dict[str, int] = {}
        for q_index, question in enumerate(questions, 1):
            qlabel = f"{label}.questions[{q_index}]"
            if not isinstance(question, dict):
                errors.append(f"{qlabel}: требуется объект")
                continue
            question_id = require_string(question, "id", qlabel, errors)
            if question_id and not QUESTION_ID_RE.fullmatch(question_id):
                errors.append(f"{qlabel}.id: требуется формат question-N с минимум двумя цифрами")
            if question_id in question_ids:
                errors.append(
                    f"{label}: конфликтующий ID вопроса «{question_id}» в questions[{question_ids[question_id]}] и questions[{q_index}]"
                )
            elif question_id:
                question_ids[question_id] = q_index
            require_string(question, "question", qlabel, errors)
            require_string(question, "explanation", qlabel, errors)
            image = question.get("image", "")
            validate_local_image(image, "img/quiz/", f"{qlabel}.image", errors)
            if isinstance(image, str) and image:
                image_parts = Path(image).parts
                if len(image_parts) > 3 and image_parts[:2] == ("img", "quiz") and image_parts[2] != slug:
                    errors.append(f"{qlabel}.image: папка изображения должна совпадать со slug «{slug}»")
            if image and not isinstance(question.get("image_alt"), str):
                errors.append(f"{qlabel}.image_alt: для изображения требуется строка")
            validate_external_url(question.get("image_source_url", ""), f"{qlabel}.image_source_url", errors)
            answers = question.get("answers")
            if not isinstance(answers, list) or not 2 <= len(answers) <= 6:
                errors.append(f"{qlabel}.answers: требуется от 2 до 6 вариантов")
                answers = []
            answer_ids: dict[str, int] = {}
            correct_count = 0
            for a_index, answer in enumerate(answers, 1):
                alabel = f"{qlabel}.answers[{a_index}]"
                if not isinstance(answer, dict):
                    errors.append(f"{alabel}: требуется объект")
                    continue
                answer_id = require_string(answer, "id", alabel, errors)
                if answer_id and not ANSWER_ID_RE.fullmatch(answer_id):
                    errors.append(f"{alabel}.id: требуется формат answer-N с минимум двумя цифрами")
                if answer_id in answer_ids:
                    errors.append(
                        f"{label}: конфликтующий ID ответа «{answer_id}» в questions[{q_index}].answers[{answer_ids[answer_id]}] и questions[{q_index}].answers[{a_index}]"
                    )
                elif answer_id:
                    answer_ids[answer_id] = a_index
                require_string(answer, "text", alabel, errors)
                if not isinstance(answer.get("correct"), bool):
                    errors.append(f"{alabel}.correct: требуется true или false")
                elif answer["correct"]:
                    correct_count += 1
            if correct_count != 1:
                errors.append(f"{qlabel}.answers: правильным должен быть ровно один вариант, найдено {correct_count}")
        quizzes.append(data)
    if errors:
        raise ContentError("\n".join(errors))
    return [normalize_quiz(quiz) for quiz in quizzes]


def normalize_quiz(source: dict) -> dict:
    quiz = copy.deepcopy(source)
    slug = quiz["slug"]
    for q_index, question in enumerate(quiz["questions"], 1):
        image = question.get("image", "")
        if image:
            question["_source_image"] = image
            question["image"] = f"img/quiz/{slug}/{q_index:02d}{Path(image).suffix.lower()}"
    version_quiz = copy.deepcopy(quiz)
    image_hashes = []
    for question in version_quiz["questions"]:
        source_image = question.pop("_source_image", None)
        image_hashes.append(hashlib.sha256((ROOT / source_image).read_bytes()).hexdigest() if source_image else "")
    version_payload = {"quiz": version_quiz, "question_image_sha256": image_hashes}
    version_data = json.dumps(version_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    quiz["content_version"] = hashlib.sha256(version_data).hexdigest()
    return quiz


def make_catalog(tags: list[dict], quizzes: list[dict]) -> dict:
    published_tags = sorted(
        ({"slug": tag["slug"], "name": tag["name"], "order": tag["order"]} for tag in tags if tag["published"]),
        key=lambda tag: (tag["order"], tag["name"].casefold()),
    )
    published_quizzes = [
        {
            "slug": quiz["slug"],
            "title": quiz["title"],
            "published": True,
            "publication_date": quiz["publication_date"],
            "short_description": quiz["short_description"],
            "cover": quiz.get("cover", ""),
            "tags": quiz["tags"],
            "question_count": len(quiz["questions"]),
            "content_version": quiz["content_version"],
        }
        for quiz in quizzes if quiz["published"]
    ]
    return {"tags": list(published_tags), "quizzes": published_quizzes}


def build(output: Path = OUTPUT) -> dict:
    tags, known_tags = load_tags(ROOT / "data")
    quizzes = load_quizzes(ROOT / "data", known_tags)
    catalog = make_catalog(tags, quizzes)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    for filename in HTML_FILES:
        shutil.copy2(ROOT / filename, output / filename)
    for dirname in COPY_DIRS:
        shutil.copytree(ROOT / dirname, output / dirname, ignore=shutil.ignore_patterns(".gitkeep"))
    shutil.copytree(ROOT / "img" / "covers", output / "img" / "covers", ignore=shutil.ignore_patterns(".gitkeep"))
    shutil.copytree(ROOT / "data" / "tags", output / "data" / "tags")
    quiz_output = output / "data" / "quizzes"
    quiz_output.mkdir(parents=True)
    for quiz in quizzes:
        for question in quiz["questions"]:
            source_image = question.pop("_source_image", "")
            if source_image:
                destination = output / question["image"]
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / source_image, destination)
        with (quiz_output / f"{quiz['slug']}.json").open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(quiz, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    with (output / "data" / "catalog.json").open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(catalog, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return catalog


def main() -> int:
    parser = argparse.ArgumentParser(description="Проверить контент и собрать статический сайт")
    parser.add_argument("--check", action="store_true", help="только проверить данные, не создавать _site")
    args = parser.parse_args()
    try:
        tags, known_tags = load_tags(ROOT / "data")
        quizzes = load_quizzes(ROOT / "data", known_tags)
        if args.check:
            print(f"Проверка пройдена: тегов — {len(tags)}, викторин — {len(quizzes)}.")
        else:
            catalog = build()
            print(f"Сборка готова: {OUTPUT.relative_to(ROOT)}; опубликованных викторин — {len(catalog['quizzes'])}.")
        return 0
    except ContentError as error:
        print("Ошибка проверки контента:", file=sys.stderr)
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

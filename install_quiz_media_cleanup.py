#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


CLEANUP_SCRIPT = r"""#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


MEDIA_ROOTS = (
    PurePosixPath("img/covers"),
    PurePosixPath("img/quiz"),
)

IMAGE_EXTENSIONS = {
    ".avif",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".svg",
    ".webp",
}


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)


def normalize_repo_path(value: str) -> PurePosixPath | None:
    normalized = value.strip().replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.lstrip("/")

    if not normalized:
        return None

    path = PurePosixPath(normalized)
    if ".." in path.parts:
        return None

    for media_root in MEDIA_ROOTS:
        if path == media_root or media_root in path.parents:
            return path

    return None


def collect_references(repo_root: Path) -> set[PurePosixPath]:
    data_root = repo_root / "data"
    references: set[PurePosixPath] = set()
    errors: list[str] = []

    if not data_root.is_dir():
        raise FileNotFoundError(f"Не найдена папка данных: {data_root}")

    json_files = sorted(data_root.rglob("*.json"))
    if not json_files:
        raise RuntimeError(f"В {data_root} не найдено ни одного JSON-файла.")

    for json_path in json_files:
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception as error:
            errors.append(f"{json_path.relative_to(repo_root)}: {error}")
            continue

        for value in iter_strings(payload):
            media_path = normalize_repo_path(value)
            if media_path is not None:
                references.add(media_path)

    if errors:
        joined = "\n".join(f"- {item}" for item in errors)
        raise RuntimeError(
            "Очистка отменена: обнаружены повреждённые JSON-файлы.\n" + joined
        )

    return references


def collect_media_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []

    for relative_root in MEDIA_ROOTS:
        absolute_root = repo_root / Path(*relative_root.parts)
        if not absolute_root.exists():
            continue

        for path in absolute_root.rglob("*"):
            if (
                path.is_file()
                and not path.is_symlink()
                and path.suffix.lower() in IMAGE_EXTENSIONS
            ):
                files.append(path)

    return sorted(files)


def remove_empty_directories(repo_root: Path, dry_run: bool) -> list[Path]:
    removed: list[Path] = []

    for relative_root in MEDIA_ROOTS:
        absolute_root = repo_root / Path(*relative_root.parts)
        if not absolute_root.is_dir():
            continue

        directories = sorted(
            (path for path in absolute_root.rglob("*") if path.is_dir()),
            key=lambda path: len(path.parts),
            reverse=True,
        )

        for directory in directories:
            try:
                is_empty = not any(directory.iterdir())
            except OSError:
                continue

            if not is_empty:
                continue

            removed.append(directory)
            if not dry_run:
                directory.rmdir()

    return removed


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Удаляет изображения из img/covers и img/quiz, "
            "на которые не ссылаются JSON-файлы в data."
        )
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только показать, что будет удалено.",
    )
    parser.add_argument(
        "repo",
        nargs="?",
        default=".",
        help="Корень репозитория; по умолчанию текущая папка.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()
    if not (repo_root / ".git").exists():
        raise RuntimeError(f"Это не корень Git-репозитория: {repo_root}")

    references = collect_references(repo_root)
    media_files = collect_media_files(repo_root)

    unused: list[Path] = []
    missing: list[PurePosixPath] = []

    existing_relative = {
        PurePosixPath(path.relative_to(repo_root).as_posix())
        for path in media_files
    }

    for reference in sorted(references, key=str):
        if reference not in existing_relative:
            missing.append(reference)

    for file_path in media_files:
        relative = PurePosixPath(file_path.relative_to(repo_root).as_posix())
        if relative not in references:
            unused.append(file_path)

    for file_path in unused:
        print(
            ("БУДЕТ УДАЛЁН: " if args.dry_run else "УДАЛЁН: ")
            + file_path.relative_to(repo_root).as_posix()
        )
        if not args.dry_run:
            file_path.unlink()

    removed_dirs = remove_empty_directories(repo_root, args.dry_run)
    for directory in removed_dirs:
        print(
            ("БУДЕТ УДАЛЕНА ПАПКА: " if args.dry_run else "УДАЛЕНА ПАПКА: ")
            + directory.relative_to(repo_root).as_posix()
        )

    print()
    print(f"Используемых путей в JSON: {len(references)}")
    print(f"Найдено изображений: {len(media_files)}")
    print(f"Неиспользуемых изображений: {len(unused)}")

    if missing:
        print()
        print("ПРЕДУПРЕЖДЕНИЕ: в JSON есть ссылки на отсутствующие файлы:")
        for reference in missing:
            print(f"- {reference.as_posix()}")

    if args.dry_run:
        print("\nЭто был предварительный просмотр; файлы не изменены.")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        raise SystemExit(1)
"""

WORKFLOW = r"""name: Cleanup unused quiz media

on:
  push:
    branches:
      - main
    paths:
      - "data/quizzes/**/*.json"
      - "data/quizzes/*.json"
  workflow_dispatch:

permissions:
  contents: write

concurrency:
  group: cleanup-unused-quiz-media
  cancel-in-progress: false

jobs:
  cleanup:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Remove unreferenced media and commit
        shell: bash
        run: |
          set -euo pipefail

          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

          for attempt in 1 2 3; do
            echo "Cleanup attempt ${attempt}"

            git fetch origin main
            git reset --hard origin/main

            python scripts/cleanup_unused_quiz_media.py

            if git diff --quiet -- img/covers img/quiz; then
              echo "No unused media found."
              exit 0
            fi

            git add -A img/covers img/quiz
            git commit -m "Clean up unused quiz media"

            if git push origin HEAD:main; then
              exit 0
            fi

            echo "Remote changed while cleaning; retrying from the newest main."
            sleep 5
          done

          echo "Could not push cleanup after three attempts."
          exit 1
"""


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"Создан/обновлён: {path.as_posix()}")


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()

    if not (root / ".git").exists():
        raise RuntimeError(
            f"Запусти файл из корня репозитория Quiz. Не найдено: {root / '.git'}"
        )

    cleanup_path = root / "scripts" / "cleanup_unused_quiz_media.py"
    workflow_path = root / ".github" / "workflows" / "cleanup-unused-quiz-media.yml"

    write_text(cleanup_path, CLEANUP_SCRIPT)
    write_text(workflow_path, WORKFLOW)

    print("\nЗапускаю текущую очистку...")
    result = subprocess.run(
        [sys.executable, str(cleanup_path), str(root)],
        cwd=root,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Файлы автоматизации созданы, но текущая очистка завершилась ошибкой. "
            "Ничего не коммить до проверки сообщения выше."
        )

    print("\nГотово.")
    print("Проверь изменения командой: git status --short")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        raise SystemExit(1)

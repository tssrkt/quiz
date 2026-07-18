#!/usr/bin/env python3
from pathlib import Path
import sys


OLD = (
    ".sort-control{display:inline-flex;align-items:center;gap:1px;padding:2px;"
    "background:#fff;border:1px solid var(--line);border-radius:10px}"
    ".sort-control select{width:142px;min-height:36px;padding:6px 22px 6px 9px;"
    "border:0;border-radius:7px;background:#fff;color:var(--ink);font:inherit;cursor:pointer}"
    ".sort-direction{display:grid;place-items:center;min-width:36px;min-height:36px;"
    "padding:0;border:0;border-radius:7px;background:transparent;color:var(--primary-dark);"
    "font-size:1.15rem;font-weight:900;cursor:pointer}"
)

NEW = (
    ".sort-control{display:inline-flex;align-items:center;gap:0;padding:1px;"
    "background:#fff;border:1px solid var(--line);border-radius:9px}"
    ".sort-control select{width:132px;min-height:34px;padding:5px 20px 5px 8px;"
    "border:0;border-radius:7px;background:#fff;color:var(--ink);font:inherit;cursor:pointer}"
    ".sort-direction{display:grid;place-items:center;min-width:32px;min-height:32px;"
    "padding:0;border:0;border-radius:7px;background:transparent;color:var(--primary-dark);"
    "font-size:1.1rem;font-weight:900;cursor:pointer}"
)


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    css_path = root / "css" / "style.css"

    if not css_path.is_file():
        raise FileNotFoundError(f"Не найден файл: {css_path}")

    css = css_path.read_text(encoding="utf-8")

    if NEW in css:
        print("Изменение уже применено.")
        return 0

    count = css.count(OLD)
    if count != 1:
        raise RuntimeError(
            f"Ожидалось одно совпадение текущих стилей сортировки, найдено {count}. "
            "Версия style.css отличается."
        )

    css_path.write_text(css.replace(OLD, NEW, 1), encoding="utf-8", newline="\n")

    print("Готово:")
    print("- ширина select: 142px → 132px;")
    print("- кнопка стрелки: 36px → 32px;")
    print("- padding оболочки: 2px → 1px;")
    print("- gap: 1px → 0;")
    print("- размер шрифта текста не изменён.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        raise SystemExit(1)

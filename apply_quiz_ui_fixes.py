#!/usr/bin/env python3
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label}: ожидалось одно совпадение, найдено {count}. "
            "Возможно, файлы уже изменены или версия репозитория отличается."
        )
    return text.replace(old, new, 1)


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    css_path = root / "css" / "style.css"
    js_path = root / "js" / "quiz.js"

    if not css_path.is_file():
        raise FileNotFoundError(f"Не найден файл: {css_path}")
    if not js_path.is_file():
        raise FileNotFoundError(f"Не найден файл: {js_path}")

    css = css_path.read_text(encoding="utf-8")
    js = js_path.read_text(encoding="utf-8")

    css = replace_once(
        css,
        ".tag{display:inline-flex;padding:3px 11px;border-radius:999px;background:var(--mint);color:#315f51;font-size:.78rem;font-weight:700;text-decoration:none;border:1px solid transparent}.tag:hover{border-color:#74a696}",
        ".tag{display:inline-flex;padding:3px 11px;border-radius:999px;background:#f0edf8;color:var(--primary-dark);font-size:.78rem;font-weight:700;text-decoration:none;border:1px solid #cec5e4}.tag:hover{background:#e6e0f3;border-color:#aa9dce}",
        "Обычные теги",
    )

    css = replace_once(
        css,
        ".catalog-tag{display:inline-flex;align-items:center;gap:7px;min-height:31px;padding:3px 11px;border:1px solid transparent;border-radius:999px;background:var(--mint);color:#315f51;font-family:inherit;font-size:.78rem;font-weight:700;line-height:1.35;white-space:nowrap;cursor:pointer}.catalog-tag:hover{border-color:#74a696}.catalog-tag small{min-width:1.5em;color:#58766d;font-size:.72rem;font-weight:650;text-align:center}",
        ".catalog-tag{display:inline-flex;align-items:center;gap:7px;min-height:31px;padding:3px 11px;border:1px solid #cec5e4;border-radius:999px;background:#f0edf8;color:var(--primary-dark);font-family:inherit;font-size:.78rem;font-weight:700;line-height:1.35;white-space:nowrap;cursor:pointer}.catalog-tag:hover{background:#e6e0f3;border-color:#aa9dce}.catalog-tag small{min-width:1.5em;color:#71668f;font-size:.72rem;font-weight:650;text-align:center}",
        "Теги фильтра",
    )

    css = replace_once(
        css,
        ".sort-control{display:inline-flex;align-items:center;gap:3px;padding:3px;background:#fff;border:1px solid var(--line);border-radius:12px}.sort-control select{min-height:38px;padding:7px 30px 7px 10px;border:0;border-radius:8px;background:#fff;color:var(--ink);font:inherit;cursor:pointer}.sort-direction{display:grid;place-items:center;min-width:44px;min-height:44px;padding:0;border:0;border-radius:8px;background:transparent;color:var(--primary-dark);font-size:1.25rem;font-weight:900;cursor:pointer}",
        ".sort-control{display:inline-flex;align-items:center;gap:1px;padding:2px;background:#fff;border:1px solid var(--line);border-radius:10px}.sort-control select{width:142px;min-height:36px;padding:6px 22px 6px 9px;border:0;border-radius:7px;background:#fff;color:var(--ink);font:inherit;cursor:pointer}.sort-direction{display:grid;place-items:center;min-width:36px;min-height:36px;padding:0;border:0;border-radius:7px;background:transparent;color:var(--primary-dark);font-size:1.15rem;font-weight:900;cursor:pointer}",
        "Поле сортировки",
    )

    css = replace_once(
        css,
        ".result-summary{margin:14px 0 0;color:var(--primary-dark);font-size:clamp(1.35rem,4vw,2rem);font-weight:850}",
        ".result-summary{margin:14px 0 0;color:var(--ink);font-size:clamp(1.35rem,4vw,2rem);font-weight:850}",
        "Цвет результата",
    )

    js = replace_once(
        js,
        "📖📖 СБОРНИК СТАТЕЙ О ЛОШАДКАХ",
        "📖 СБОРНИК СТАТЕЙ О ЛОШАДКАХ",
        "Дублированное эмодзи",
    )

    css_path.write_text(css, encoding="utf-8", newline="\n")
    js_path.write_text(js, encoding="utf-8", newline="\n")

    print("Готово:")
    print("- уменьшено поле сортировки без изменения шрифта;")
    print("- зелёные теги заменены на светло-лавандовые с более тёмной каймой;")
    print("- удалён дубль эмодзи 📖;")
    print("- строка «Ваш результат…» сделана цветом основного текста.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        raise SystemExit(1)

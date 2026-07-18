#!/usr/bin/env python3
from pathlib import Path
import sys


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label}: ожидалось одно совпадение, найдено {count}. "
            "Возможно, изменение уже применено или версия файла отличается."
        )
    return text.replace(old, new, 1)


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    html_path = root / "contacts.html"
    css_path = root / "css" / "style.css"
    js_path = root / "js" / "common.js"

    for path in (html_path, css_path, js_path):
        if not path.is_file():
            raise FileNotFoundError(f"Не найден файл: {path}")

    html = html_path.read_text(encoding="utf-8")
    css = css_path.read_text(encoding="utf-8")
    js = js_path.read_text(encoding="utf-8")

    old_html = '''      <div class="donate-block" aria-label="Поддержать проект через ЮMoney">
        <p>Пока что на сайте находится несколько викторин, однако я планирую постепенно добавлять новые. Если вам нравится этот проект и вы желаете его поддержать, то вот ЮMoney: <span class="copy-donate" data-copy="4100116004998786" title="Нажмите, чтобы скопировать" role="button" tabindex="0">4100116004998786</span></p>
        <div class="copy-message" role="status" aria-live="polite"></div>
      </div>
      <p>Если вам интересны другие мои проекты, у вас возникли вопросы, предложения по развитию сайта или вы обнаружили ошибку в его работе, то можете связаться со мной через любой из указанных ниже сервисов. Буду рада вашим отзывам, замечаниям и предложениям.</p>
      <ul class="social-links"><li><a href="https://author.today/u/tssrkt" target="_blank" rel="noopener noreferrer">Author.Today <span class="external-mark" aria-hidden="true">↗</span></a></li><li><a href="https://t.me/tssrkt" target="_blank" rel="noopener noreferrer">Telegram <span class="external-mark" aria-hidden="true">↗</span></a></li><li><a href="https://vk.com/ada.king3d" target="_blank" rel="noopener noreferrer">ВКонтакте <span class="external-mark" aria-hidden="true">↗</span></a></li><li><a href="https://www.livelib.ru/reader/ada_king" target="_blank" rel="noopener noreferrer">LiveLib <span class="external-mark" aria-hidden="true">↗</span></a></li></ul>'''

    new_html = '''      <div class="donate-block" aria-label="Поддержать проект через ЮMoney">
        <p class="contact-text">Пока что на сайте находится несколько викторин, однако я планирую постепенно добавлять новые. Если вам нравится этот проект и вы желаете его поддержать, то вот ЮMoney: <span class="copy-donate" data-copy="4100116004998786" title="Нажмите, чтобы скопировать" role="button" tabindex="0">4100116004998786</span></p>
      </div>
      <p class="contact-text">Если вам интересны другие мои проекты, у вас возникли вопросы, предложения по развитию сайта или вы обнаружили ошибку в его работе, то можете связаться со мной через любой из указанных ниже сервисов. Буду рада вашим отзывам, замечаниям и предложениям.</p>
      <ul class="social-links"><li><a href="https://author.today/u/tssrkt" target="_blank" rel="noopener noreferrer">Author.Today <span class="external-mark" aria-hidden="true">↗</span></a></li><li><a href="https://t.me/tssrkt" target="_blank" rel="noopener noreferrer">Telegram <span class="external-mark" aria-hidden="true">↗</span></a></li><li><a href="https://vk.com/ada.king3d" target="_blank" rel="noopener noreferrer">ВКонтакте <span class="external-mark" aria-hidden="true">↗</span></a></li><li><a href="https://www.livelib.ru/reader/ada_king" target="_blank" rel="noopener noreferrer">LiveLib <span class="external-mark" aria-hidden="true">↗</span></a></li></ul>
      <div class="copy-message" role="status" aria-live="polite"></div>'''

    html = replace_once(
        html,
        old_html,
        new_html,
        "Разметка контактной страницы",
    )

    old_css = (
        ".prose{font-size:1.05rem}.prose>p{margin-block:0 26px}"
        ".donate-block{margin:-8px 0 24px}.donate-block p{margin-bottom:6px}"
        ".copy-donate{display:inline;padding:0;color:inherit;background:transparent;border:0;"
        "font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:inherit;"
        "letter-spacing:.03em;white-space:nowrap;cursor:pointer}"
        ".copy-donate:hover,.copy-donate:focus-visible{color:inherit;font-weight:800;outline:none}"
        ".copy-message{min-height:1.5em;margin-top:4px;color:var(--muted);"
        "font-size:.88rem;font-weight:700}"
        ".social-links{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));"
        "gap:12px;padding:0;list-style:none}"
    )

    new_css = (
        ".prose{font-size:1.05rem}.prose>p{margin-block:0 26px}"
        ".contact-text{font-size:calc(1.05rem + 3px)}"
        ".donate-block{margin:-8px 0 0}.donate-block .contact-text{margin:0}"
        ".prose>.contact-text{margin:0}"
        ".copy-donate{display:inline;padding:0;color:inherit;background:transparent;border:0;"
        "font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:inherit;"
        "letter-spacing:.03em;white-space:nowrap;cursor:pointer}"
        ".copy-donate:hover,.copy-donate:focus-visible{color:inherit;font-weight:800;outline:none}"
        ".copy-message:empty{display:none}"
        ".copy-message:not(:empty){min-height:1.5em;margin-top:8px;color:var(--muted);"
        "font-size:.88rem;font-weight:700;text-align:center}"
        ".social-links{display:grid;grid-template-columns:repeat(4,minmax(140px,1fr));"
        "gap:12px;padding:0 0 4px;overflow-x:auto;overscroll-behavior-x:contain;"
        "scrollbar-width:thin;list-style:none}"
    )

    css = replace_once(
        css,
        old_css,
        new_css,
        "Стили контактного текста, сообщения и кнопок",
    )

    old_mobile_css = (
        ".social-links{grid-template-columns:1fr}"
    )
    new_mobile_css = (
        ".social-links{grid-template-columns:repeat(4,minmax(140px,1fr))}"
    )

    css = replace_once(
        css,
        old_mobile_css,
        new_mobile_css,
        "Мобильное расположение социальных кнопок",
    )

    old_js = (
        "      const status = copyDonate.closest('.donate-block')?.querySelector('.copy-message');"
    )
    new_js = (
        "      const status = document.querySelector('.copy-message');"
    )

    js = replace_once(
        js,
        old_js,
        new_js,
        "Поиск сообщения о копировании",
    )

    html_path.write_text(html, encoding="utf-8", newline="\n")
    css_path.write_text(css, encoding="utf-8", newline="\n")
    js_path.write_text(js, encoding="utf-8", newline="\n")

    print("Готово:")
    print("- оба контактных абзаца увеличены на 3 px;")
    print("- пустой промежуток между абзацами убран;")
    print("- сообщение о копировании перенесено под четыре кнопки;")
    print("- четыре кнопки расположены в одну строку;")
    print("- на узких экранах строка прокручивается горизонтально.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        raise SystemExit(1)

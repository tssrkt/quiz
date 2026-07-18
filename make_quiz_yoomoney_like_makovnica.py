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

    old_html = '''      <p>Пока что на сайте находится несколько викторин, однако я планирую постепенно добавлять новые. Если вам нравится этот проект и вы желаете его поддержать, то вот ЮMoney:</p>
      <div class="copy-card"><div><span class="copy-label">ЮMoney</span><code id="yoomoney-number">4100116004998786</code></div><button class="copy-button" type="button" data-copy-target="yoomoney-number">Копировать</button><span class="copy-status" role="status" aria-live="polite"></span></div>'''

    new_html = '''      <div class="donate-block" aria-label="Поддержать проект через ЮMoney">
        <p>Пока что на сайте находится несколько викторин, однако я планирую постепенно добавлять новые. Если вам нравится этот проект и вы желаете его поддержать, то вот ЮMoney: <span class="copy-donate" data-copy="4100116004998786" title="Нажмите, чтобы скопировать" role="button" tabindex="0">4100116004998786</span></p>
        <div class="copy-message" role="status" aria-live="polite"></div>
      </div>'''

    html = replace_once(
        html,
        old_html,
        new_html,
        "Разметка ЮMoney в contacts.html",
    )

    old_css = (
        '.copy-card{display:flex;flex-wrap:wrap;align-items:center;gap:15px 22px;'
        'padding:20px 22px;margin:-8px 0 30px;background:var(--mint);border-radius:var(--radius)}'
        '.copy-card>div{display:grid}'
        '.copy-label{font-size:.72rem;font-weight:800;text-transform:uppercase;'
        'letter-spacing:.12em;color:#315f51}'
        '.copy-card code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;'
        'font-size:clamp(1rem,3vw,1.2rem);font-weight:700}'
        '.copy-button{padding:9px 17px;margin-left:auto}'
        '.copy-status{flex-basis:100%;min-height:1.5em;color:#315f51;'
        'font-size:.88rem;font-weight:700}'
    )

    new_css = (
        '.donate-block{margin:-8px 0 24px}'
        '.donate-block p{margin-bottom:6px}'
        '.copy-donate{display:inline;padding:0;color:inherit;background:transparent;border:0;'
        'font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:inherit;'
        'letter-spacing:.03em;white-space:nowrap;cursor:pointer}'
        '.copy-donate:hover,.copy-donate:focus-visible{color:inherit;font-weight:800;outline:none}'
        '.copy-message{min-height:1.5em;margin-top:4px;color:var(--muted);'
        'font-size:.88rem;font-weight:700}'
    )

    css = replace_once(
        css,
        old_css,
        new_css,
        "Стили старой карточки ЮMoney в css/style.css",
    )

    old_js = '''  const copyButton = document.querySelector('[data-copy-target]');
  if (copyButton) {
    copyButton.addEventListener('click', async () => {
      const value = document.getElementById(copyButton.dataset.copyTarget)?.textContent.trim();
      const status = copyButton.parentElement.querySelector('.copy-status');
      if (!value || !status) return;
      try {
        if (navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(value);
        else {
          const input = document.createElement('textarea'); input.value = value; input.setAttribute('readonly', ''); input.style.position = 'fixed'; input.style.opacity = '0';
          document.body.appendChild(input); input.select();
          if (!document.execCommand('copy')) throw new Error('Команда копирования недоступна');
          input.remove();
        }
        status.textContent = 'Скопировано!'; copyButton.textContent = 'Готово';
      } catch (error) { status.textContent = 'Не удалось скопировать. Выделите номер вручную.'; console.warn('[Quiz] Ошибка копирования:', error); }
      window.setTimeout(() => { status.textContent = ''; copyButton.textContent = 'Копировать'; }, 2500);
    });
  }'''

    new_js = '''  const copyDonate = document.querySelector('[data-copy]');
  if (copyDonate) {
    const activateCopy = async () => {
      const value = copyDonate.dataset.copy?.trim();
      const status = copyDonate.closest('.donate-block')?.querySelector('.copy-message');
      if (!value || !status) return;

      const showStatus = (message) => {
        status.textContent = message;
        window.setTimeout(() => { status.textContent = ''; }, 2200);
      };

      try {
        if (navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(value);
        else {
          const input = document.createElement('textarea');
          input.value = value;
          input.setAttribute('readonly', '');
          input.style.position = 'fixed';
          input.style.left = '-9999px';
          input.style.top = '-9999px';
          document.body.appendChild(input);
          input.select();
          const copied = document.execCommand('copy');
          input.remove();
          if (!copied) throw new Error('Команда копирования недоступна');
        }

        copyDonate.title = 'Скопировано!';
        showStatus('Номер ЮMoney скопирован.');
        window.setTimeout(() => { copyDonate.title = 'Нажмите, чтобы скопировать'; }, 2200);
      } catch (error) {
        showStatus('Не удалось скопировать автоматически. Выделите номер вручную.');
        console.warn('[Quiz] Ошибка копирования:', error);
      }
    };

    copyDonate.addEventListener('click', activateCopy);
    copyDonate.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        activateCopy();
      }
    });
  }'''

    js = replace_once(
        js,
        old_js,
        new_js,
        "Старая логика копирования в js/common.js",
    )

    html_path.write_text(html, encoding="utf-8", newline="\n")
    css_path.write_text(css, encoding="utf-8", newline="\n")
    js_path.write_text(js, encoding="utf-8", newline="\n")

    print("Готово:")
    print("- номер ЮMoney теперь расположен прямо в тексте;")
    print("- отдельные подпись и кнопка «Копировать» удалены;")
    print("- номер копируется кликом, Enter или пробелом;")
    print("- при наведении номер становится жирнее;")
    print("- после копирования появляется сообщение «Номер ЮMoney скопирован.»")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        raise SystemExit(1)

(function () {
  'use strict';
  const toggle = document.querySelector('.menu-toggle');
  const menu = document.querySelector('.site-nav');
  const closeMenu = (restoreFocus) => {
    if (!toggle || !menu) return;
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Открыть меню');
    menu.classList.remove('is-open');
    if (restoreFocus) toggle.focus();
  };
  if (toggle && menu) {
    toggle.addEventListener('click', () => {
      const isOpen = toggle.getAttribute('aria-expanded') === 'true';
      if (isOpen) closeMenu(false);
      else {
        toggle.setAttribute('aria-expanded', 'true');
        toggle.setAttribute('aria-label', 'Закрыть меню');
        menu.classList.add('is-open');
        menu.querySelector('a')?.focus();
      }
    });
    menu.addEventListener('click', (event) => { if (event.target.closest('a')) closeMenu(false); });
    document.addEventListener('click', (event) => { if (!menu.contains(event.target) && !toggle.contains(event.target)) closeMenu(false); });
    document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && menu.classList.contains('is-open')) closeMenu(true); });
    window.addEventListener('resize', () => { if (window.matchMedia('(min-width: 769px)').matches) closeMenu(false); });
  }
  document.querySelectorAll('[data-current-year]').forEach((item) => { item.textContent = new Date().getFullYear(); });
  const copyButton = document.querySelector('[data-copy-target]');
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
  }
})();

"""Optional real-browser scenarios; requires Python Playwright and installed Chrome."""

import json
import shutil
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / ".ui-test-profile"
BASE_URL = "http://127.0.0.1:8766"
QUIZ_URL = f"{BASE_URL}/quiz.html?quiz=horse-colors"
QUIZ = json.loads((ROOT / "_site/data/quizzes/horse-colors.json").read_text(encoding="utf-8"))
DRAFT_PATH = ROOT / "_site/data/quizzes/ui-draft.json"
BROKEN_PATH = ROOT / "_site/data/quizzes/ui-broken.json"


def chosen_id(question, correct):
    return next(answer["id"] for answer in question["answers"] if answer["correct"] is correct)


def wait_next(page, index):
    if index + 1 < len(QUIZ["questions"]):
        page.get_by_text(f"Вопрос {index + 2} из {len(QUIZ['questions'])}").wait_for(timeout=2500)
    else:
        page.get_by_text("Викторина завершена").wait_for(timeout=2500)


def start_clean(page):
    page.goto(QUIZ_URL)
    page.evaluate("localStorage.clear()")
    page.reload()
    page.get_by_role("button", name="Начать викторину").click()


def all_correct(page):
    start_clean(page)
    for index, question in enumerate(QUIZ["questions"]):
        page.locator(f'[data-answer="{chosen_id(question, True)}"]').click()
        page.get_by_text("Верно!").wait_for()
        assert page.locator(".answer-option.is-correct .answer-icon").inner_text() == "✓"
        wait_next(page, index)
    assert page.locator(".result-score").inner_text() == f"{len(QUIZ['questions'])} из {len(QUIZ['questions'])}"
    assert page.locator(".result-percent").inner_text() == "100%"
    assert page.locator(".low-result").count() == 0


def all_wrong(page):
    start_clean(page)
    for index, question in enumerate(QUIZ["questions"]):
        page.locator(f'[data-answer="{chosen_id(question, False)}"]').click()
        page.get_by_text("Неверно", exact=True).wait_for()
        assert page.locator(".answer-option.is-wrong .answer-icon").inner_text() == "×"
        assert page.locator(".answer-option.is-correct .answer-icon").inner_text() == "✓"
        feedback_text = page.locator(".answer-feedback").inner_text()
        assert question["explanation"].strip() in feedback_text, f"Вопрос {index + 1}: {feedback_text!r}"
        if index == 0:
            page.wait_for_timeout(1000)
            assert page.get_by_text(f"Вопрос 1 из {len(QUIZ['questions'])}").is_visible()
        page.locator("[data-next]").click()
        wait_next(page, index)
    assert page.locator(".result-score").inner_text() == f"0 из {len(QUIZ['questions'])}"
    assert page.locator(".result-percent").inner_text() == "0%"
    low_result = page.locator(".low-result")
    assert low_result.is_visible()
    assert "Что ж, некоторые вопросы оказались непростыми — и это отличный повод узнать больше! Если желаете разобраться в теме глубже, откройте сборник статей о лошадках, а затем попробуйте пройти викторину еще раз. Наверняка после этого результат вас приятно удивит." in low_result.inner_text()
    articles = low_result.get_by_role("link", name="📖📖 Сборник статей о лошадках")
    assert articles.get_attribute("href") == "https://author.today/work/439719"
    assert articles.get_attribute("target") == "_blank"
    assert "noopener" in articles.get_attribute("rel")
    page.evaluate("Object.defineProperty(navigator, 'share', {value: undefined, configurable: true})")
    page.locator("[data-share]").click()
    page.get_by_text("Результат скопирован.").wait_for()
    low_result.get_by_role("link", name="↻ Пройти викторину еще раз").click()
    page.get_by_role("button", name="Начать викторину").wait_for()
    saved = page.evaluate("JSON.parse(localStorage.getItem('quiz-progress:horse-colors'))")
    assert saved["current_index"] == 0
    assert saved["correct_count"] == 0
    assert saved["answers"] == {}
    assert saved["completed"] is False


def mixed_with_reload(context, page):
    start_clean(page)
    first = QUIZ["questions"][0]
    page.locator(f'[data-answer="{chosen_id(first, True)}"]').click()
    wait_next(page, 0)
    second = QUIZ["questions"][1]
    page.locator(f'[data-answer="{chosen_id(second, False)}"]').click()
    page.get_by_text("Неверно", exact=True).wait_for()
    page.locator("[data-next]").click()
    page.get_by_text(f"Вопрос 3 из {len(QUIZ['questions'])}").wait_for()
    page.close()
    page = context.new_page()
    page.goto(QUIZ_URL)
    page.get_by_role("button", name="Продолжить").click()
    page.get_by_text(f"Вопрос 3 из {len(QUIZ['questions'])}").wait_for()
    for index in range(2, len(QUIZ["questions"])):
        question = QUIZ["questions"][index]
        answer_id = chosen_id(question, index == 2)
        page.locator(f'[data-answer="{answer_id}"]').click()
        if index == 2:
            wait_next(page, index)
        else:
            page.locator("[data-next]").click()
            wait_next(page, index)
    assert page.locator(".result-score").inner_text() == f"2 из {len(QUIZ['questions'])}"
    assert page.locator(".result-percent").inner_text() == "40%"
    return page


def adaptive_checks(page):
    for width in (360, 768, 1024, 1440):
        page.set_viewport_size({"width": width, "height": 900})
        start_clean(page)
        overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        assert not overflow, f"Горизонтальное переполнение при {width}px"
        image = page.locator(".question-image img")
        if image.count():
            assert image.bounding_box()["width"] <= width
        question = QUIZ["questions"][0]
        page.locator(f'[data-answer="{chosen_id(question, False)}"]').click()
        page.get_by_text(question["explanation"]).wait_for()
        overflow = page.evaluate("document.documentElement.scrollWidth > document.documentElement.clientWidth")
        assert not overflow, f"Переполнение пояснения при {width}px"


def main():
    if PROFILE.exists():
        shutil.rmtree(PROFILE)
    server = subprocess.Popen(
        ["python", "-m", "http.server", "8766", "-d", "_site", "--bind", "127.0.0.1"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        draft = {**QUIZ, "slug": "ui-draft", "title": "Тестовый черновик", "published": False}
        DRAFT_PATH.write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")
        BROKEN_PATH.write_text('{"slug": "ui-broken",', encoding="utf-8")
        time.sleep(1)
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                str(PROFILE), headless=True,
                executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                args=["--disable-crash-reporter", "--disable-breakpad"],
            )
            javascript_errors = []
            page = context.pages[0]
            page.on("pageerror", lambda error: javascript_errors.append(str(error)))
            context.on("page", lambda opened_page: opened_page.on("pageerror", lambda error: javascript_errors.append(str(error))))
            page.goto(f"{BASE_URL}/quiz.html")
            page.get_by_text("Не указана викторина для открытия.").wait_for()
            page.goto(f"{BASE_URL}/quiz.html?quiz=unknown-quiz")
            page.get_by_text("Викторина не найдена.").wait_for()
            page.goto(f"{BASE_URL}/quiz.html?quiz=ui-broken")
            page.get_by_text("Не удалось загрузить викторину. Попробуйте позже.").wait_for()
            page.goto(f"{BASE_URL}/quiz.html?quiz=ui-draft")
            page.get_by_text("Эта викторина пока не опубликована.").wait_for()
            page.goto(f"{BASE_URL}/quiz.html?quiz=ui-draft&preview=1")
            page.get_by_text("Предварительный просмотр. Викторина не опубликована.").wait_for()
            page.get_by_role("button", name="Начать викторину").wait_for()
            all_correct(page)
            all_wrong(page)
            page = mixed_with_reload(context, page)
            adaptive_checks(page)
            assert not javascript_errors, f"Ошибки JavaScript: {javascript_errors}"
            context.close()
        print("ui_quiz_scenarios.py: 3 браузерных сценария пройдены")
    finally:
        server.terminate()
        server.wait(timeout=5)
        if PROFILE.exists():
            shutil.rmtree(PROFILE)
        DRAFT_PATH.unlink(missing_ok=True)
        BROKEN_PATH.unlink(missing_ok=True)


if __name__ == "__main__":
    main()

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import build_site


ROOT = build_site.ROOT


class BuildSiteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".content-test-", dir=ROOT)
        self.base = Path(self.temp.name)
        self.data = self.base / "data"
        shutil.copytree(ROOT / "data", self.data)

    def tearDown(self):
        self.temp.cleanup()

    def load(self):
        tags, known = build_site.load_tags(self.data)
        quizzes = build_site.load_quizzes(self.data, known)
        return tags, quizzes

    def horse(self):
        return json.loads((self.data / "quizzes" / "horse-colors.json").read_text(encoding="utf-8"))

    def write_quiz(self, quiz, name="horse-colors.json"):
        (self.data / "quizzes" / name).write_text(json.dumps(quiz, ensure_ascii=False, indent=2), encoding="utf-8")

    def assert_quiz_error(self, mutate, expected):
        quiz = self.horse()
        mutate(quiz)
        self.write_quiz(quiz)
        tags, known = build_site.load_tags(self.data)
        with self.assertRaisesRegex(build_site.ContentError, expected):
            build_site.load_quizzes(self.data, known)

    def test_auto_discovers_new_tag_and_quiz_but_excludes_draft(self):
        tag = {"name": "История", "slug": "history", "order": 40, "published": True}
        (self.data / "tags" / "history.json").write_text(json.dumps(tag, ensure_ascii=False), encoding="utf-8")
        draft = self.horse()
        draft.update({"slug": "history-draft", "title": "Черновик", "published": False, "tags": ["history"]})
        self.write_quiz(draft, "history-draft.json")
        tags, quizzes = self.load()
        catalog = build_site.make_catalog(tags, quizzes)
        self.assertIn("history", {item["slug"] for item in catalog["tags"]})
        self.assertNotIn("history-draft", {item["slug"] for item in catalog["quizzes"]})
        draft["published"] = True
        self.write_quiz(draft, "history-draft.json")
        tags, quizzes = self.load()
        published = {item["slug"]: item for item in build_site.make_catalog(tags, quizzes)["quizzes"]}
        self.assertEqual(published["history-draft"]["question_count"], 4)

    def test_no_correct_answer(self):
        self.assert_quiz_error(lambda quiz: [answer.update(correct=False) for answer in quiz["questions"][0]["answers"]], "ровно один вариант")

    def test_two_correct_answers(self):
        self.assert_quiz_error(lambda quiz: quiz["questions"][0]["answers"][1].update(correct=True), "ровно один вариант")

    def test_duplicate_question_id(self):
        self.assert_quiz_error(lambda quiz: quiz["questions"][1].update(id=quiz["questions"][0]["id"]), "повторяющийся идентификатор")

    def test_duplicate_answer_id(self):
        self.assert_quiz_error(lambda quiz: quiz["questions"][0]["answers"][1].update(id=quiz["questions"][0]["answers"][0]["id"]), "повторяющийся идентификатор")

    def test_unknown_tag(self):
        self.assert_quiz_error(lambda quiz: quiz.update(tags=["missing-tag"]), "неизвестный тег")

    def test_missing_image(self):
        self.assert_quiz_error(lambda quiz: quiz["questions"][0].update(image="img/quiz/missing.webp"), "файл не найден")

    def test_question_with_and_without_image(self):
        _, quizzes = self.load()
        questions = quizzes[0]["questions"]
        self.assertTrue(any(question["image"] for question in questions))
        self.assertTrue(any(not question["image"] for question in questions))


if __name__ == "__main__":
    unittest.main(verbosity=2)

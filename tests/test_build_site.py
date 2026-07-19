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
        quiz = json.loads((ROOT / "data" / "quizzes" / "horse-colors.json").read_text(encoding="utf-8"))
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
        for question in draft["questions"]:
            question["image"] = ""
        self.write_quiz(draft, "history-draft.json")
        tags, quizzes = self.load()
        catalog = build_site.make_catalog(tags, quizzes)
        self.assertIn("history", {item["slug"] for item in catalog["tags"]})
        self.assertNotIn("history-draft", {item["slug"] for item in catalog["quizzes"]})
        draft["published"] = True
        self.write_quiz(draft, "history-draft.json")
        tags, quizzes = self.load()
        published = {item["slug"]: item for item in build_site.make_catalog(tags, quizzes)["quizzes"]}
        self.assertEqual(published["history-draft"]["question_count"], len(draft["questions"]))

    def test_no_correct_answer(self):
        self.assert_quiz_error(lambda quiz: [answer.update(correct=False) for answer in quiz["questions"][0]["answers"]], "ровно один вариант")

    def test_two_correct_answers(self):
        self.assert_quiz_error(lambda quiz: quiz["questions"][0]["answers"][0].update(correct=True), "ровно один вариант")

    def test_invalid_and_duplicate_ids_are_rejected(self):
        self.assert_quiz_error(lambda quiz: quiz["questions"][0].update(id="manual"), "формат question-N")
        self.assert_quiz_error(lambda quiz: quiz["questions"][0]["answers"][0].update(id="manual"), "формат answer-N")
        self.assert_quiz_error(lambda quiz: quiz["questions"][1].update(id="question-01"), "конфликтующий ID вопроса «question-01»")
        self.assert_quiz_error(lambda quiz: quiz["questions"][0]["answers"][1].update(id="answer-01"), "конфликтующий ID ответа «answer-01»")

    def test_generates_stable_ids_and_content_version(self):
        _, quizzes = self.load()
        horse = quizzes[0]
        self.assertEqual(horse["questions"][0]["id"], "question-01")
        self.assertEqual(horse["questions"][4]["id"], "question-05")
        self.assertEqual([answer["id"] for answer in horse["questions"][0]["answers"]], ["answer-01", "answer-02", "answer-03", "answer-04"])
        self.assertRegex(horse["content_version"], r"^[0-9a-f]{64}$")

        changed = self.horse()
        changed["questions"][3]["question"] += " Изменено"
        self.write_quiz(changed)
        _, changed_quizzes = self.load()
        self.assertNotEqual(horse["content_version"], changed_quizzes[0]["content_version"])

        image_changed = self.horse()
        replacement = self.base / "replacement.webp"
        replacement.write_bytes(b"replacement image bytes")
        image_changed["questions"][0]["image"] = replacement.relative_to(ROOT).as_posix()
        self.assertNotEqual(horse["content_version"], build_site.normalize_quiz(image_changed)["content_version"])

        changed = self.horse()
        changed["questions"].append(copy.deepcopy(changed["questions"][-1]))
        changed["questions"][-1]["id"] = f"question-{len(changed['questions']):02d}"
        changed["questions"][-1]["question"] = "Новый тестовый вопрос?"
        self.write_quiz(changed)
        _, changed_quizzes = self.load()
        self.assertEqual(len(changed_quizzes[0]["questions"]), len(horse["questions"]) + 1)
        self.assertNotEqual(horse["content_version"], changed_quizzes[0]["content_version"])

        changed = self.horse()
        changed["questions"][0]["answers"][0]["text"] += "!"
        changed["questions"][0]["explanation"] += " Изменено"
        self.write_quiz(changed)
        _, changed_quizzes = self.load()
        self.assertNotEqual(horse["content_version"], changed_quizzes[0]["content_version"])

    def test_build_does_not_modify_source_and_writes_normalized_quiz(self):
        source = ROOT / "data" / "quizzes" / "horse-colors.json"
        before = source.read_bytes()
        output = self.base / "site"
        catalog = build_site.build(output)
        self.assertEqual(source.read_bytes(), before)
        built = json.loads((output / "data" / "quizzes" / "horse-colors.json").read_text(encoding="utf-8"))
        source_quiz = json.loads(source.read_text(encoding="utf-8"))
        self.assertEqual(len(built["questions"]), len(source_quiz["questions"]))
        self.assertEqual(catalog["quizzes"][0]["question_count"], len(source_quiz["questions"]))
        self.assertEqual(catalog["quizzes"][0]["difficulty"], "low")
        self.assertEqual(catalog["quizzes"][0]["content_version"], built["content_version"])
        self.assertEqual(
            [question["id"] for question in built["questions"]],
            [question["id"] for question in source_quiz["questions"]],
        )
        self.assertEqual(
            [[answer["id"] for answer in question["answers"]] for question in built["questions"]],
            [[answer["id"] for answer in question["answers"]] for question in source_quiz["questions"]],
        )
        self.assertEqual(sorted(path.name for path in (output / "img" / "quiz" / "horse-colors").iterdir()), [f"{index:02d}.webp" for index in range(1, len(source_quiz["questions"]) + 1)])

    def test_unknown_tag(self):
        self.assert_quiz_error(lambda quiz: quiz.update(tags=["missing-tag"]), "неизвестный тег")

    def test_difficulty_is_required_and_restricted(self):
        self.assert_quiz_error(lambda quiz: quiz.pop("difficulty"), "difficulty: требуется одно из значений")
        self.assert_quiz_error(lambda quiz: quiz.update(difficulty="expert"), "difficulty: требуется одно из значений")

    def test_missing_image(self):
        self.assert_quiz_error(lambda quiz: quiz["questions"][0].update(image="img/quiz/missing.webp"), "файл не найден")

    def test_image_without_image_alt_is_valid(self):
        quiz = self.horse()
        quiz["questions"][0].pop("image_alt", None)
        self.write_quiz(quiz)
        _, quizzes = self.load()
        self.assertNotIn("image_alt", quizzes[0]["questions"][0])

    def test_image_alt_is_rejected_only_when_present_and_not_a_string(self):
        self.assert_quiz_error(
            lambda quiz: quiz["questions"][0].update(image_alt=None),
            "image_alt:",
        )

    def test_ten_question_build_publishes_every_question_and_image(self):
        source = self.horse()
        self.assertEqual(len(source["questions"]), 10)
        output = self.base / "ten-question-site"
        catalog = build_site.build(output)
        horse = next(item for item in catalog["quizzes"] if item["slug"] == "horse-colors")
        published = json.loads((output / "data" / "quizzes" / "horse-colors.json").read_text(encoding="utf-8"))
        self.assertEqual(horse["question_count"], 10)
        self.assertEqual(len(published["questions"]), 10)
        self.assertEqual(
            sorted(path.name for path in (output / "img" / "quiz" / "horse-colors").iterdir()),
            [f"{index:02d}.webp" for index in range(1, 11)],
        )

    def test_question_images_are_isolated_by_quiz_slug(self):
        _, quizzes = self.load()
        self.assertTrue(all(question["image"].startswith("img/quiz/horse-colors/") for question in quizzes[0]["questions"]))

        other = self.horse()
        other["slug"] = "other-quiz"
        normalized = build_site.normalize_quiz(other)
        self.assertTrue(all(question["image"].startswith("img/quiz/other-quiz/") for question in normalized["questions"]))
        self.assertEqual(normalized["questions"][0]["image"], "img/quiz/other-quiz/01.webp")

    def test_rejects_image_folder_owned_by_another_quiz(self):
        quiz = self.horse()
        quiz["slug"] = "other-quiz"
        self.write_quiz(quiz, "other-quiz.json")
        tags, known = build_site.load_tags(self.data)
        with self.assertRaisesRegex(build_site.ContentError, "папка изображения должна совпадать"):
            build_site.load_quizzes(self.data, known)


if __name__ == "__main__":
    unittest.main(verbosity=2)

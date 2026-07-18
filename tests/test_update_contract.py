import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class UpdateContractTests(unittest.TestCase):
    def test_current_quiz_has_five_persisted_stable_ids(self):
        quiz = json.loads((ROOT / "data" / "quizzes" / "horse-colors.json").read_text(encoding="utf-8"))
        self.assertEqual(len(quiz["questions"]), 5)
        self.assertEqual([question["id"] for question in quiz["questions"]], [f"question-{index:02d}" for index in range(1, 6)])
        self.assertTrue(all([answer["id"] for answer in question["answers"]] == [f"answer-{index:02d}" for index in range(1, 5)] for question in quiz["questions"]))
        self.assertEqual(
            [question["image"] for question in quiz["questions"]],
            [f"img/quiz/horse-colors/{index:02d}.webp" for index in range(1, 6)],
        )

    def test_cms_schema_preserves_hidden_ids_and_merge(self):
        schema = (ROOT / ".pages.yml").read_text(encoding="utf-8")
        self.assertNotIn("Уникальный идентификатор", schema)
        self.assertNotIn("{id}", schema)
        self.assertEqual(len(re.findall(r"(?m)^\s+- name: id\s*$", schema)), 2)
        hidden_id = r"- name: id\s+type: string\s+hidden: true\s+required: false"
        self.assertEqual(len(re.findall(hidden_id, schema)), 2)
        self.assertRegex(schema, r"settings:\s+content:\s+merge: true")
        self.assertIn('summary: "{question}"', schema)
        self.assertIn('summary: "{text}"', schema)

    def test_json_and_question_images_are_cache_busted(self):
        catalog_js = (ROOT / "js" / "quizzes.js").read_text(encoding="utf-8")
        quiz_js = (ROOT / "js" / "quiz.js").read_text(encoding="utf-8")
        self.assertIn("{ cache: 'no-store' }", catalog_js)
        self.assertGreaterEqual(quiz_js.count("{ cache: 'no-store' }"), 2)
        self.assertIn("contentVersion", quiz_js)
        self.assertIn("core.versionedUrl(question.image, quiz.content_version)", quiz_js)
        self.assertNotRegex(quiz_js, r"fetch\(`data/quizzes/\$\{encodeURIComponent\(slug\)\}\.json`\)")

    def test_image_css_uses_intrinsic_ratio_and_800_pixel_cap(self):
        css = (ROOT / "css" / "style.css").read_text(encoding="utf-8")
        self.assertIn(".question-image{width:800px;max-width:100%;margin:0 auto 25px}", css)
        self.assertIn(".question-image img{width:800px;max-width:100%;height:auto", css)
        question_rule = re.search(r"\.question-image img\{([^}]+)\}", css).group(1)
        self.assertNotIn("object-fit:cover", question_rule)
        self.assertNotIn("max-height", question_rule)

    def test_wide_question_layout_and_no_image_fallback(self):
        css = (ROOT / "css" / "style.css").read_text(encoding="utf-8")
        quiz_js = (ROOT / "js" / "quiz.js").read_text(encoding="utf-8")
        self.assertIn(".content-narrow.quiz-layout-wide{width:min(100% - 32px,1400px)}", css)
        self.assertIn("grid-template-columns:800px 500px", css)
        self.assertIn("@media(min-width:1432px)", css)
        self.assertIn("const withImage = Boolean(question.image);", quiz_js)
        self.assertIn("setWideLayout(withImage);", quiz_js)
        self.assertIn("question-card question-card--with-image", quiz_js)
        self.assertIn(": `<section class=\"question-card\">${questionContent}</section>`", quiz_js)


if __name__ == "__main__":
    unittest.main(verbosity=2)

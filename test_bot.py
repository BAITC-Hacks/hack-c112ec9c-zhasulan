import tempfile
import unittest
from pathlib import Path

from bot import find_answer, load_faq


class FAQBotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = load_faq()

    def test_finds_all_five_topics(self):
        cases = {
            "Сколько это длится?": "30–60 минут",
            "Можно участвовать одному без тиммейтов?": "самостоятельно",
            "Какое направление у задания?": "LLM-приложения",
            "Куда загрузить репозиторий?": "README",
            "Что можно выиграть, есть награды?": "призов",
        }
        for question, expected in cases.items():
            with self.subTest(question=question):
                self.assertIn(expected, find_answer(question, self.items))

    def test_unknown_question(self):
        self.assertEqual("не знаю", find_answer("Какая погода на Марсе?", self.items))

    def test_rejects_invalid_faq(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "faq.txt"
            path.write_text("Вопрос: Только вопрос", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_faq(path)


if __name__ == "__main__":
    unittest.main()

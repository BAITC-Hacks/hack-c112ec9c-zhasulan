#!/usr/bin/env python3
"""Простой терминальный FAQ-бот без LLM и внешних зависимостей."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path


FAQ_PATH = Path(__file__).with_name("faq.txt")
MIN_SCORE = 0.34

STOP_WORDS = {
    "а", "без", "бы", "в", "во", "вы", "где", "да", "для", "до", "же",
    "за", "и", "из", "или", "к", "как", "ли", "мне", "мы", "на", "не",
    "о", "об", "от", "по", "про", "с", "со", "то", "у", "что", "это",
    "я", "the", "a", "an", "is", "are", "of", "to", "for", "in", "on",
}

ALIASES = {
    "когда": "время", "долго": "время", "длится": "время",
    "продолжительность": "время", "срок": "время", "сроки": "время",
    "дедлайн": "время", "тим": "команда", "тиммейты": "команда",
    "тиммейтов": "команда", "участники": "команда", "участников": "команда",
    "человек": "команда", "направление": "трек", "категория": "трек",
    "отправить": "сдача", "отправлять": "сдача", "загрузить": "сдача",
    "загружать": "сдача", "репозиторий": "сдача", "решение": "сдача",
    "награда": "призы", "награды": "призы", "подарки": "призы",
    "выиграть": "призы",
}


@dataclass(frozen=True)
class FAQItem:
    question: str
    keywords: frozenset[str]
    answer: str


def normalize_words(text: str) -> set[str]:
    """Возвращает значимые слова в нижнем регистре, включая алиасы."""
    raw_words = re.findall(r"[a-zа-яё0-9-]+", text.lower())
    words = {word for word in raw_words if len(word) > 1 and word not in STOP_WORDS}
    words.update(ALIASES[word] for word in tuple(words) if word in ALIASES)
    return words


def load_faq(path: Path = FAQ_PATH) -> list[FAQItem]:
    """Читает блоки Вопрос/Ключевые слова/Ответ из faq.txt."""
    if not path.exists():
        raise FileNotFoundError(f"Файл с вопросами не найден: {path}")

    items: list[FAQItem] = []
    text = path.read_text(encoding="utf-8")
    for number, block in enumerate(re.split(r"\n\s*---\s*\n", text), 1):
        fields: dict[str, str] = {}
        for line in block.splitlines():
            if ":" not in line:
                continue
            name, value = line.split(":", 1)
            fields[name.strip().lower()] = value.strip()

        question = fields.get("вопрос", "")
        answer = fields.get("ответ", "")
        keyword_text = fields.get("ключевые слова", "")
        if not question or not answer:
            raise ValueError(f"Ошибка в блоке {number}: нужны поля «Вопрос» и «Ответ»")
        keywords = normalize_words(f"{question} {keyword_text}")
        items.append(FAQItem(question, frozenset(keywords), answer))

    if not items:
        raise ValueError("В faq.txt нет ни одной пары вопрос–ответ")
    return items


def similarity(query_words: set[str], keywords: frozenset[str]) -> float:
    """Оценивает совпадение точных и слегка опечатанных ключевых слов."""
    if not query_words:
        return 0.0

    exact = query_words & keywords
    unmatched = query_words - exact
    fuzzy_hits = 0
    for word in unmatched:
        if len(word) < 4:
            continue
        if any(SequenceMatcher(None, word, keyword).ratio() >= 0.82 for keyword in keywords):
            fuzzy_hits += 1

    hits = len(exact) + 0.75 * fuzzy_hits
    return hits / max(1, min(len(query_words), 3))


def find_answer(query: str, items: list[FAQItem]) -> str:
    query_words = normalize_words(query)
    scored = [(similarity(query_words, item.keywords), item) for item in items]
    score, best_item = max(scored, key=lambda pair: pair[0])
    return best_item.answer if score >= MIN_SCORE else "не знаю"


def main() -> int:
    try:
        items = load_faq()
    except (OSError, ValueError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1

    print("FAQ-бот репетиции. Задайте вопрос (для выхода: выход).")
    while True:
        try:
            query = input("Вы: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nДо встречи!")
            return 0

        if query.lower() in {"выход", "exit", "quit"}:
            print("До встречи!")
            return 0
        if not query:
            continue
        print(f"Бот: {find_answer(query, items)}")


if __name__ == "__main__":
    raise SystemExit(main())

# News Digest (Python)

Программа для автоматической генерации еженедельного новостного дайджеста.

---

## Установка

1. Создай виртуальное окружение:
python3 -m venv venv

2. Активируй окружение:
source venv/bin/activate

3. Установи необходимые библиотеки:
python3 -m pip install feedparser python-dateutil beautifulsoup4 colorama g4f

---

## Запуск

Обычный запуск:
python3 news_digest.py --days 7 --limit 7

Запуск с пересказом через g4f:
python3 news_digest.py --days 7 --limit 7 --use-g4f

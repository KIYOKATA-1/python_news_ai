import feedparser
import hashlib
import json
import re
import os
from datetime import datetime, timedelta, timezone
from dateutil import parser as dtparser
from bs4 import BeautifulSoup
from colorama import init, Fore, Style

init(autoreset=True)  

FEEDS = {
    "Маркетинг": [
        ("Marketing Dive", "https://www.marketingdive.com/feeds/news/"),
        ("HubSpot Blog", "https://blog.hubspot.com/marketing/rss.xml"),
    ],
    "Технологии": [
        ("TechCrunch", "http://feeds.feedburner.com/Techcrunch/"),
        ("The Verge", "https://www.theverge.com/rss/index.xml"),
    ],
    "Реклама": [
        ("Adweek", "https://www.adweek.com/feed/"),
        ("Campaign US", "https://www.campaignlive.com/us/rss"),
    ],
    "Искусственный интеллект": [
        ("VentureBeat – AI", "https://venturebeat.com/category/ai/feed/"),
        ("The Decoder", "https://the-decoder.com/feed/"),
    ],
    "Социальные сети": [
        ("Social Media Today", "https://www.socialmediatoday.com/.rss/full/"),
        ("Mashable – Social Media", "https://mashable.com/feeds/social-media/"),
    ],
}


def strip_html(html: str) -> str:
    """Удаляет HTML-теги и пробелы"""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return re.sub(r"\s+", " ", soup.get_text(separator=" ", strip=True)).strip()


def parse_datetime(dt_str: str):
    """Парсит дату"""
    if not dt_str:
        return None
    try:
        dt = dtparser.parse(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except Exception:
        return None


def summarize_naive(text: str, max_sentences: int = 2, max_chars: int = 300) -> str:
    """Короткое описание"""
    if not text:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    summary = " ".join(sentences[:max_sentences])
    if len(summary) > max_chars:
        summary = summary[: max_chars - 1].rstrip() + "..."
    return summary


def summarize_with_g4f(text: str) -> str:
    """Краткий пересказ через g4f"""
    try:
        import g4f
    except Exception:
        return summarize_naive(text)

    try:
        response = g4f.ChatCompletion.create(
            model=g4f.models.gpt_4,
            messages=[
                {"role": "system", "content": "Ты — ИИ-журналист. Пиши кратко, нейтрально, без рекламы."},
                {"role": "user", "content": f"Перескажи нейтрально и коротко: {text}"},
            ],
            stream=False,
        )
        return str(response).strip()
    except Exception:
        return summarize_naive(text)


def fetch_news(days: int = 7, limit: int = 7, use_g4f: bool = False):
    """Загрузка новостей"""
    all_news = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    for category, feeds in FEEDS.items():
        for source_name, url in feeds:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = strip_html(entry.get("title", ""))
                if not title:
                    continue

                desc = strip_html(entry.get("summary", "") or entry.get("description", ""))
                date_str = entry.get("published", "") or entry.get("updated", "")
                dt = parse_datetime(date_str)

                if dt and dt < cutoff:
                    continue

                summary = summarize_with_g4f(desc) if use_g4f else summarize_naive(desc)

                all_news.append(
                    {
                        "title": title,
                        "summary": summary,
                        "date": dt.isoformat() if dt else "unknown",
                        "source": source_name,
                        "link": entry.get("link", ""),
                        "category": category,
                    }
                )

    seen = set()
    unique = []
    for n in all_news:
        key = hashlib.sha256((n["title"] + n["source"]).encode()).hexdigest()
        if key not in seen:
            seen.add(key)
            unique.append(n)

    unique.sort(key=lambda x: x.get("date", ""), reverse=True)
    return unique[:limit]


def print_news(news):
    """Аккуратный и читаемый вывод"""
    print("\n" + "=" * 90)
    print(" ЕЖЕНЕДЕЛЬНАЯ ПОДБОРКА НОВОСТЕЙ ".center(90, "="))
    print("=" * 90 + "\n")

    for i, n in enumerate(news, 1):
        print(Fore.YELLOW + f"< {i}. {n['title']} >")
        print(Fore.CYAN + "-" * 90)
        print(Fore.WHITE + f"{n['summary']}\n")
        print(Fore.MAGENTA + f"Дата: {n['date']}")
        print(Fore.BLUE + f"Источник: {n['source']}")
        print(Fore.GREEN + f"Ссылка: {n['link']}\n")
        print(Fore.CYAN + "<" + "=" * 88 + ">\n")

    print(Fore.GREEN + "Конец подборки.")
    print("=" * 90 + "\n")


def save_to_md(news):
    lines = [
        f"# Еженедельная подборка новостей ({datetime.now().strftime('%d.%m.%Y %H:%M')})\n"
    ]
    for n in news:
        lines.append(f"### {n['title']}\n")
        lines.append(f"{n['summary']}\n")
        lines.append(f"_{n['date']} • {n['source']}_  \n[{n['link']}]({n['link']})\n")
    md = "\n".join(lines)

    output_path = os.path.join(os.getcwd(), "digest.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(Fore.GREEN + f"Файл digest.md сохранён в: {output_path}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Еженедельный новостной дайджест")
    parser.add_argument("--days", type=int, default=7, help="За сколько дней брать новости")
    parser.add_argument("--limit", type=int, default=7, help="Сколько новостей вывести")
    parser.add_argument("--use-g4f", action="store_true", help="Использовать g4f для пересказа")

    args = parser.parse_args()

    print(Fore.CYAN + "\n< Сбор новостей... пожалуйста, подожди несколько секунд >\n")

    news = fetch_news(days=args.days, limit=args.limit, use_g4f=args.use_g4f)
    if not news:
        print(Fore.RED + "Не удалось получить новости. Попробуйте увеличить период (--days 14).")
    else:
        print_news(news)
        save_to_md(news)

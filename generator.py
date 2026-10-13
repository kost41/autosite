import os
import random
import re
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

import requests

API_KEY = os.environ.get("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("GROQ_API_KEY not set")

API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Список моделей на случай если одна не работает
MODELS = [
    "qwen/qwen3.6-27b",
    "openai/gpt-oss-120b",
]

TOPICS = [
    "как выбрать надёжного партнёра для интернет-магазина",
    "преимущества дропшиппинга в 2025 году",
    "как начать онлайн-бизнес с нуля",
    "ошибки начинающих предпринимателей",
    "автоматизация бизнес-процессов для экономии времени",
    "где брать трафик на сайт бесплатно",
    "как увеличить продажи через email-рассылки",
    "зачем нужен сайт компании и как он помогает в продажах",
    "как защитить свой бизнес от кибератак",
    "искусственный интеллект в помощь малому бизнесу",
    "построение команды удалённых сотрудников",
    "упаковка услуг: как продавать дороже",
]

def slugify(title: str) -> str:
    s = title.lower()
    s = re.sub(r'[^a-zа-яё0-9\s-]', '', s)
    s = re.sub(r'\s+', '-', s).strip('-')
    return s[:80]

def generate_content(topic: str) -> str:
    sys_msg = (
        "Ты — профессиональный копирайтер. Напиши SEO-оптимизированный пост на русском языке. "
        "В ответе верни ТОЛЬКО JSON в формате: {\"title\": \"...\", \"content\": \"...\", \"tags\": [\"...\"]}. "
        "Контент — размеченный HTML (заголовки h2, абзацы p, списки ul/li). Никакого Markdown."
    )
    usr_msg = f"Напиши пост на тему: «{topic}». Минимум 800 слов."

    payload = {
        "model": MODELS[0],
        "messages": [
            {"role": "system", "content": sys_msg},
            {"role": "user", "content": usr_msg},
        ],
        "temperature": 0.7,
        "max_tokens": 4096,
    }

    for model in MODELS:
        try:
            payload["model"] = model
            response = requests.post(API_URL, headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            raw = data["choices"][0]["message"]["content"]
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not match:
                print(f"Model {model}: no JSON found in response")
                continue
            parsed = json.loads(match.group(0))
            if parsed.get("content"):
                print(f"Success with model: {model}")
                return parsed["content"]
        except Exception as e:
            print(f"Model {model} failed: {e}")
            try:
                print("Response body:", response.text[:500])
            except Exception:
                pass
            continue

    raise RuntimeError("All models failed")

def generate_title_from_content(content: str) -> str:
    sys_msg = "Придумай короткий цепляющий заголовок для текста (до 60 символов). Верни ТОЛЬКО заголовок, без кавычек."
    usr_msg = content[:2000]

    for model in MODELS:
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": usr_msg},
                ],
                "temperature": 0.7,
                "max_tokens": 60,
            }
            response = requests.post(API_URL, headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            title = data["choices"][0]["message"]["content"].strip().strip('"\'')
            if title:
                return title
        except Exception as e:
            print(f"Title generation with {model} failed: {e}")
            continue

    return "Новый пост"

def create_post():
    today = datetime.now().strftime("%Y-%m-%d")
    existing = [f.stem for f in Path(".").glob("20*.html")]
    if any(today in e for e in existing):
        print(f"Post for {today} already exists. Skipping.")
        return False

    topic = random.choice(TOPICS)
    print(f"Selected topic: {topic}")

    print("Generating content...")
    content = generate_content(topic)
    print("Generating title...")
    title = generate_title_from_content(content)

    slug = slugify(title)
    date_str = datetime.now().strftime("%Y-%m-%d-%H%M")
    filename = f"{date_str}-{slug}.html"

    post_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>
    <header>
        <h1>{title}</h1>
        <p class="meta">Опубликовано: {datetime.now().strftime('%d.%m.%Y')}</p>
    </header>
    <main>
        {content}
    </main>
    <footer>
        <p><a href="index.html">← На главную</a></p>
    </footer>
</body>
</html>"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(post_html)
    print(f"Created post: {filename}")
    update_index(filename, title, datetime.now().strftime('%d.%m.%Y'))
    return True

def update_index(post_filename, title, date_str):
    posts = []
    for f in sorted(Path(".").glob("20*.html"), reverse=True):
        posts.append((f.name, f.stem))

    list_items = "".join([
        f'<li><a href="{fn}">{title}</a> — {date_str}</li>\n'
        for fn, title in posts
    ])

    index_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoSite</title>
    <link rel="stylesheet" href="assets/style.css">
</head>
<body>
    <h1>AutoSite</h1>
    <p>Последние посты:</p>
    <ul>
        {list_items}
    </ul>
</body>
</html>"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print("Updated index.html")

if __name__ == "__main__":
    create_post()

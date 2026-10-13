import os
import re
import random
import datetime
import requests
import feedparser
from html import escape
from slugify import slugify

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-70b-versatile"

RSS_FEEDS = [
    "https://lenta.ru/rss/news",
    "https://www.rbc.ru/logic/rss/interesting.rss",
    "https://news.yandex.ru/index.rss"  # может не работать, тогда удали
]

def fetch_trend_topic():
    """Берём случайную новость из RSS"""
    for feed_url in random.sample(RSS_FEEDS, len(RSS_FEEDS)):
        try:
            d = feedparser.parse(feed_url)
            if d.entries:
                entry = random.choice(d.entries[:10])
                return entry.title, entry.get("summary", "")
        except Exception as e:
            print(f"RSS fail {feed_url}: {e}")
            continue
    # Fallback если RSS не работают
    return "Что нового в мире технологий", "обзор актуальных событий"

def humanize_text(text):
    """Добавляем человечности: случайные вставки, убираем перфекционизм"""
    # Меняем местами некоторые предложения (если много)
    sentences = text.split(". ")
    if len(sentences) > 4:
        # Меняем местами 2 случайных предложения в середине
        idx = random.randint(1, len(sentences)-3)
        sentences[idx], sentences[idx+1] = sentences[idx+1], sentences[idx]
    
    text = ". ".join(sentences)
    
    # Добавляем случайную «человеческую» вставку
    intros = [
        "Честно говоря, ",
        "Я тут подумал — ",
        "Знаете, ",
        "По моему мнению, ",
        "Короче, ",
        "Ну и ну, "
    ]
    if random.random() > 0.5:
        text = random.choice(intros) + text[0].lower() + text[1:]
    
    # Заменяем идеальные формулировки на просторечные
    replacements = {
        "Однако": "Но",
        "Тем не менее": "Всё же",
        "В связи с этим": "Поэтому",
        "Необходимо отметить": "Кстати",
        "Следует отметить": "Важно сказать",
        "в связи с чем": "так что",
        "осуществлять": "делать",
        "является": "это",
        "в настоящее время": "сейчас"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Добавляем опечатку (одну!) — типичный приём «человечности»
    if random.random() > 0.7:
        common_typos = [("привет", "привет"), ("вообще", "вообще"), ("скажем", "скажем")]
        # Просто убираем одну случайную запятую где-то
        text = text.replace(", ", " ", 1)
    
    return text

def generate_article(title, summary):
    """Генерируем статью через Llama с человеческим промптом"""
    
    system_prompt = """Ты — обычный парень из интернета, пишешь пост в свой личный блог. 
Ты НЕ журналист. Ты пишешь простым языком, как рассказываешь другу за пивом. 
Используй короткие абзацы (2-3 предложения). 
Иногда допускай лёгкие разговорные обороты («блин», «короче», «прикол в том», «не парься»).
Добавь личное мнение и сомнения. Не пиши идеально — это выглядит как робот.
НЕ используй списки с маркерами. НЕ пиши вступление «В этой статье мы рассмотрим...». 
Сразу начинай с сути или с личной истории.
Не используй Markdown, только чистый текст с абзацами."""

    user_prompt = f"""Вот заголовок новости: "{title}"
Краткое содержание: {summary}

Напиши развёрнутый пост для блога (800-1000 слов) на эту тему. 
Представь, что ты сам столкнулся с этой ситуацией и рассказываешь, что думаешь.
Добавь вымышленную личную историю в начале (например, «помню, у моего друга было такое...»).
Заверши текст неопределённым выводом, типа «посмотрим, что будет дальше».
НЕ используй заголовки внутри текста. Только текст."""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.9,  # Высокая температура = менее предсказуемо
        "max_tokens": 1500
    }
    
    try:
        r = requests.post(GROQ_URL, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        raw_text = r.json()["choices"][0]["message"]["content"]
        return humanize_text(raw_text)
    except Exception as e:
        print(f"Groq error: {e}")
        return f"Сегодня поговорим о {title}. Интересная тема, надо разобраться подробнее."

def build_html(title, body, date_str, slug):
    """Собираем HTML страницу"""
    # Берём ключевое слово для картинки
    keyword = slug.replace("-", " ")
    # Unsplash source (бесплатно, прямые ссылки)
    img_url = f"https://source.unsplash.com/800x400/?{requests.utils.quote(keyword)}"
    
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)}</title>
    <style>
        body {{ font-family: Georgia, serif; line-height: 1.7; max-width: 700px; margin: 0 auto; padding: 20px; color: #333; background: #fafafa; }}
        h1 {{ font-size: 1.8em; margin-bottom: 0.2em; color: #222; }}
        .meta {{ color: #888; font-size: 0.9em; margin-bottom: 20px; }}
        img {{ width: 100%; height: auto; border-radius: 8px; margin-bottom: 20px; }}
        p {{ margin-bottom: 1.2em; text-align: justify; }}
        a {{ color: #2a6496; }}
    </style>
</head>
<body>
    <article>
        <h1>{escape(title)}</h1>
        <div class="meta">{date_str}</div>
        <img src="{img_url}" alt="{escape(title)}" loading="lazy">
        {''.join(f'<p>{escape(p)}</p>' for p in body.split('\n\n') if p.strip())}
    </article>
</body>
</html>"""
    return html

def update_index(posts):
    """Обновляем главную страницу"""
    items = ""
    for post in sorted(posts, reverse=True)[:50]:  # последние 50
        items += f'<li><a href="{post["file"]}">{escape(post["title"])}</a> <span style="color:#888;font-size:0.85em">— {post["date"]}</span></li>\n'
    
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Автоблог</title>
    <style>
        body {{ font-family: Georgia, serif; max-width: 700px; margin: 40px auto; padding: 0 20px; color: #333; background: #fafafa; }}
        h1 {{ border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #eee; }}
        a {{ text-decoration: none; font-size: 1.1em; color: #2a6496; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>📝 Заметки и мысли</h1>
    <p style="color:#666">Новый пост примерно каждый час. Всё как есть.</p>
    <ul>
        {items}
    </ul>
</body>
</html>"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

def main():
    now = datetime.datetime.now()
    date_str = now.strftime("%d.%m.%Y %H:%M")
    date_slug = now.strftime("%Y-%m-%d-%H")
    
    # Получаем тему
    title, summary = fetch_trend_topic()
    print(f"Topic: {title}")
    
    # Генерируем текст
    article_body = generate_article(title, summary)
    
    # Создаём slug
    slug = slugify(title)[:40] or "post"
    filename = f"posts/{date_slug}-{slug}.html"
    
    # Создаём папку если нет
    os.makedirs("posts", exist_ok=True)
    
    # Пишем HTML
    html = build_html(title, article_body, date_str, slug)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    
    # Обновляем индекс
    posts = []
    if os.path.exists("posts"):
        for fname in os.listdir("posts"):
            if fname.endswith(".html"):
                # Парсим дату из имени файла
                try:
                    parts = fname.split("-")
                    d = f"{parts[2]}.{parts[1]}.{parts[0]} {parts[3]}:00"
                except:
                    d = "??"
                # Заголовок — из тега title файла (упрощённо)
                with open(f"posts/{fname}", "r", encoding="utf-8") as f:
                    content = f.read()
                    t = re.search(r"<title>(.*?)</title>", content)
                    t = t.group(1) if t else "Без названия"
                posts.append({"file": f"posts/{fname}", "title": t, "date": d})
    
    update_index(posts)
    print(f"Done: {filename}")

if __name__ == "__main__":
    main()

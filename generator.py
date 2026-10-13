import os
import requests
import json
import re
from datetime import datetime
from pathlib import Path

API_KEY = os.environ.get("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

def generate_content():
    if not API_KEY:
        raise ValueError("GROQ_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = (
        "Напиши пост (400-700 слов) на тему программирования, ИИ или кибербезопасности. "
        "Используй простой HTML: <p>, <h2>, <ul>, <li>, <strong>, <code>. "
        "Без <!DOCTYPE>, <html>, <head>, <body>. Только контент для вставки в div. "
        "Ответь на русском языке."
    )

    payload = {
        "model": "llama-3.1-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"API Error: {e}")
        return None

def make_filename(title):
    clean = re.sub(r'<[^>]+>', '', title)
    clean = re.sub(r'[^\w\s-]', '', clean).strip().lower()
    clean = re.sub(r'[\s]+', '-', clean)
    return clean[:50] or "post"

def create_post():
    print("Generating content...")
    raw = generate_content()
    if not raw:
        return False

    # Вытаскиваем заголовок
    title_match = re.search(r'<h2>(.*?)</h2>', raw, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
    else:
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        title = lines[0][:100] if lines else "Новый пост"

    # Убираем обёртку html/body если API вернул целую страницу
    content = raw
    if "<html" in content.lower():
        body = re.search(r'<body[^>]*>(.*?)</body>', content, re.IGNORECASE | re.DOTALL)
        if body:
            content = body.group(1)
        content = re.sub(r'</?(html|head|body|!doctype)[^>]*>', '', content, flags=re.IGNORECASE)

    # ⚠️ ВАЖНО: замену \n делаем ЗДЕСЬ, а не внутри f-string
    content_br = content.replace('\n', '<br>\n')
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M")
    filename = f"{date_str}-{make_filename(title)}.html"

    # HTML поста — здесь внутри {} НЕТ бэкслэшей
    post_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 700px; margin: 40px auto; padding: 0 20px; line-height: 1.6; color: #333; }}
        h1 {{ color: #111; }}
        .meta {{ color: #777; font-size: 0.9em; margin-bottom: 20px; }}
        a {{ color: #0066cc; }}
    </style>
</head>
<body>
    <a href="index.html">← На главную</a>
    <h1>{title}</h1>
    <div class="meta">{date_str} {time_str}</div>
    <div class="content">
{content_br}
    </div>
</body>
</html>"""

    Path(filename).write_text(post_html, encoding="utf-8")
    print(f"Created: {filename}")
    update_index(title, filename, date_str)
    return True

def update_index(title, filename, date_str):
    idx = Path("index.html")
    posts = []

    if idx.exists():
        text = idx.read_text(encoding="utf-8")
        found = re.findall(r'<li><a href="([^"]+)">([^<]+)</a> - ([^<]+)</li>', text)
        for href, t, d in found:
            posts.append({"file": href, "title": t, "date": d})

    posts.insert(0, {"file": filename, "title": title, "date": date_str})
    posts = posts[:50]  # храним последние 50

    lines = []
    for p in posts:
        safe = p['title'].replace('"', '&quot;')
        lines.append(f'        <li><a href="{p["file"]}">{safe}</a> — {p["date"]}</li>')

    list_html = "\n".join(lines)

    index_html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoSite</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 700px; margin: 40px auto; padding: 0 20px; color: #333; }}
        h1 {{ color: #111; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ padding: 10px 0; border-bottom: 1px solid #eee; }}
        a {{ text-decoration: none; color: #0066cc; font-size: 1.1em; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>AutoSite</h1>
    <p>Последние посты:</p>
    <ul>
{list_html}
    </ul>
</body>
</html>"""

    idx.write_text(index_html, encoding="utf-8")
    print("Updated index.html")

if __name__ == "__main__":
    create_post()

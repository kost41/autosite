#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoSite Generator
"""

import os
import re
import json
import random
from pathlib import Path
from datetime import datetime

import requests

# ==================== НАСТРОЙКИ ====================
SITE_NAME = "Системный взгляд"
SITE_TAGLINE = "Заметки о технологиях, бизнесе и инструментах. Без воды."
# ===================================================

API_KEY = os.environ.get("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("GROQ_API_KEY not set")

API_URL = "https://api.groq.com/openai/v1/chat/completions"

TOPICS = [
    "Python-разработка: скрытые возможности стандартной библиотеки",
    "Как не потерять фокус в эпоху уведомлений",
    "Простые инструменты для автоматизации рутины",
    "Чем отличается хороший API от плохого",
    "Инвестиции в себя: навыки с наибольшей отдачей",
    "Основы системного мышления на пальцах",
    "Как читать документацию, чтобы не засыпать",
    "Паттерны проектирования в реальной жизни",
    "Зачем разработчику разбираться в продукте",
    "Маленькие привычки, которые экономят часы",
    "Честный взгляд на удаленную работу",
    "Как принимать решения при нехватке данных",
]


def api_call(messages, max_tokens=2048):
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.75,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    r = requests.post(API_URL, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def generate_article(topic: str):
    sys_msg = (
        "Ты — практикующий разработчик и автор технического блога. "
        "Пишешь живо, без канцелярита, конкретно. "
        "Избегай слов: данный, представленный, позволяет, является, носит, осуществляет. "
        "Ответь строго JSON: {\"title\":\"...\",\"excerpt\":\"...\",\"content\":\"...\",\"reading_time\":число}. "
        "excerpt — 1-2 предложения о сути статьи. "
        "content — HTML только с тегами: <h2>, <p>, <ul>, <li>, <strong>, <em>, <blockquote>. "
        "Без markdown, без ```. Объём: 600-800 слов."
    )
    raw = api_call([
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": f"Тема: «{topic}»."},
    ], max_tokens=4096)
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if not m:
        raise ValueError(f"No JSON in LLM output: {raw[:300]}")
    return json.loads(m.group(0))


def slugify(title: str) -> str:
    s = title.lower()
    s = re.sub(r'[^a-zа-яё0-9\s-]', '', s)
    s = re.sub(r'\s+', '-', s).strip('-')
    return s[:80]


def build_post_html(title, date_str, content, reading_time, excerpt):
    excerpt_safe = excerpt.replace('"', '&quot;')
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — {SITE_NAME}</title>
<meta name="description" content="{excerpt_safe}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--bg:#fafafa;--surface:#ffffff;--text:#1a1a1a;--muted:#737373;--accent:#2563eb;--accent-hover:#1d4ed8;--border:#e5e7eb;--shadow:0 1px 3px rgba(0,0,0,0.07);--font:Inter,system-ui,-apple-system,sans-serif;}}
*,*::before,*::after{{box-sizing:border-box;margin:0}}
body{{font-family:var(--font);background:var(--bg);color:var(--text);line-height:1.65;-webkit-font-smoothing:antialiased}}
a{{color:var(--accent);text-decoration:none}}a:hover{{color:var(--accent-hover);text-decoration:underline}}
.container{{max-width:720px;margin:0 auto;padding:0 20px}}
header{{padding:32px 0 24px;border-bottom:1px solid var(--border);margin-bottom:40px}}
.brand{{font-size:18px;font-weight:700;letter-spacing:-0.02em;color:var(--text)}}
.brand span{{color:var(--muted);font-weight:400;margin-left:8px;font-size:15px}}
.back{{display:inline-flex;align-items:center;gap:6px;font-size:14px;color:var(--muted);margin-bottom:24px}}
.back:hover{{color:var(--accent)}}
article{{background:var(--surface);padding:40px;border-radius:12px;border:1px solid var(--border);box-shadow:var(--shadow)}}
.meta{{display:flex;align-items:center;gap:16px;margin-bottom:24px;flex-wrap:wrap;font-size:14px;color:var(--muted)}}
h1{{font-size:clamp(26px,5vw,36px);line-height:1.15;margin-bottom:20px;letter-spacing:-0.02em;font-weight:700}}
.article-body p{{margin-bottom:1.15em;font-size:17px}}
.article-body p:last-child{{margin-bottom:0}}
.article-body h2{{font-size:22px;margin-top:2rem;margin-bottom:.8rem;font-weight:600}}
.article-body ul{{padding-left:1.4rem;margin-bottom:1.15em}}
.article-body li{{margin:.35rem 0}}
.article-body blockquote{{margin:1.5rem 0;padding:1.2rem 1.5rem;border-left:3px solid var(--accent);background:#f8fafc;font-style:italic;color:var(--muted)}}
footer{{text-align:center;padding:40px 0;color:var(--muted);font-size:13px;border-top:1px solid var(--border);margin-top:60px}}
@media (max-width:600px){{article{{padding:24px}}h1{{font-size:24px}}}}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="brand">{SITE_NAME}<span>— {SITE_TAGLINE}</span></div>
  </header>
  <a class="back" href="index.html">← На главную</a>
  <article>
    <div class="meta">
      <span>{date_str}</span>
      <span>·</span>
      <span>⏱ {reading_time} мин</span>
    </div>
    <h1>{title}</h1>
    <div class="article-body">
      {content}
    </div>
  </article>
  <footer>
    © {datetime.now().year} {SITE_NAME}
  </footer>
</div>
</body>
</html>"""


def build_index_html(posts):
    cards = []
    for p in posts:
        cards.append(
            f'    <a class="card" href="{p["file"]}">\n'
            f'      <h2>{p["title"]}</h2>\n'
            f'      <p class="card-excerpt">{p["excerpt"]}</p>\n'
            f'      <div class="card-meta">{p["date"]} · {p["reading_time"]} мин</div>\n'
            f'    </a>'
        )
    cards_html = "\n".join(cards) if cards else '<p class="empty">Пока нет записей.</p>'

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{SITE_NAME}</title>
<meta name="description" content="{SITE_TAGLINE}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{{--bg:#fafafa;--surface:#ffffff;--text:#1a1a1a;--muted:#737373;--accent:#2563eb;--border:#e5e7eb;--shadow:0 1px 3px rgba(0,0,0,0.07);--shadow-hover:0 10px 15px -3px rgba(0,0,0,0.07);--font:Inter,system-ui,-apple-system,sans-serif;}}
*,*::before,*::after{{box-sizing:border-box;margin:0}}
body{{font-family:var(--font);background:var(--bg);color:var(--text);line-height:1.6;-webkit-font-smoothing:antialiased}}
a{{color:var(--accent);text-decoration:none}}
.container{{max-width:960px;margin:0 auto;padding:0 20px}}
.hero{{padding:64px 0 48px;text-align:center;border-bottom:1px solid var(--border);margin-bottom:40px}}
.hero h1{{font-size:clamp(30px,6vw,44px);letter-spacing:-0.03em;line-height:1.1;margin-bottom:14px;font-weight:700}}
.hero p{{font-size:17px;color:var(--muted);max-width:560px;margin:0 auto;line-height:1.55}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:24px;padding-bottom:60px}}
.card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:28px;display:flex;flex-direction:column;gap:10px;box-shadow:var(--shadow);transition:transform .15s ease,box-shadow .15s ease;text-decoration:none;color:inherit}}
.card:hover{{transform:translateY(-2px);box-shadow:var(--shadow-hover)}}
.card h2{{font-size:19px;line-height:1.3;color:var(--text);margin:0;font-weight:600}}
.card-excerpt{{font-size:15px;color:var(--muted);line-height:1.55;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;margin:0}}
.card-meta{{margin-top:auto;font-size:13px;color:var(--muted);padding-top:8px}}
.empty{{text-align:center;color:var(--muted);padding:60px 0;font-size:16px}}
footer{{text-align:center;padding:36px 0;color:var(--muted);font-size:13px;border-top:1px solid var(--border)}}
@media (max-width:600px){{.hero{{padding:40px 0 32px}}}}
</style>
</head>
<body>
<div class="container">
  <section class="hero">
    <h1>{SITE_NAME}</h1>
    <p>{SITE_TAGLINE}</p>
  </section>
  <div class="grid">
{cards_html}
  </div>
  <footer>
    © {datetime.now().year} {SITE_NAME}
  </footer>
</div>
</body>
</html>"""


def create_post():
    today = datetime.now().strftime("%Y-%m-%d")
    existing = [f.stem for f in Path(".").glob("20*.html")]
    if any(today in e for e in existing):
        print(f"Post for {today} already exists. Skip.")
    else:
        topic = random.choice(TOPICS)
        print(f"Topic: {topic}")
        data = generate_article(topic)
        title = data.get("title", "Без названия")
        excerpt = data.get("excerpt", "")
        content = data.get("content", "")
        reading_time = data.get("reading_time", random.randint(5, 10))

        slug = slugify(title)
        date_slug = datetime.now().strftime("%Y-%m-%d-%H%M")
        filename = f"{date_slug}-{slug}.html"

        months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]
        d = datetime.now()
        date_ru = f"{d.day} {months[d.month-1]} {d.year}"

        html = build_post_html(title, date_ru, content, reading_time, excerpt)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Created: {filename}")

    rebuild_index()
    return True


def rebuild_index():
    posts = []
    for f in sorted(Path(".").glob("20*.html"), reverse=True):
        text = f.read_text(encoding="utf-8")
        title_match = re.search(r'<title>(.*?) —', text)
        title = title_match.group(1).strip() if title_match else f.stem
        date_match = re.search(r'<span>(\d{1,2}\s+[а-я]+)', text)
        date = date_match.group(1).strip() if date_match else f.stem[:10]
        excerpt_match = re.search(r'<meta name="description" content="(.*?)"', text)
        excerpt = excerpt_match.group(1).strip() if excerpt_match else ""
        rt_match = re.search(r'⏱ (\d+) мин', text)
        reading_time = int(rt_match.group(1)) if rt_match else 5
        posts.append({
            "file": f.name,
            "title": title,
            "date": date,
            "excerpt": excerpt,
            "reading_time": reading_time,
        })

    idx = build_index_html(posts)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(idx)
    print("Rebuilt index.html")


if __name__ == "__main__":
    create_post()

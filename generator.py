#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoSite Generator — Media Edition with Monetization
"""

import os
import re
import json
import random
from pathlib import Path
from datetime import datetime

import requests

# ======================= НАСТРОЙКИ =======================
SITE_NAME = "Hardcode"
SITE_URL = "https://kost41.github.io/autosite"
SITE_TAGLINE = "Практические гайды, зарплаты, инструменты. Без воды."
AUTHOR = "Hardcode Team"
LANG = "ru"

# AdSense (вставь свои значения после получения одобрения)
ADSENSE_CLIENT = "ca-pub-XXXXXXXXXXXXXXXX"   # <-- ЗАМЕНИ
ADSENSE_SLOTS = {
    "header": "1111111111",
    "in_content": "2222222222",
    "sidebar": "3333333333",
    "footer": "4444444444",
    "mobile_sticky": "5555555555",
}

# Партнёрские ссылки (вставь свои рефералки)
PARTNERS = {
    "hosting": "https://www.namecheap.com/hosting/shared/?aff=XXXXX",      # хостинг
    "vpn": "https://nordvpn.com/ru/",                                       # VPN
    "ai": "https://chat.openai.com/",                                      # ChatGPT
    "courses": "https://www.udemy.com/",                                   # курсы
}

# Темы с высоким поисковым потенциалом и вирусностью
TOPICS = [
    "Сколько зарабатывает Python-разработчик в 2026: зарплаты по городам и уровням",
    "Лучшие бесплатные VPN в 2026: ТОП-5 реально быстрых сервисов",
    "GitHub Copilot бесплатно: как получить и реально ли он заменяет джуна",
    "Как создать сайт бесплатно с нуля: пошаговый гайд для новичков",
    "ТОП-10 расширений VS Code, которые увеличивают продуктивность в 2 раза",
    "Удалённая работа в 2026: где искать заказы и как не попасть на мошенников",
    "Python для начинающих с нуля: дорожная карта 2026 года",
    "ChatGPT vs Claude vs Gemini: какой ИИ выбрать для программирования",
    "Как заработать на сайте с нуля: 5 проверенных способов монетизации",
    "Лучшие курсы по Python: бесплатные и платные в 2026 — наш выбор",
    "SSD или HDD для сервера в 2026: сравнение с цифрами и кейсами",
    "Защита данных в 2026: как не слить пароли и не попасть на фишинг",
    "Docker для новичков: объяснение на пицце за 10 минут",
    "Бесплатные альтернативы Photoshop: ТОП-3 для веб-дизайнера",
    "Как выйти на зарубежного заказчика: гайд по фрилансу в 2026",
]

API_KEY = os.environ.get("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("GROQ_API_KEY not set")

API_URL = "https://api.groq.com/openai/v1/chat/completions"


def api_call(messages, max_tokens=2048):
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.78,
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
        "Ты — главный редактор технологического медиа с аудиторией 500 000. "
        "Пишешь живо, цепляешь с первого абзаца, даёшь конкретику, цифры, кейсы. "
        "Тон: уверенный эксперт, но без занудства. Как будто объясняешь другу за кофе. "
        "Запрещённые слова: данный, представленный, позволяет, является, носит, осуществляет, "
        "вследствие, исходя из, в рамках, в целях, на основании. "
        "\n\nОтветь строго JSON объектом без markdown-обёртки:\n"
        "{\n"
        '  "title": "Кликабельный SEO-заголовок 60-70 символов",\n'
        '  "excerpt": "Описание для meta 150-160 символов. Цепляющее.",\n'
        '  "content": "HTML-контент...",\n'
        '  "faq": [\n'
        '    {"question":"...","answer":"..."}\n'
        '  ],\n'
        '  "reading_time": 8\n'
        "}\n\n"
        "Требования к content:\n"
        "- Начни с вводного абзаца <p class='lead'> — 2-3 предложения, которые цепляют проблему.\n"
        "- Используй <h2> для разделов, <h3> для подразделов.\n"
        "- Добавь <ul>/<li> для списков.\n"
        "- Выделяй ключевые моменты <strong>.\n"
        "- Минимум одна цитата <blockquote>.\n"
        "- Минимум один блок с кодом <pre><code class='language-python'>...</code></pre>.\n"
        "- Объём 900-1200 слов. Не повторяйся.\n"
        "- FAQ: 3-4 вопроса, которые реально ищут в Google. Краткие, честные ответы."
    )
    raw = api_call([
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": f"Тема: «{topic}». Напиши статью, которую захочется дочитать и которой захочется поделиться."},
    ], max_tokens=4096)
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    if not m:
        raise ValueError(f"No JSON in LLM output: {raw[:400]}")
    data = json.loads(m.group(0))
    return data


def slugify(text: str) -> str:
    s = text.lower()
    s = re.sub(r'[^a-zа-яё0-9\s-]', '', s)
    s = re.sub(r'\s+', '-', s).strip('-')
    return s[:90]


def add_ids_to_headings(html: str) -> str:
    def repl(m):
        inner = m.group(1)
        txt = re.sub(r'<[^>]+>', '', inner)
        aid = slugify(txt)
        return f'<h2 id="{aid}">{inner}</h2>'
    return re.sub(r'<h2>(.*?)</h2>', repl, html, flags=re.DOTALL)


def build_toc(html: str) -> str:
    items = []
    for m in re.finditer(r'<h2 id="([^"]+)">(.*?)</h2>', html):
        aid = m.group(1)
        txt = re.sub(r'<[^>]+>', '', m.group(2))
        items.append(f'<li><a href="#{aid}">{txt}</a></li>')
    if not items:
        return ""
    return '<nav class="toc"><div class="toc-title">Содержание</div><ul>' + "\n".join(items) + "</ul></nav>"


def adsense_block(slot: str, style: str = "display:block", extra: str = ""):
    if "XXXXXXXX" in ADSENSE_CLIENT:
        return f"<!-- AdSense: вставь свой код. Slot: {slot} -->"
    return f'''<div class="ad-box">
<ins class="adsbygoogle" style="{style}" data-ad-client="{ADSENSE_CLIENT}" data-ad-slot="{ADSENSE_SLOTS.get(slot, '')}" data-ad-format="auto" data-full-width-responsive="true"{extra}></ins>
<script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</div>'''


def partner_box():
    opts = [
        ("Надёжный хостинг для проектов", PARTNERS.get("hosting", "#"), "Дешевые домены и SSD-хостинг с панелью управления"),
        ("Быстрый VPN без логов", PARTNERS.get("vpn", "#"), "Доступ к заблокированным ресурсам и защита трафика"),
        ("ChatGPT Plus для работы", PARTNERS.get("ai", "#"), "Ускорьте кодинг, тексты и аналитику в 2 раза"),
    ]
    title, link, desc = random.choice(opts)
    return f'''<div class="partner-box">
<div class="partner-label">Рекомендуем</div>
<div class="partner-title"><a href="{link}" target="_blank" rel="nofollow sponsored noopener">{title} →</a></div>
<div class="partner-desc">{desc}</div>
</div>'''


def build_faq_html(faq_list):
    if not faq_list:
        return ""
    items = []
    ld = []
    for q in faq_list:
        question = q.get("question", "")
        answer = q.get("answer", "")
        if not question or not answer:
            continue
        items.append(f'<details class="faq-item" itemscope itemprop="mainEntity" itemtype="https://schema.org/Question">'
                     f'<summary itemprop="name">{question}</summary>'
                     f'<div itemscope itemprop="acceptedAnswer" itemtype="https://schema.org/Answer">'
                     f'<div itemprop="text">{answer}</div></div></details>')
        ld.append({"@type": "Question", "name": question,
                   "acceptedAnswer": {"@type": "Answer", "text": answer}})
    if not items:
        return ""
    faq_ld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": ld}, ensure_ascii=False)
    return '<section class="faq-section"><h2>Частые вопросы</h2>\n' + "\n".join(items) + f'</section>\n<script type="application/ld+json">{faq_ld}</script>'


def related_posts_html(current_file, all_posts, n=3):
    others = [p for p in all_posts if p["file"] != current_file]
    if not others:
        return ""
    chosen = random.sample(others, min(n, len(others)))
    cards = "".join(
        f'<a class="rel-card" href="{p["file"]}">'
        f'<div class="rel-title">{p["title"]}</div>'
        f'<div class="rel-meta">{p["date"]} · {p["reading_time"]} мин</div></a>'
        for p in chosen
    )
    return f'<section class="related"><h3>Читайте также</h3><div class="rel-grid">{cards}</div></section>'


def post_json_ld(title, excerpt, date_iso, url):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": excerpt,
        "url": url,
        "author": {"@type": "Organization", "name": AUTHOR},
        "publisher": {"@type": "Organization", "name": SITE_NAME, "logo": {"@type": "ImageObject", "url": f"{SITE_URL}/favicon.ico"}},
        "datePublished": date_iso,
        "dateModified": date_iso,
    }, ensure_ascii=False)


COMMON_CSS = '''
:root{--bg:#f6f7f9;--surface:#ffffff;--text:#0f1115;--muted:#5b616b;--accent:#d62828;--accent2:#f77f00;--link:#005fcc;--border:#e2e4e8;--shadow:0 2px 8px rgba(0,0,0,.06);--radius:14px;--font:'Inter',system-ui,-apple-system,sans-serif;}
[data-theme="dark"]{--bg:#0f1115;--surface:#181b21;--text:#f0f2f5;--muted:#9aa0a8;--border:#2a2e36;--shadow:0 2px 8px rgba(0,0,0,.35);}
*,*::before,*::after{box-sizing:border-box;margin:0}
html{scroll-behavior:smooth}
body{font-family:var(--font);background:var(--bg);color:var(--text);line-height:1.65;-webkit-font-smoothing:antialiased;transition:background .2s,color .2s}
a{color:var(--link);text-decoration:none}a:hover{color:var(--accent);text-decoration:underline}
.container{max-width:1120px;margin:0 auto;padding:0 18px}
header.site-header{background:var(--surface);border-bottom:1px solid var(--border);padding:16px 0;position:sticky;top:0;z-index:50}
.header-inner{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}
.brand{font-size:20px;font-weight:800;letter-spacing:-.03em;color:var(--text)}.brand span{color:var(--accent)}
nav.header-nav{display:flex;gap:18px;font-size:14px;font-weight:500}
nav.header-nav a{color:var(--muted)}nav.header-nav a:hover{color:var(--text)}
.theme-toggle{background:none;border:1px solid var(--border);border-radius:8px;padding:6px 10px;cursor:pointer;font-size:13px;color:var(--muted)}
.hero{padding:56px 0 40px;text-align:center;border-bottom:1px solid var(--border);margin-bottom:32px}
.hero h1{font-size:clamp(28px,5vw,46px);letter-spacing:-.04em;line-height:1.08;margin-bottom:14px;font-weight:800}
.hero p{font-size:18px;color:var(--muted);max-width:560px;margin:0 auto}
.grid-layout{display:grid;grid-template-columns:1fr 300px;gap:32px;align-items:start}
.posts-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:24px;padding-bottom:60px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:24px;display:flex;flex-direction:column;gap:10px;box-shadow:var(--shadow);transition:transform .15s,box-shadow .15s;text-decoration:none;color:inherit;min-height:200px}
.card:hover{transform:translateY(-3px);box-shadow:0 8px 20px rgba(0,0,0,.1)}
.card h2{font-size:18px;line-height:1.35;font-weight:700;margin:0}
.card .excerpt{font-size:15px;color:var(--muted);line-height:1.55;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;margin:0}
.card-meta{margin-top:auto;font-size:12px;color:var(--muted);font-weight:500;text-transform:uppercase;letter-spacing:.03em}
.ad-box{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:20px;text-align:center;margin:24px 0}
.sidebar-ad{position:sticky;top:90px}
.partner-box{background:linear-gradient(135deg,#fff7ed,#fff0f0);border:1px solid #ffe4e6;border-radius:var(--radius);padding:22px;margin:24px 0}
[data-theme="dark"] .partner-box{background:linear-gradient(135deg,#2a1f1f,#1f1f2a);border-color:#3a2a2a}
.partner-label{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--accent);font-weight:700;margin-bottom:8px}
.partner-title{font-size:17px;font-weight:700;margin-bottom:6px}
.partner-desc{font-size:14px;color:var(--muted)}
article.post{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:36px;box-shadow:var(--shadow);margin-bottom:24px}
.post-header{margin-bottom:28px}
.post-header h1{font-size:clamp(26px,4.5vw,38px);line-height:1.1;letter-spacing:-.03em;margin-bottom:12px}
.meta{display:flex;align-items:center;gap:14px;flex-wrap:wrap;font-size:14px;color:var(--muted)}
.meta span::before{content:"·";margin-right:14px;color:var(--border)}.meta span:first-child::before{content:none}
.lead{font-size:19px;color:var(--muted);line-height:1.55;margin-bottom:28px}
.toc{background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:18px 22px;margin-bottom:28px}
.toc-title{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:700;margin-bottom:10px}
.toc ul{list-style:none;padding:0;margin:0;display:grid;gap:6px}
.toc a{color:var(--text);font-size:15px}.toc a:hover{color:var(--accent)}
.article-body p{margin-bottom:1.25em;font-size:17px}
.article-body h2{font-size:22px;margin-top:2.2rem;margin-bottom:.9rem;font-weight:700;letter-spacing:-.01em}
.article-body h3{font-size:18px;margin-top:1.8rem;margin-bottom:.7rem;font-weight:600;color:var(--muted)}
.article-body ul{padding-left:1.5rem;margin-bottom:1.2em}
.article-body li{margin:.35rem 0}
.article-body blockquote{margin:1.6rem 0;padding:1.1rem 1.4rem;border-left:3px solid var(--accent);background:var(--bg);border-radius:0 10px 10px 0;font-style:italic;color:var(--muted)}
.article-body pre{background:#0d1117;color:#c9d1d9;padding:16px;border-radius:10px;overflow-x:auto;font-size:14px;margin-bottom:1.2em}
.article-body code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.88em;background:var(--bg);padding:.15em .4em;border-radius:5px;color:var(--accent)}
.article-body pre code{background:transparent;padding:0;color:inherit}
.faq-section{margin-top:36px;border-top:1px solid var(--border);padding-top:28px}
.faq-item{margin-bottom:14px;border:1px solid var(--border);border-radius:10px;padding:16px 18px;background:var(--bg)}
.faq-item summary{font-weight:600;cursor:pointer;list-style:none}.faq-item summary::-webkit-details-marker{display:none}
.faq-item[open] summary{margin-bottom:8px;color:var(--accent)}
.related{margin-top:36px;border-top:1px solid var(--border);padding-top:28px}
.rel-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px;margin-top:16px}
.rel-card{background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:16px;text-decoration:none;color:inherit}
.rel-title{font-weight:600;font-size:15px;margin-bottom:6px;line-height:1.3}
.rel-meta{font-size:12px;color:var(--muted)}
.sticky-mobile{position:fixed;bottom:0;left:0;right:0;background:var(--surface);border-top:1px solid var(--border);padding:10px;z-index:60;display:none;text-align:center}
footer.site-footer{text-align:center;padding:36px 0;color:var(--muted);font-size:13px;border-top:1px solid var(--border);margin-top:40px}
@media(max-width:900px){.grid-layout{grid-template-columns:1fr}.sidebar-ad{display:none}.sticky-mobile{display:block}}
@media(max-width:600px){.hero{padding:36px 0 28px}.hero h1{font-size:28px}article.post{padding:22px}}
'''.strip()


def base_page(title, desc, body, extra_head="", extra_end=""):
    return f'''<!DOCTYPE html>
<html lang="{LANG}" data-theme="light">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE_URL}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>{COMMON_CSS}</style>
{extra_head}
</head>
<body>
<header class="site-header"><div class="container header-inner">
  <a class="brand" href="index.html">{SITE_NAME}<span>.</span></a>
  <nav class="header-nav">
    <a href="index.html">Главная</a>
    <a href="about.html">О проекте</a>
    <a href="contacts.html">Контакты</a>
    <a href="privacy.html">Конфиденциальность</a>
  </nav>
  <button class="theme-toggle" onclick="toggleTheme()" title="Тема">☀️/🌙</button>
</div></header>
{body}
<footer class="site-footer"><div class="container">© {datetime.now().year} {SITE_NAME}. {SITE_TAGLINE}</div></footer>
<div class="sticky-mobile">{adsense_block('mobile_sticky')}</div>
<script>
function toggleTheme(){{let h=document.documentElement;let t=h.getAttribute('data-theme');h.setAttribute('data-theme',t==='dark'?'light':'dark');localStorage.setItem('theme',h.getAttribute('data-theme'));}}
(function(){{let t=localStorage.getItem('theme');if(t)document.documentElement.setAttribute('data-theme',t);}})();
</script>
{extra_end}
</body>
</html>'''


def build_post_html(title, date_ru, date_iso, content, reading_time, excerpt, faq_list, filename, all_posts):
    content = add_ids_to_headings(content)
    toc = build_toc(content)
    faq_html = build_faq_html(faq_list)
    related = related_posts_html(filename, all_posts)
    url = f"{SITE_URL}/{filename}"
    ld = post_json_ld(title, excerpt, date_iso, url)

    body = f'''
<div class="container grid-layout" style="padding-top:28px">
<main>
  <article class="post" itemscope itemtype="https://schema.org/Article">
    <div class="post-header">
      <div class="meta">
        <span>{date_ru}</span>
        <span>{reading_time} мин чтения</span>
      </div>
      <h1 itemprop="headline">{title}</h1>
    </div>
    <p class="lead">{excerpt}</p>
    {adsense_block('header')}
    {toc}
    <div class="article-body" itemprop="articleBody">
      {content}
    </div>
    {adsense_block('in_content')}
    {partner_box()}
    {faq_html}
    {related}
    {adsense_block('footer')}
    <meta itemprop="datePublished" content="{date_iso}">
    <meta itemprop="dateModified" content="{date_iso}">
  </article>
</main>
<aside class="sidebar">
  <div class="sidebar-ad">{adsense_block('sidebar', 'display:inline-block;width:300px;height:600px')}</div>
  <div class="partner-box">
    <div class="partner-label">Популярное</div>
    <div style="font-size:14px;line-height:1.6;color:var(--muted);margin-top:6px">
      Мы собрали гайды, которые реально помогают заработать и оптимизировать работу. Без воды.
    </div>
  </div>
</aside>
</div>
<script type="application/ld+json">{ld}</script>
'''
    return base_page(f"{title} — {SITE_NAME}", excerpt, body)


def build_index_html(posts):
    if not posts:
        cards = '<p class="empty">Пока нет записей. Скоро будет.</p>'
    else:
        # Первый пост — крупная карточка
        first = posts[0]
        rest = posts[1:]
        big = f'''
<a class="card" href="{first['file']}" style="grid-column:1 / -1; flex-direction:row; align-items:center; gap:28px;">
  <div style="flex:1">
    <h2 style="font-size:24px">{first['title']}</h2>
    <p class="excerpt">{first['excerpt']}</p>
    <div class="card-meta">{first['date']} · {first['reading_time']} мин</div>
  </div>
</a>
''' if len(posts) > 0 else ""
        cards = big + "\n".join(
            f'<a class="card" href="{p["file"]}">'
            f'<h2>{p["title"]}</h2>'
            f'<p class="excerpt">{p["excerpt"]}</p>'
            f'<div class="card-meta">{p["date"]} · {p["reading_time"]} мин</div>'
            f'</a>' for p in rest
        )
    body = f'''
<section class="hero">
  <h1>{SITE_NAME}</h1>
  <p>{SITE_TAGLINE}</p>
</section>
<div class="container grid-layout">
  <div class="posts-grid">
    {cards}
  </div>
  <aside class="sidebar">
    <div class="sidebar-ad">{adsense_block('sidebar', 'display:inline-block;width:300px;height:600px')}</div>
    {partner_box()}
    <div class="ad-box" style="margin-top:24px">
      <div style="font-size:13px;color:var(--muted);line-height:1.5">
        <strong>Подпишись на обновления</strong><br>
        Новые гайды по заработку и автоматизации — без спама.
      </div>
    </div>
  </aside>
</div>
'''
    return base_page(SITE_NAME, SITE_TAGLINE, body)


def build_about_html():
    body = '''
<div class="container" style="max-width:720px;padding-top:40px;padding-bottom:60px">
  <article class="post">
    <h1>О проекте</h1>
    <p class="lead">{SITE_NAME} — это практические заметки о технологиях, заработке и инструментах, которые реально работают.</p>
    <p>Мы не пишем «вода ради воды». Каждый материал проверяется на себе: от зарплатных цифр до настроек софта. Цель — дать читателю конкретику, которую можно применить сегодня же.</p>
    <p>Если у вас есть предложения или вопросы — пишите через страницу <a href="contacts.html">контактов</a>.</p>
  </article>
</div>
'''.replace("{SITE_NAME}", SITE_NAME)
    return base_page(f"О проекте — {SITE_NAME}", f"Кто стоит за {SITE_NAME}. Практические гайды без воды.", body)


def build_contacts_html():
    body = '''
<div class="container" style="max-width:720px;padding-top:40px;padding-bottom:60px">
  <article class="post">
    <h1>Контакты</h1>
    <p>По вопросам сотрудничества, рекламы и предложений пишите на электронную почту.</p>
    <p>Мы отвечаем в течение 1-2 рабочих дней.</p>
    <ul>
      <li>Email: contact@example.com (замени на свой)</li>
      <li>Тема: реклама, гостевые посты, партнёрство</li>
    </ul>
  </article>
</div>
'''
    return base_page(f"Контакты — {SITE_NAME}", "Контакты для связи и сотрудничества.", body)


def build_privacy_html():
    body = '''
<div class="container" style="max-width:720px;padding-top:40px;padding-bottom:60px">
  <article class="post">
    <h1>Политика конфиденциальности</h1>
    <p>Мы уважаем вашу приватность. На сайте используются файлы cookie для аналитики и показа персонализированной рекламы.</p>
    <p>Мы сотрудничаем с рекламными сетями (Google AdSense). Эти партнёры могут использовать cookie для подбора релевантных объявлений.</p>
    <p>Вы можете отключить cookie в настройках браузера. Продолжая использовать сайт, вы соглашаетесь с использованием cookie.</p>
    <h2>Сбор данных</h2>
    <p>Мы не собираем персональные данные без вашего согласия. Все формы обратной связи работают через сторонние сервисы.</p>
  </article>
</div>
'''
    return base_page(f"Конфиденциальность — {SITE_NAME}", "Политика конфиденциальности и использования cookie.", body)


def build_sitemap(posts):
    urls = [f"<url><loc>{SITE_URL}/index.html</loc><changefreq>daily</changefreq><priority>1.0</priority></url>"]
    for p in posts:
        urls.append(f"<url><loc>{SITE_URL}/{p['file']}</loc><lastmod>{p['date_iso']}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>")
    extras = ["about.html", "contacts.html", "privacy.html"]
    for e in extras:
        urls.append(f"<url><loc>{SITE_URL}/{e}</loc><changefreq>monthly</changefreq><priority>0.5</priority></url>")
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>"


def build_robots_txt():
    return f"""User-agent: *
Allow: /
Sitemap: {SITE_URL}/sitemap.xml
"""


def build_ads_txt():
    if "XXXXXXXX" in ADSENSE_CLIENT:
        return "# Замени XXXXXX на свой publisher ID после регистрации в AdSense\ngoogle.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0"
    pid = ADSENSE_CLIENT.replace("ca-pub-", "")
    return f"google.com, {pid}, DIRECT, f08c47fec0942fa0"


def create_post():
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    existing = [f.stem for f in Path(".").glob("20*.html")]
    if any(today_str in e for e in existing):
        print(f"Post for {today_str} already exists. Skip generation.")
    else:
        topic = random.choice(TOPICS)
        print(f"Generating: {topic}")
        data = generate_article(topic)

        title = data.get("title", "Без названия")
        excerpt = data.get("excerpt", "")
        content = data.get("content", "")
        faq = data.get("faq", [])
        reading_time = data.get("reading_time", random.randint(6, 12))

        slug = slugify(title)
        date_slug = today.strftime("%Y-%m-%d-%H%M")
        filename = f"{date_slug}-{slug}.html"

        months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]
        date_ru = f"{today.day} {months[today.month-1]} {today.year}"
        date_iso = today.strftime("%Y-%m-%d")

        # Собираем текущие посты для блока "Читайте также"
        all_posts = []
        for f in sorted(Path(".").glob("20*.html"), reverse=True):
            t = f.read_text(encoding="utf-8")
            tm = re.search(r'<title>(.*?) —', t)
            em = re.search(r'<meta name="description" content="(.*?)"', t)
            dm = re.search(r'<span>(\d{1,2}\s+[а-я]+)', t)
            rm = re.search(r'(\d+) мин чтения', t)
            all_posts.append({
                "file": f.name,
                "title": tm.group(1).strip() if tm else f.stem,
                "excerpt": em.group(1).strip() if em else "",
                "date": dm.group(1).strip() if dm else f.stem[:10],
                "date_iso": f.stem[:10],
                "reading_time": int(rm.group(1)) if rm else 5,
            })

        html = build_post_html(title, date_ru, date_iso, content, reading_time, excerpt, faq, filename, all_posts)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Created: {filename}")

    rebuild_all()
    return True


def rebuild_all():
    posts = []
    for f in sorted(Path(".").glob("20*.html"), reverse=True):
        t = f.read_text(encoding="utf-8")
        tm = re.search(r'<title>(.*?) —', t)
        em = re.search(r'<meta name="description" content="(.*?)"', t)
        dm = re.search(r'<span>(\d{1,2}\s+[а-я]+)', t)
        rm = re.search(r'(\d+) мин чтения', t)
        posts.append({
            "file": f.name,
            "title": tm.group(1).strip() if tm else f.stem,
            "excerpt": em.group(1).strip() if em else "",
            "date": dm.group(1).strip() if dm else f.stem[:10],
            "date_iso": f.stem[:10],
            "reading_time": int(rm.group(1)) if rm else 5,
        })

    # Index
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(build_index_html(posts))

    # Service pages
    with open("about.html", "w", encoding="utf-8") as f:
        f.write(build_about_html())
    with open("contacts.html", "w", encoding="utf-8") as f:
        f.write(build_contacts_html())
    with open("privacy.html", "w", encoding="utf-8") as f:
        f.write(build_privacy_html())
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(build_sitemap(posts))
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(build_robots_txt())
    with open("ads.txt", "w", encoding="utf-8") as f:
        f.write(build_ads_txt())

    print("Rebuilt: index.html, service pages, sitemap.xml, robots.txt, ads.txt")


if __name__ == "__main__":
    create_post()

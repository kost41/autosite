import os
import random
import re
import json
import textwrap
from datetime import datetime
from pathlib import Path

import requests

API_KEY = os.environ.get("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("GROQ_API_KEY not set")

API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODELS_URL = "https://api.groq.com/openai/v1/models"

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
    "почему стартапы умирают в первый год",
    "как писать тексты для сайта, которые продают",
    "SEO в 2025: что работает, а что нет",
    "продажи через Telegram-каналы: пошаговая схема",
    "микросервисы или монолит: что выбрать",
    "как выйти на зарубежный рынок без офиса",
]

TAGLINES = [
    "Идеи, которые сложно скопировать.",
    "Тексты о бизнесе без воды.",
    "Честные заметки о том, что работает.",
    "Между кодом и кассой.",
    "Практика важнее теории. Всегда.",
    "Заметки из реальных проектов.",
]

FONT_PAIRS = {
    "amber":      ("Playfair+Display:ital,wght@0,400;0,700;1,400", "Inter:wght@300;400;600"),
    "vintage":    ("Merriweather:ital,wght@0,300;0,700;1,300",     "IBM+Plex+Sans:wght@400;500"),
    "brutalist":  ("Space+Grotesk:wght@400;700",                     "PT+Sans:ital,wght@0,400;0,700;1,400"),
    "midnight":   ("Montserrat:wght@400;700",                        "Open+Sans:ital,wght@0,400;0,600;1,400"),
    "forest":     ("Crimson+Text:ital,wght@0,400;0,600;1,400",       "Work+Sans:wght@300;400;500"),
    "cyberpunk":  ("Oswald:wght@400;600",                            "Roboto+Mono:wght@400;500"),
}

DESIGN_SYSTEMS = [
    {
        "key": "amber",
        "name": "Amber Editorial",
        "colors": {"bg": "#0f0f0f", "text": "#e7e7e7", "accent": "#ff9f1c", "surface": "#1a1a1a", "muted": "#888888"},
        "radius": "2px",
        "shadow": "0 12px 40px rgba(0,0,0,0.4)",
        "extras": ["dropcap", "pullquote"],
    },
    {
        "key": "vintage",
        "name": "Vintage Newspaper",
        "colors": {"bg": "#fdfbf7", "text": "#222222", "accent": "#bc6c25", "surface": "#f4f1ea", "muted": "#666666"},
        "radius": "0px",
        "shadow": "4px 4px 0px #d6cfc7",
        "extras": ["double-top", "smallcaps-date"],
    },
    {
        "key": "brutalist",
        "name": "Concrete Brutalist",
        "colors": {"bg": "#ffffff", "text": "#000000", "accent": "#ff0000", "surface": "#f0f0f0", "muted": "#555555"},
        "radius": "0px",
        "shadow": "6px 6px 0px #000",
        "extras": ["thick-borders", "mono-meta"],
    },
    {
        "key": "midnight",
        "name": "Midnight Gradient",
        "colors": {"bg": "#0b0f19", "text": "#c9d1d9", "accent": "#58a6ff", "surface": "#161b22", "muted": "#8b949e"},
        "radius": "16px",
        "shadow": "0 8px 32px rgba(88,166,255,0.08)",
        "extras": ["glass", "glow-hover"],
    },
    {
        "key": "forest",
        "name": "Forest Organic",
        "colors": {"bg": "#f4f7f5", "text": "#1a2e1a", "accent": "#2d6a4f", "surface": "#e9f0ea", "muted": "#5a6b5c"},
        "radius": "24px",
        "shadow": "0 4px 24px rgba(45,106,79,0.10)",
        "extras": ["soft", "pill-tags"],
    },
    {
        "key": "cyberpunk",
        "name": "Cyberpunk Street",
        "colors": {"bg": "#050505", "text": "#e0e0e0", "accent": "#00f0ff", "surface": "#111111", "muted": "#777777"},
        "radius": "0px",
        "shadow": "0 0 20px rgba(0,240,255,0.15)",
        "extras": ["glitch", "scanline"],
    },
]

AD_BLOCKS = [
    '<div style="margin:2.5rem 0;padding:1.5rem;background:var(--surface);border:1px dashed var(--muted);text-align:center;color:var(--muted);font-size:.8rem;letter-spacing:1px;text-transform:uppercase;">Рекламный блок<br><span style="font-size:.7rem;opacity:.7;">Замените на код AdSense / Яндекс.Директ</span></div>',
    '<div style="margin:2.5rem 0;padding:1.5rem;background:linear-gradient(135deg,var(--surface) 0%,transparent 100%);border-left:3px solid var(--accent);"><small style="text-transform:uppercase;letter-spacing:1px;color:var(--muted);font-size:.65rem;">Партнёрский материал</small><p style="margin:.4rem 0 0;font-weight:600;font-size:1.05rem;">Лучший хостинг для стартапа — 3 месяца бесплатно</p><a href="#" style="color:var(--accent);font-size:.9rem;">Получить скидку →</a></div>',
    '<div style="margin:2.5rem 0;padding:1.5rem;background:var(--surface);border:1px solid var(--muted);display:flex;gap:1rem;align-items:center;"><div style="font-size:2rem;">📦</div><div><strong style="color:var(--text);">Маркетплейс поставщиков</strong><p style="margin:.3rem 0 0;color:var(--muted);font-size:.9rem;">Найдите надёжных партнёров за 5 минут</p><a href="#" style="color:var(--accent);font-size:.8rem;">Каталог →</a></div></div>',
]


def fetch_available_models():
    try:
        r = requests.get(MODELS_URL, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=20)
        r.raise_for_status()
        models = r.json().get("data", [])
        ids = [m["id"] for m in models]
        print(f"Available Groq models: {ids[:10]}... ({len(ids)} total)")
        preferred_keywords = ["llama-4", "llama-3.3", "llama-3.1", "qwen", "deepseek", "mixtral"]
        for kw in preferred_keywords:
            for mid in ids:
                if kw in mid.lower():
                    print(f"Auto-selected model: {mid}")
                    return mid
        for mid in ids:
            if "llama" in mid.lower():
                return mid
        return ids[0] if ids else None
    except Exception as e:
        print(f"Could not fetch model list: {e}")
        return None


WORKING_MODEL = fetch_available_models()
if not WORKING_MODEL:
    WORKING_MODEL = "llama-3.3-70b-versatile"
    print(f"Fallback model: {WORKING_MODEL}")


def api_call(messages, max_tokens=2048):
    payload = {
        "model": WORKING_MODEL,
        "messages": messages,
        "temperature": 0.75,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        try:
            body = r.text[:500]
        except Exception:
            body = "no body"
        print(f"API Error: {e} | Body: {body}")
        raise


def generate_article(topic: str):
    sys_msg = (
        "Ты — опытный предприниматель и редактор блога. "
        "Пишешь живо, по-человечески, с лёгкой иронией, без воды и канцелярита. "
        "Избегай слов: данный, представленный, позволяет, является, носит, осуществляет. "
        "Ответь строго JSON: {\"title\":\"...\",\"excerpt\":\"...\",\"content\":\"...\",\"reading_time\":число}. "
        "excerpt — 1-2 цепких предложения для превью. "
        "content — HTML только с тегами: <h2>, <p>, <ul>, <li>, <strong>, <em>, <blockquote>. "
        "Без markdown, без ```. Объём: 700-900 слов."
    )
    raw = api_call([
        {"role": "system", "content": sys_msg},
        {"role": "user", "content": f"Тема: «{topic}». Добавь 1 цитату в <blockquote>."},
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


def insert_ads(content_html: str, n=2):
    parts = re.split(r'(</p>)', content_html)
    if len(parts) < 4:
        return content_html
    out = []
    ad_indices = sorted(random.sample(range(1, len(parts)//2), min(n, len(parts)//2 - 1)))
    p_idx = 0
    for i, chunk in enumerate(parts):
        out.append(chunk)
        if chunk == "</p>":
            p_idx += 1
            if p_idx in ad_indices:
                out.append(random.choice(AD_BLOCKS))
    return "".join(out)


def build_post_css(design):
    c = design["colors"]
    h_font, b_font = FONT_PAIRS[design["key"]]
    radius = design["radius"]
    extras = design["extras"]

    grain = ""
    if "scanline" in extras:
        grain = """
        body::before{content:"";position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 1px,rgba(0,0,0,.15) 1px,rgba(0,0,0,.15) 2px);pointer-events:none;z-index:9999;}
        """

    dropcap = ""
    if "dropcap" in extras:
        dropcap = """
        article > p:first-of-type::first-letter{font-family:var(--font-h);font-size:3.8rem;line-height:.8;float:left;margin-right:.6rem;margin-top:.2rem;color:var(--accent);}
        """

    glass = ""
    if "glass" in extras:
        glass = """
        header{backdrop-filter:blur(10px);background:rgba(22,27,34,.7)!important;border-bottom:1px solid rgba(88,166,255,.1);}
        """

    glow = ""
    if "glow-hover" in extras:
        glow = """
        a:hover{text-shadow:0 0 8px var(--accent);border-bottom-color:transparent!important;}
        """

    glitch = ""
    if "glitch" in extras:
        glitch = """
        h1{position:relative;}
        h1::after{content:attr(data-text);position:absolute;left:2px;top:0;color:#ff00ff;clip-path:inset(0 0 0 0);animation:glitch 2s infinite linear alternate-reverse;}
        @keyframes glitch{0%{clip-path:inset(20% 0 60% 0);}20%{clip-path:inset(60% 0 10% 0);}40%{clip-path:inset(40% 0 40% 0);}60%{clip-path:inset(80% 0 5% 0);}80%{clip-path:inset(10% 0 70% 0);}100%{clip-path:inset(30% 0 30% 0);}}
        """

    thick = ""
    if "thick-borders" in extras:
        thick = """
        article{border:3px solid var(--text);padding:2rem;}
        h2{border-top:3px solid var(--text);padding-top:1rem;margin-top:2.5rem;}
        """

    smallcaps = ""
    if "smallcaps-date" in extras:
        smallcaps = """
        .meta{font-variant:small-caps;letter-spacing:2px;}
        """

    mono = ""
    if "mono-meta" in extras:
        mono = """
        .meta{font-family:var(--font-b);text-transform:uppercase;letter-spacing:1.5px;font-size:.75rem;}
        """

    selection = f"::selection{{background:var(--accent);color:var(--bg);}}"

    return textwrap.dedent(f"""
    @import url('https://fonts.googleapis.com/css2?family={h_font}&family={b_font}&display=swap');
    :root{{--bg:{c['bg']};--text:{c['text']};--accent:{c['accent']};--surface:{c['surface']};--muted:{c['muted']};--font-h:'{h_font.split(':')[0].replace('+',' ')}',serif;--font-b:'{b_font.split(':')[0].replace('+',' ')}',sans-serif;}}
    *{{box-sizing:border-box;}}
    body{{background:var(--bg);color:var(--text);font-family:var(--font-b);line-height:1.7;margin:0;min-height:100vh;}}
    .container{{max-width:740px;margin:0 auto;padding:2rem 1.5rem 4rem;}}
    header{{margin-bottom:2.5rem;padding-bottom:1.5rem;}}
    h1{{font-family:var(--font-h);font-size:clamp(2rem,5vw,3.4rem);line-height:1.05;margin:0 0 .6rem;letter-spacing:-.02em;}}
    .meta{{color:var(--muted);font-size:.85rem;margin:0 0 2rem;}}
    article > h2{{font-family:var(--font-h);font-size:1.5rem;margin-top:2.2rem;color:var(--text);}}
    article p{{margin:1.15rem 0;font-size:1.05rem;}}
    a{{color:var(--accent);text-decoration:none;border-bottom:1px solid transparent;transition:border-color .2s,color .2s;}}
    a:hover{{border-bottom-color:var(--accent);}}
    blockquote{{margin:2rem 0;padding:1.5rem;background:var(--surface);border-left:4px solid var(--accent);font-family:var(--font-h);font-size:1.15rem;font-style:italic;color:var(--text);}}
    ul{{padding-left:1.4rem;}}
    li{{margin:.35rem 0;}}
    footer{{margin-top:3rem;padding-top:1.5rem;border-top:1px solid var(--surface);font-size:.8rem;color:var(--muted);display:flex;gap:1rem;flex-wrap:wrap;}}
    .ps{{margin-top:2.5rem;padding-top:1.5rem;border-top:1px dashed var(--surface);font-style:italic;color:var(--muted);}}
    {selection}
    {grain}
    {dropcap}
    {glass}
    {glow}
    {glitch}
    {thick}
    {smallcaps}
    {mono}
    @media(max-width:600px){{.container{{padding:1.2rem 1rem 3rem;}}h1{{font-size:2rem;}}}}
    """).strip()


def build_post_html(design, title, date_str, content, reading_time):
    css = build_post_css(design)
    content_with_ads = insert_ads(content, n=random.choice([1, 2]))
    ps_phrases = [
        "P.S. Если читаете это в три часа ночи — ложитесь спать. Бизнес подождёт.",
        "P.S. Лучший способ проверить идею — спросить у клиента, а не у друга.",
        "P.S. Не забывайте выключать ноутбук хотя бы на выходные.",
        "P.S. Текст написан без нейросетей. Шучу. Но проверьте факты сами.",
        "P.S. Делитесь ссылкой, если было полезно. Или не делитесь — мы не торгуем лайками.",
    ]
    ps = f'<div class="ps">{random.choice(ps_phrases)}</div>'

    deco = ""
    if design["key"] == "amber":
        deco = '<div style="height:4px;width:60px;background:var(--accent);margin:0 0 1.5rem;border-radius:2px;"></div>'
    elif design["key"] == "vintage":
        deco = '<div style="height:1px;background:var(--accent);margin:0 0 1.5rem;opacity:.4;"></div>'
    elif design["key"] == "midnight":
        deco = '<div style="height:120px;background:linear-gradient(135deg,var(--accent),transparent);opacity:.15;filter:blur(30px);border-radius:50%;margin:0 0 1rem;"></div>'
    elif design["key"] == "forest":
        deco = '<div style="height:6px;width:40px;background:var(--accent);border-radius:10px;margin:0 0 1.5rem;"></div>'

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>
<div class="container">
<header>
{deco}
<h1>{title}</h1>
<p class="meta">{date_str} · {reading_time} мин чтения</p>
</header>
<article>
{content_with_ads}
{ps}
</article>
<footer>
<a href="index.html">← На главную</a>
<a href="about.html">О проекте</a>
<a href="privacy.html">Политика</a>
</footer>
</div>
</body>
</html>"""


def build_index_html(design, posts, tagline):
    c = design["colors"]
    h_font, b_font = FONT_PAIRS[design["key"]]
    cards = []
    for i, p in enumerate(posts):
        cards.append(f"""
        <article class="card">
            <a href="{p['file']}" class="card-link">
                <h2>{p['title']}</h2>
                <p class="excerpt">{p['excerpt']}</p>
                <span class="card-meta">{p['date']} · {p['reading_time']} мин</span>
            </a>
        </article>
        """)
        if (i + 1) % random.choice([2, 3]) == 0 and i != len(posts) - 1:
            cards.append(f'<div class="card promo">{random.choice(AD_BLOCKS)}</div>')

    css = textwrap.dedent(f"""
    @import url('https://fonts.googleapis.com/css2?family={h_font}&family={b_font}&display=swap');
    :root{{--bg:{c['bg']};--text:{c['text']};--accent:{c['accent']};--surface:{c['surface']};--muted:{c['muted']};--font-h:'{h_font.split(':')[0].replace('+',' ')}',serif;--font-b:'{b_font.split(':')[0].replace('+',' ')}',sans-serif;}}
    *{{box-sizing:border-box;}}
    body{{background:var(--bg);color:var(--text);font-family:var(--font-b);margin:0;line-height:1.6;}}
    header{{padding:4rem 1.5rem 3rem;text-align:center;border-bottom:1px solid var(--surface);}}
    h1{{font-family:var(--font-h);font-size:clamp(2.2rem,6vw,4rem);margin:0;line-height:1.05;}}
    .tagline{{color:var(--muted);margin-top:.8rem;font-size:1.1rem;}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1.5rem;padding:2rem 1.5rem 4rem;max-width:1100px;margin:0 auto;}}
    .card{{background:var(--surface);padding:1.5rem;border-radius:8px;transition:transform .2s,box-shadow .2s;}}
    .card:hover{{transform:translateY(-3px);box-shadow:0 10px 30px rgba(0,0,0,.2);}}
    .card-link{{text-decoration:none;color:inherit;display:block;}}
    .card h2{{font-family:var(--font-h);font-size:1.25rem;margin:0 0 .6rem;color:var(--text);}}
    .excerpt{{color:var(--muted);margin:0 0 .8rem;font-size:.95rem;line-height:1.5;}}
    .card-meta{{font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;}}
    .promo{{grid-column:1/-1;background:transparent;border:2px dashed var(--surface);display:flex;align-items:center;justify-content:center;min-height:140px;}}
    footer{{text-align:center;padding:2rem;color:var(--muted);font-size:.8rem;border-top:1px solid var(--surface);}}
    footer a{{color:var(--muted);margin:0 .6rem;text-decoration:none;}}
    footer a:hover{{color:var(--accent);}}
    @media(max-width:600px){{.grid{{grid-template-columns:1fr;padding:1.5rem 1rem;}}header{{padding:3rem 1rem 2rem;}}}}
    """).strip()

    posts_html = "\n".join(cards)

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AutoSite</title>
<style>
{css}
</style>
</head>
<body>
<header>
<h1>AutoSite</h1>
<p class="tagline">{tagline}</p>
</header>
<main class="grid">
{posts_html}
</main>
<footer>
<a href="about.html">О проекте</a>
<a href="privacy.html">Конфиденциальность</a>
</footer>
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
        reading_time = data.get("reading_time", random.randint(5, 12))

        slug = slugify(title)
        date_slug = datetime.now().strftime("%Y-%m-%d-%H%M")
        filename = f"{date_slug}-{slug}.html"

        design = random.choice(DESIGN_SYSTEMS)
        print(f"Design: {design['name']}")

        months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]
        d = datetime.now()
        date_ru = f"{d.day} {months[d.month-1]} {d.year}"

        html = build_post_html(design, title, date_ru, content, reading_time)

        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Created: {filename}")

    # Пересобираем index ВСЕГДА, даже если пост пропущен
    rebuild_index()
    return True


def rebuild_index():
    posts = []
    for f in sorted(Path(".").glob("20*.html"), reverse=True):
        text = f.read_text(encoding="utf-8")
        title_match = re.search(r"<title>(.*?)</title>", text)
        title = title_match.group(1) if title_match else f.stem
        rt_match = re.search(r"(\d+)\s+мин\s+чтения", text)
        rt = rt_match.group(1) if rt_match else "5"
        date_match = re.search(r'class="meta">([^·]+)', text)
        date_str = date_match.group(1).strip() if date_match else ""
        p_match = re.search(r"<article>.*?<p>(.+?)</p>", text, re.DOTALL)
        excerpt = ""
        if p_match:
            excerpt = re.sub(r"<[^>]+>", "", p_match.group(1)).strip()[:140] + "…"
        posts.append({
            "file": f.name,
            "title": title,
            "date": date_str,
            "reading_time": rt,
            "excerpt": excerpt,
        })

    if not posts:
        return

    design = random.choice(DESIGN_SYSTEMS)
    tagline = random.choice(TAGLINES)
    index_html = build_index_html(design, posts, tagline)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print("index.html rebuilt.")


if __name__ == "__main__":
    create_post()

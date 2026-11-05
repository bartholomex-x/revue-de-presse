#!/usr/bin/env python3
"""
Revue de presse quotidienne par email Gmail.
Lit les flux RSS, genere un email HTML, l'envoie.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import feedparser
from datetime import datetime
import ssl

# ─── CONFIGURATION À MODIFIER ──────────────────────────────────────────────
RSS_FEEDS = {
    "Le Monde": "https://www.lemonde.fr/rss/une.xml",
    "Le Figaro": "https://www.lefigaro.fr/rss/figaro_actualites.xml",
    "Libération": "https://www.liberation.fr/arc/outboundfeeds/rss/",
    "Le Parisien": "https://feeds.leparisien.fr/leparisien/rss/paris-75",
    "Les Échos": "https://services.lesechos.fr/rss/les-echos-a-la-une.xml",
    "Ouest-France": "https://www.ouest-france.fr/rss-en-continu.xml",
    "La Voix du Nord": "https://www.lavoixdunord.fr/rss",
    "Sud Ouest": "https://www.sudouest.fr/rss.xml",
    "La Provence": "https://www.laprovence.com/rss/actu",
    "Mediapart": "https://www.mediapart.fr/articles/feed",
    "Le Canard enchaîné": "https://www.lecanardenchaine.fr/rss.xml",
    "Charlie Hebdo": "https://charliehebdo.fr/feed/",
}

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465  # Port modifié pour SSL
EMAIL_FROM = "oniluck@gmail.com"           # ← Ton adresse Gmail
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")  # lu depuis la variable d'environnement
EMAIL_TO = "oniluck@gmail.com"             # ← Ton adresse Gmail
# ────────────────────────────────────────────────────────────────────────────


def fetch_articles(feed_url, count=3):
    """Récupère les derniers articles d'un flux RSS"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(feed_url, headers=headers, timeout=15)
        feed = feedparser.parse(resp.content)
        return feed.entries[:count]
    except Exception as e:
        print(f"[WARN] Erreur flux: {e}")
        return []


def generate_html(newspaper_articles):
    """Genere l'email HTML"""
    today = datetime.now().strftime("%d %B %Y")

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ background: white; border-radius: 12px; padding: 30px; max-width: 600px; margin: 0 auto; }}
        .header {{ text-align: center; border-bottom: 2px solid #16a34a; padding-bottom: 20px; margin-bottom: 25px; }}
        .header h1 {{ color: #16a34a; margin: 0 0 10px; }}
        .header p {{ color: #666; margin: 0; }}
        .newspaper {{ margin-bottom: 25px; border-left: 4px solid #16a34a; padding-left: 20px; }}
        .newspaper h2 {{ color: #1a1a1a; margin: 0 0 10px; font-size: 18px; }}
        .article {{ margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #eee; }}
        .article:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
        .article a {{ color: #16a34a; text-decoration: none; font-weight: 500; }}
        .article a:hover {{ text-decoration: underline; }}
        .article .summary {{ color: #555; font-size: 13px; margin-top: 4px; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📰 Revue de presse quotidienne</h1>
            <p>{today}</p>
        </div>
"""

    for name, entries in newspaper_articles.items():
        if not entries:
            continue
        html += f'        <div class="newspaper">\n            <h2>{name}</h2>\n'
        for entry in entries:
            title = entry.get('title', 'Sans titre')
            link = entry.get('link', '#')
            summary = entry.get('summary', '')[:150] + '...' if entry.get('summary') else ''
            html += f'''            <div class="article">
                <a href="{link}" target="_blank">{title}</a>
                {f'<div class="summary">{summary}</div>' if summary else ''}
            </div>
'''
        html += '        </div>\n'

    html += f'''        <div class="footer">Généré à {datetime.now().strftime("%H:%M")} | {sum(len(a) for a in newspaper_articles.values())} articles</div>
    </div>
</body>
</html>'''
    return html


def send_email(html_content, subject):
    """Envoie l'email via Gmail SMTP en SSL"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    msg.attach(MIMEText("Votre revue de presse quotidienne", "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print("[OK] Email envoyé avec succes")
        return True
    except Exception as e:
        print(f"[ERROR] Envoi email: {e}")
        return False


def main():
    if not EMAIL_PASSWORD:
        print("[ERROR] Variable d'environnement EMAIL_PASSWORD manquante.")
        return
    print("[INFO] Recuperation des flux RSS...")
    newspaper_articles = {}

    for name, url in RSS_FEEDS.items():
        print(f"  -> {name}...")
        entries = fetch_articles(url, 3)
        newspaper_articles[name] = entries
        print(f"     {len(entries)} articles")

    print("[INFO] Generation du contenu email...")
    html = generate_html(newspaper_articles)

    print("[INFO] Envoi de l'email...")
    subject = f"Revue de presse - {datetime.now().strftime('%d/%m/%Y')}"
    if send_email(html, subject):
        print("[OK] Termine")
    else:
        print("[WARN] Email non envoye, mais HTML genere.")


if __name__ == "__main__":
    main()

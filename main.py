import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import google.generativeai as genai

# --- CONFIG ---
NEWS_API_KEY = os.environ["NEWS_API_KEY"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GMAIL_USER = os.environ["GMAIL_USER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
TO_EMAIL = "elom.karl.patrick@gmail.com"

TOPICS = ["cybersecurity", "artificial intelligence Claude Anthropic", "tech news"]

# --- FETCH NEWS ---
def fetch_articles():
    articles = []
    for topic in TOPICS:
        url = (
            f"https://newsapi.org/v2/everything"
            f"?q={topic}&language=en&sortBy=publishedAt&pageSize=3"
            f"&apiKey={NEWS_API_KEY}"
        )
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("articles"):
            for a in data["articles"]:
                articles.append(f"- {a['title']}: {a.get('description', '')}")
    return "\n".join(articles[:9])  # max 9 articles

# --- GENERATE THREADS ---
def generate_threads(articles_text):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""Tu es un créateur de contenu tech/cybersec francophone.
À partir de ces actualités, génère exactement 3 threads Twitter/Threads en français.
Chaque thread = 5 tweets max, percutants, informatifs, ton humain pas corporate.
Format :

🧵 THREAD 1 — [Sujet]
1/
2/
3/
...

🧵 THREAD 2 — [Sujet]
...

🧵 THREAD 3 — [Sujet]
...

Actualités :
{articles_text}
"""
    response = model.generate_content(prompt)
    return response.text

# --- SEND EMAIL ---
def send_email(threads_content):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🧵 Tes threads du jour"
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL

    body = MIMEText(threads_content, "plain", "utf-8")
    msg.attach(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_USER, TO_EMAIL, msg.as_string())

# --- MAIN ---
if __name__ == "__main__":
    articles = fetch_articles()
    if not articles:
        print("No articles fetched.")
        exit(0)
    threads = generate_threads(articles)
    send_email(threads)
    print("Email sent.")

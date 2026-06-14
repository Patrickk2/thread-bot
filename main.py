import os
import smtplib
import requests
import time
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- UTILS ---
def safe_encode(text):
    if not isinstance(text, str):
        text = str(text)
    return "".join(char for char in text if ord(char) < 128)

# --- CONFIGURATION ---
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
GMAIL_USER = safe_encode(os.environ.get("GMAIL_USER", ""))
GMAIL_APP_PASSWORD = safe_encode(os.environ.get("GMAIL_APP_PASSWORD", ""))
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
        try:
            r = requests.get(url, timeout=10)
            data = r.json()
            if data.get("articles"):
                for a in data["articles"]:
                    title = safe_encode(a.get('title', ''))
                    desc = safe_encode(a.get('description', ''))
                    articles.append(f"- {title}: {desc}")
        except Exception as e:
            print(f"Error fetching news for {topic}: {e}")
    return "\n".join(articles[:9])

# --- IMAGE LINKS ---
TOPIC_KEYWORDS = {
    "cybersecurity": "hacker+cybersecurity",
    "artificial intelligence": "artificial+intelligence",
    "anthropic": "artificial+intelligence+robot",
    "breach": "data+breach+security",
    "hack": "hacker+dark",
    "surveillance": "surveillance+camera",
    "water": "water+infrastructure",
    "military": "cyber+warfare",
    "bank": "banking+finance+security",
    "privacy": "privacy+digital",
    "ai": "artificial+intelligence",
    "tech": "technology+future",
}

def get_image_links(thread_text):
    thread_lower = thread_text.lower()
    keyword = "cybersecurity+technology"
    for key, val in TOPIC_KEYWORDS.items():
        if key in thread_lower:
            keyword = val
            break
    link1 = f"https://unsplash.com/s/photos/{keyword}"
    link2 = f"https://www.pexels.com/search/{keyword.replace('+', '%20')}/"
    return link1, link2

# --- GENERATE THREADS ---
def generate_threads(articles_text):
    prompt = f"""You are a viral tech/cybersecurity content creator.
From these news articles, generate exactly 3 Threads posts in ENGLISH.
Each post = 4 to 5 lines MAX. No more.

STRICT RULES:
1. OUTPUT ONLY THE POSTS. NO intro, NO conclusion, NO metadata.
2. Each post starts with a SHOCKING HOOK (a bold stat or provocative claim).
3. High contrast writing: short punchy sentences. No corporate tone.
4. End each post with one implicit call-to-action line.
5. After each post, on a new line write: KEYWORDS: [2-3 topic keywords in English, comma separated]

Format:
POST 1
[hook line]
[line 2]
[line 3]
[line 4]
[CTA line]
KEYWORDS: keyword1, keyword2

POST 2
...

News:
{articles_text}
"""

    models_to_try = [
        "openrouter/free",
        "deepseek/deepseek-chat-v3-0324:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "qwen/qwen3-coder:free"
    ]

    for model in models_to_try:
        print(f"Trying model: {model}...")
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/Patrickk2/thread-bot",
                    "X-Title": "Thread Bot GitHub Action"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=45
            )
            data = response.json()

            if "choices" in data:
                print(f"Success with {model}!")
                raw_content = data["choices"][0]["message"]["content"]
                return safe_encode(raw_content)

            print(f"Failed with {model}: {data.get('error', {}).get('message', 'Unknown error')}")
            time.sleep(3)

        except Exception as e:
            print(f"Network error with {model}: {e}")
            time.sleep(3)

    return None

# --- INJECT IMAGE LINKS ---
def inject_image_links(threads_content):
    lines = threads_content.split("\n")
    output = []
    post_buffer = []
    keywords_line = ""

    for line in lines:
        if line.strip().startswith("KEYWORDS:"):
            keywords_line = line.strip().replace("KEYWORDS:", "").strip()
            # Build image links from keywords
            kw = keywords_line.split(",")[0].strip().replace(" ", "+")
            img1 = f"https://unsplash.com/s/photos/{kw}"
            img2 = f"https://www.pexels.com/search/{kw.replace('+', '%20')}/"
            post_buffer.append(f"")
            post_buffer.append(f"[IMAGES]")
            post_buffer.append(f"Unsplash: {img1}")
            post_buffer.append(f"Pexels:   {img2}")
            post_buffer.append(f"{'='*50}")
            output.extend(post_buffer)
            post_buffer = []
            keywords_line = ""
        elif line.strip().startswith("POST "):
            if post_buffer:
                output.extend(post_buffer)
                post_buffer = []
            post_buffer.append(line)
        else:
            post_buffer.append(line)

    if post_buffer:
        output.extend(post_buffer)

    return "\n".join(output)

# --- SEND EMAIL ---
def send_email(threads_content):
    clean_content = safe_encode(threads_content)

    msg = MIMEMultipart()
    msg["Subject"] = "Threads Report"
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg["Message-ID"] = email.utils.make_msgid()

    msg.attach(MIMEText(clean_content, "plain", "us-ascii"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.ehlo()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, TO_EMAIL, msg.as_bytes())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Critical email error: {e}")
        raise e

# --- MAIN ---
if __name__ == "__main__":
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("Error: Missing Gmail credentials.")
        exit(1)

    articles = fetch_articles()
    if not articles:
        print("No articles fetched.")
        exit(0)

    threads = generate_threads(articles)

    if threads:
        final_content = inject_image_links(threads)
        send_email(final_content)
    else:
        print("Total generation failure.")
        exit(1)

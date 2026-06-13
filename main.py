import os
import smtplib
import requests
import time
import email.utils
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- UTILS POUR LE NETTOYAGE ---
def safe_encode(text):
    """Force la conversion en ASCII pur pour éviter les erreurs d'encodage SMTP."""
    if not isinstance(text, str):
        text = str(text)
    return "".join(char for char in text if ord(char) < 128)

# --- CONFIG ---
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
                    # Nettoyage à la source
                    title = safe_encode(a.get('title', ''))
                    desc = safe_encode(a.get('description', ''))
                    articles.append(f"- {title}: {desc}")
        except Exception as e:
            print(f"Erreur lors de la récupération des news pour {topic}: {e}")
    return "\n".join(articles[:9])

# --- GENERATE THREADS ---
def generate_threads(articles_text):
    prompt = f"""Tu es un créateur de contenu tech/cybersec francophone.
À partir de ces actualités, génère exactement 3 threads Twitter/Threads en français.
Chaque thread = 5 tweets max, percutants, informatifs, ton humain pas corporate.
Format :

THREAD 1 — [Sujet]
1/
2/
3/
...

Actualités :
{articles_text}
"""
    
    models_to_try = [
        "openrouter/free",
        "deepseek/deepseek-chat-v3-0324:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "qwen/qwen3-coder:free"
    ]
    
    for model in models_to_try:
        print(f"Tentative de génération avec le modèle : {model}...")
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
                print(f"✅ Succès avec {model} !")
                return data["choices"][0]["message"]["content"]
            
            print(f"⚠️ Échec avec {model} : {data.get('error', {}).get('message', 'Erreur inconnue')}")
            time.sleep(3) 
            
        except Exception as e:
            print(f"❌ Erreur réseau avec {model} : {e}")
            time.sleep(3)
            
    return None

# --- SEND EMAIL ---
def send_email(threads_content):
    # Nettoyage radical final
    clean_content = safe_encode(threads_content)

    msg = MIMEMultipart()
    msg["Subject"] = "Threads Report"
    msg["From"] = GMAIL_USER
    msg["To"] = TO_EMAIL
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg["Message-ID"] = email.utils.make_msgid()

    # Utilisation explicite de us-ascii
    msg.attach(MIMEText(clean_content, "plain", "us-ascii"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.ehlo()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            # Envoi des bytes pour contourner les codecs Python
            server.sendmail(GMAIL_USER, TO_EMAIL, msg.as_bytes())
        print("✅ Email envoyé avec succès.")
    except Exception as e:
        print(f"❌ Erreur critique lors de l'envoi email : {e}")
        raise e

# --- MAIN ---
if __name__ == "__main__":
    articles = fetch_articles()
    if not articles:
        print("No articles fetched.")
        exit(0)
        
    threads = generate_threads(articles)
    
    if threads:
        send_email(threads)
    else:
        print("❌ Échec de la génération.")
        exit(1)

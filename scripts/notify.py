import os
import sys
import json
import requests

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "notify_config.json")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "ntfy_topic": "hung-daily-intel-melbourne",  # Replace with custom secret topic
        "dashboard_url": "https://your-github-username.github.io/daily-intel", # Or local/tunnel link
        "telegram_bot_token": "",
        "telegram_chat_id": "",
        "discord_webhook_url": ""
    }

def send_ntfy(title, message, click_url=None, topic=None):
    cfg = load_config()
    target_topic = topic or cfg.get("ntfy_topic")
    if not target_topic:
        return False
    
    url = f"https://ntfy.sh/{target_topic}"
    headers = {
        "Title": title.encode("utf-8"),
        "Priority": "high",
        "Tags": "briefcase,newspaper,chart_with_upwards_trend"
    }
    if click_url or cfg.get("dashboard_url"):
        headers["Click"] = click_url or cfg.get("dashboard_url")
    
    try:
        resp = requests.post(url, data=message.encode("utf-8"), headers=headers, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"ntfy error: {e}")
        return False

def send_telegram(message):
    cfg = load_config()
    token = cfg.get("telegram_bot_token")
    chat_id = cfg.get("telegram_chat_id")
    if not token or not chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

if __name__ == "__main__":
    test_title = "🌅 Daily Intelligence Briefing Ready"
    test_msg = "Top radar: IMF Outlook, Tô Lâm Đan Mạch FTA, Nobel Optogenetics. Tap to open dashboard."
    print("Testing notifications...")
    cfg = load_config()
    print(f"Config topic: {cfg.get('ntfy_topic')}")
    success = send_ntfy(test_title, test_msg)
    print(f"ntfy dispatched: {success}")

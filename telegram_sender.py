import httpx
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


async def send_message(text: str) -> bool:
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        response = r.json()

    if response.get("ok"):
        print("[Telegram] Message sent successfully")
        return True
    else:
        print(f"[Telegram] Failed: {response}")
        return False
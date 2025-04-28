import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import logging
import sys

# Konfigurasi logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Starting script at " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Muat variabel lingkungan dari file .env
load_dotenv()

# Konstanta dari .env
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Pastikan sudah ada di .env

# Gunakan file id.json yang dibuat di folder kerja oleh GitHub Actions
SENT_IDS_FILE = "id.json"

def get_notion_data():
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        notion_data = response.json()
        return notion_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in Notion request: {e}")
        return None

def send_to_telegram(chat_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Message sent to {chat_id}: {message}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error in sending message to {chat_id}: {e}")

def read_sent_ids():
    try:
        if os.path.exists(SENT_IDS_FILE):
            with open(SENT_IDS_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error reading sent IDs file: {e}")
    return []

def save_sent_ids(sent_ids):
    try:
        with open(SENT_IDS_FILE, "w") as f:
            json.dump(sent_ids, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving sent IDs file: {e}")

def main():
    notion_data = get_notion_data()
    if notion_data is None:
        logger.error("Failed to retrieve data from Notion.")
        sys.exit(1)

    results = notion_data.get("results", [])
    if not results:
        logger.info("No results found in Notion database.")
        sys.exit(0)  # Bukan error, hanya tidak ada data

    sent_ids = read_sent_ids()

    for item in results:
        properties = item.get("properties", {})

        id_pesanan = properties.get("- Id Pesanan", {}).get("rich_text", [])
        pelanggan = properties.get("- Pelanggan", {}).get("rich_text", [])
        admin_sales = properties.get("- Admin Sales", {}).get("rich_text", [])

        id_pesanan_value = id_pesanan[0]["text"]["content"] if id_pesanan else None
        pelanggan_value = pelanggan[0]["text"]["content"] if pelanggan else "Tidak ada data"
        admin_sales_value = admin_sales[0]["text"]["content"] if admin_sales else "Tidak ada data"

        if id_pesanan_value and id_pesanan_value not in sent_ids:
            message = (
                f"📌 *ID Pesanan:* {id_pesanan_value}\n"
                f"👤 *Pelanggan:* {pelanggan_value}\n"
                f"🧑‍💼 *Admin Sales:* {admin_sales_value}\n\n"
                f"📅 *Waktu:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            send_to_telegram(TELEGRAM_CHAT_ID, message)
            sent_ids.append(id_pesanan_value)
            save_sent_ids(sent_ids)

    sys.exit(0)  # Exit dengan sukses

if __name__ == "__main__":
    main()

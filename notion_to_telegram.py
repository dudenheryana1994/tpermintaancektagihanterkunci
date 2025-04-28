import requests
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import logging

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
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Tambahkan ini ke .env
SENT_IDS_FILE = "/Users/mac/Documents/kreasi-integrasi-01/id.json"

# --- Fungsi untuk mengambil data dari Notion ---
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

# --- Fungsi untuk mengirim pesan ke Telegram ---
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

# --- Fungsi untuk membaca file ID yang sudah dikirim ---
def read_sent_ids():
    if os.path.exists(SENT_IDS_FILE):
        with open(SENT_IDS_FILE, "r") as f:
            return json.load(f)
    return []  # Jika file tidak ada, kembalikan list kosong

# --- Fungsi untuk menyimpan ID yang sudah terkirim ---
def save_sent_ids(sent_ids):
    with open(SENT_IDS_FILE, "w") as f:
        json.dump(sent_ids, f, indent=4)

# --- Program Utama ---
def main():
    notion_data = get_notion_data()
    if notion_data is None:
        logger.error("Failed to retrieve data from Notion.")
        return

    results = notion_data.get("results", [])
    if not results:
        logger.error("No results found in Notion database.")
        return

    sent_ids = read_sent_ids()  # Baca ID yang sudah dikirim

    for item in results:
        properties = item.get("properties", {})

        # Ambil data yang dibutuhkan
        id_pesanan = properties.get("- Id Pesanan", {}).get("rich_text", [])
        pelanggan = properties.get("- Pelanggan", {}).get("rich_text", [])
        admin_sales = properties.get("- Admin Sales", {}).get("rich_text", [])

        if id_pesanan:
            id_pesanan_value = id_pesanan[0]["text"]["content"]
        else:
            id_pesanan_value = None

        if pelanggan:
            pelanggan_value = pelanggan[0]["text"]["content"]
        else:
            pelanggan_value = "Tidak ada data"

        if admin_sales:
            admin_sales_value = admin_sales[0]["text"]["content"]
        else:
            admin_sales_value = "Tidak ada data"

        # Pastikan ID Pesanan tersedia dan belum dikirim sebelumnya
        if id_pesanan_value and id_pesanan_value not in sent_ids:
            message = (
                f"📌 *ID Pesanan:* {id_pesanan_value}\n"
                f"👤 *Pelanggan:* {pelanggan_value}\n"
                f"🧑‍💼 *Admin Sales:* {admin_sales_value}\n\n"
                f"📅 *Waktu:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            send_to_telegram(TELEGRAM_CHAT_ID, message)
            sent_ids.append(id_pesanan_value)  # Tambahkan ke daftar yang sudah dikirim
            save_sent_ids(sent_ids)  # Simpan perubahan

if __name__ == "__main__":
    main()
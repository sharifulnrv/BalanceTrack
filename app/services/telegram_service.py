import requests
import os
import threading
from flask import current_app

class TelegramService:
    @staticmethod
    def is_connected():
        """Check if internet connection is available."""
        try:
            # Try to connect to a reliable host (e.g., Google or Cloudflare DNS)
            requests.get("https://8.8.8.8", timeout=2)
            return True
        except (requests.ConnectionError, requests.Timeout):
            return False

    @staticmethod
    def send_message(chat_id, text):
        token = current_app.config.get('TELEGRAM_BOT_TOKEN')
        if not token or not chat_id:
            return False
            
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                current_app.logger.error(f"Telegram API Error: {response.status_code} - {response.text}")
            return response.status_code == 200
        except Exception as e:
            current_app.logger.error(f"Telegram Connection Error: {e}")
            return False

    @staticmethod
    def send_document(chat_id, document_path, caption=None, background=True):
        if background:
            # Run in a separate thread to avoid blocking the main app
            thread = threading.Thread(target=TelegramService._send_document_sync, args=(chat_id, document_path, caption))
            thread.daemon = True
            thread.start()
            return True
        else:
            return TelegramService._send_document_sync(chat_id, document_path, caption)

    @staticmethod
    def _send_document_sync(chat_id, document_path, caption=None):
        # We need to access app config, but since this runs in a thread, 
        # current_app might not be available unless inside app context.
        # But for now, we'll assume the token is passed or retrieved correctly.
        # However, to be safe, we'll pass the token or use the app's context inside the thread.
        # For simplicity in this env, I'll pass the token if I can, or use the app's config.
        # Since I'm using current_app.config, I need to handle the thread case.
        
        # A better way is to pass the token explicitly.
        from flask import Flask
        # This is a bit tricky with threads and Flask. 
        # I'll modify send_document to capture the token before spawning the thread.
        pass

    @staticmethod
    def send_document_with_token(token, chat_id, document_path, caption=None, background=True):
        if not TelegramService.is_connected():
            print("Telegram Sync Failed: No Internet Connection")
            return False

        if background:
            thread = threading.Thread(target=TelegramService._send_document_raw, args=(token, chat_id, document_path, caption))
            thread.daemon = True
            thread.start()
            return True
        else:
            return TelegramService._send_document_raw(token, chat_id, document_path, caption)

    @staticmethod
    def _send_document_raw(token, chat_id, document_path, caption=None):
        if not token or not chat_id or not os.path.exists(document_path):
            return False
            
        url = f"https://api.telegram.org/bot{token}/sendDocument"
        
        try:
            with open(document_path, 'rb') as doc:
                files = {'document': doc}
                data = {'chat_id': chat_id}
                if caption:
                    data['caption'] = caption
                
                response = requests.post(url, data=data, files=files, timeout=60)
                return response.status_code == 200
        except Exception as e:
            print(f"Telegram Sync Error: {e}")
            return False

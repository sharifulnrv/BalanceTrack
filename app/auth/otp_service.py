import random
import string
import requests
from datetime import datetime, timedelta, UTC
from hashlib import sha256
from flask import current_app
from app import db
from app.models import OTPLog, User

class OTPService:
    @staticmethod
    def generate_otp(length=6):
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    def hash_otp(otp):
        return sha256(otp.encode()).hexdigest()

    @staticmethod
    def send_telegram_otp(chat_id, otp):
        token = current_app.config['TELEGRAM_BOT_TOKEN']
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        message = f"Your Personal Finance App OTP is: {otp}\nExpires in {current_app.config['OTP_EXPIRY_MINUTES']} minutes."
        
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            current_app.logger.error(f"Telegram API Error: {e}")
            return False

    @staticmethod
    def create_otp_for_user(user):
        # Invalidate old OTPs
        OTPLog.query.filter_by(user_id=user.id, is_used=False).update({"is_used": True})
        
        otp = OTPService.generate_otp()
        otp_hash = OTPService.hash_otp(otp)
        expiry = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=current_app.config['OTP_EXPIRY_MINUTES'])
        
        otp_log = OTPLog(
            user_id=user.id,
            otp_hash=otp_hash,
            expires_at=expiry
        )
        db.session.add(otp_log)
        db.session.commit()
        
        if OTPService.send_telegram_otp(user.telegram_chat_id, otp):
            return True
        return False

    @staticmethod
    def verify_otp(user_id, otp):
        otp_hash = OTPService.hash_otp(otp)
        otp_log = OTPLog.query.filter_by(
            user_id=user_id,
            otp_hash=otp_hash,
            is_used=False
        ).first()
        
        if not otp_log:
            # Increment retry count for the latest active OTP
            latest = OTPLog.query.filter_by(user_id=user_id, is_used=False).order_by(OTPLog.created_at.desc()).first()
            if latest:
                latest.retry_count += 1
                if latest.retry_count >= current_app.config['MAX_OTP_RETRIES']:
                    latest.is_used = True
                db.session.commit()
            return False, "Invalid OTP."

        if otp_log.expires_at < datetime.now(UTC).replace(tzinfo=None):
            otp_log.is_used = True
            db.session.commit()
            return False, "OTP has expired."

        if otp_log.retry_count >= current_app.config['MAX_OTP_RETRIES']:
            otp_log.is_used = True
            db.session.commit()
            return False, "Maximum retries exceeded."

        otp_log.is_used = True
        db.session.commit()
        return True, "Verification successful."

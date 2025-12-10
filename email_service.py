import os
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# OAuth credentials (из переменных окружения)
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')

YANDEX_CLIENT_ID = os.getenv('YANDEX_CLIENT_ID')
YANDEX_CLIENT_SECRET = os.getenv('YANDEX_CLIENT_SECRET')
YANDEX_REDIRECT_URI = os.getenv('YANDEX_REDIRECT_URI')

MAILRU_CLIENT_ID = os.getenv('MAILRU_CLIENT_ID')
MAILRU_CLIENT_SECRET = os.getenv('MAILRU_CLIENT_SECRET')
MAILRU_REDIRECT_URI = os.getenv('MAILRU_REDIRECT_URI')

BACKEND_URL = os.getenv('WEBAPP_URL', 'http://localhost:8000')


def get_oauth_url(provider: str, state: str = None) -> str:
    """Получить URL для OAuth авторизации"""
    
    # ВАЖНО: state должен быть передан!
    if not state:
        state = 'default_user'
    
    if provider == 'google':
        return (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={GOOGLE_CLIENT_ID}&"
            f"redirect_uri={GOOGLE_REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=https://www.googleapis.com/auth/gmail.send&"
            f"access_type=offline&"
            f"state={state}&"
            f"prompt=consent"
        )
    
    elif provider == 'yandex':
        return (
            f"https://oauth.yandex.ru/authorize?"
            f"client_id={YANDEX_CLIENT_ID}&"
            f"redirect_uri={YANDEX_REDIRECT_URI}&"
            f"response_type=code&"
            f"state={state}&"
            f"force_confirm=yes"
        )
    
    elif provider == 'mailru':
        return (
            f"https://oauth.mail.ru/login?"
            f"client_id={MAILRU_CLIENT_ID}&"
            f"redirect_uri={MAILRU_REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=userinfo mail.imap&"
            f"state={state}"
        )
    
    raise ValueError(f"Неизвестный провайдер: {provider}")


async def exchange_code_for_token(provider: str, code: str) -> Dict[str, Any]:
    """Обмен authorization code на access token"""
    
    if provider == 'google':
        url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
    
    elif provider == 'yandex':
        url = "https://oauth.yandex.ru/token"
        data = {
            "code": code,
            "client_id": YANDEX_CLIENT_ID,
            "client_secret": YANDEX_CLIENT_SECRET,
            "grant_type": "authorization_code"
        }
    
    elif provider == 'mailru':
        url = "https://oauth.mail.ru/token"
        data = {
            "code": code,
            "client_id": MAILRU_CLIENT_ID,
            "client_secret": MAILRU_CLIENT_SECRET,
            "redirect_uri": MAILRU_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
    
    else:
        raise ValueError(f"Неизвестный провайдер: {provider}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, data=data)
        response.raise_for_status()
        return response.json()


async def get_user_email(provider: str, access_token: str) -> str:
    """Получить email пользователя"""
    
    if provider == 'google':
        url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            data = response.json()
            return data.get('email', '')
    
    elif provider == 'yandex':
        url = "https://login.yandex.ru/info"
        headers = {"Authorization": f"OAuth {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            data = response.json()
            return data.get('default_email', '')
    
    elif provider == 'mailru':
        # Mail.ru API для получения email
        url = "https://oauth.mail.ru/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            data = response.json()
            return data.get('email', '')
    
    return ""


async def send_email_via_oauth(
    provider: str,
    access_token: str,
    from_email: str,
    to_email: str,
    subject: str,
    body: str
) -> Dict[str, Any]:
    """Отправка письма через OAuth"""
    
    if provider == 'google':
        # Создаём MIME сообщение
        message = MIMEMultipart()
        message['From'] = from_email
        message['To'] = to_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Кодируем в base64
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Отправляем через Gmail API
        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {"raw": raw_message}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            return {"status": "success" if response.status_code == 200 else "error", "data": response.json()}
    
    elif provider == 'yandex':
        # Яндекс использует SMTP с OAuth
        return {"status": "error", "message": "Yandex SMTP требует дополнительной настройки"}
    
    elif provider == 'mailru':
        # Mail.ru также через SMTP
        return {"status": "error", "message": "Mail.ru SMTP требует дополнительной настройки"}
    
    return {"status": "error", "message": "Неизвестный провайдер"}
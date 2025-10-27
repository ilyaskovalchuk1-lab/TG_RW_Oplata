# -*- coding: utf-8 -*-
import os
import sys
import requests
import json
from flask import Flask, request

# РќР°СЃС‚СЂРѕР№РєР° РєРѕРґРёСЂРѕРІРєРё РґР»СЏ Python
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

app = Flask(__name__)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7250152884:AAGjSx9ppNaa_JlLPNKfwzUVYUJw8RofbkE")
if not TOKEN:
    raise RuntimeError("Environment variable TELEGRAM_BOT_TOKEN is not set")

# РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ РґР»СЏ epay API
EPAY_API_URL = os.getenv("EPAY_API_URL", "https://marketplay.info/api/request/requisites")
EPAY_API_KEY = os.getenv("EPAY_API_KEY", "754fc9b3bb03cb719d76a18d8c83dcfd2d7758bc595585002c10355a415143d9")
BASE_URL = os.getenv("BASE_URL", "https://web-production-f0a3.up.railway.app")

@app.route("/")
def index():
    return "Бот работает! Версия Railway - Исправлен EPay API"

@app.route("/callback", methods=["POST"])
def epay_callback():
    try:
        update = request.get_json(silent=True) or {}
        app.logger.info(f"EPay callback received: {update}")
        
        if update.get('status') == 'successful_payment':
            transaction_id = update.get('transaction_id')
            if transaction_id:
                handle_successful_payment(transaction_id)
            return 'success', 200
        else:
            return 'fail', 200
            
    except Exception as e:
        app.logger.error(f"Error processing epay callback: {e}")
        return 'fail', 500

@app.route("/success")
def payment_success():
    return "РџР»Р°С‚РµР¶ СѓСЃРїРµС€РЅРѕ РѕР±СЂР°Р±РѕС‚Р°РЅ!"

@app.route("/fail")
def payment_fail():
    return "РћС€РёР±РєР° РѕР±СЂР°Р±РѕС‚РєРё РїР»Р°С‚РµР¶Р°!"

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    # РџСЂРѕСЃС‚РѕРµ Р»РѕРіРёСЂРѕРІР°РЅРёРµ РґР»СЏ РґРёР°РіРЅРѕСЃС‚РёРєРё
    print("=== WEBHOOK CALLED ===")
    app.logger.info("=== WEBHOOK CALLED ===")
    
    update = request.get_json(silent=True) or {}
    print(f"Update: {update}")
    app.logger.info(f"Update: {update}")
    
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = message.get("text")

    print(f"Chat ID: {chat_id}, Text: {text}")
    app.logger.info(f"Chat ID: {chat_id}, Text: {text}")

    if not (chat_id and text):
        print("No chat_id or text, ignoring")
        app.logger.info("No chat_id or text, ignoring")
        return "ignored", 200

    try:
        if text.startswith('/'):
            print(f"Handling command: {text}")
            app.logger.info(f"Handling command: {text}")
            handle_command(chat_id, text)
        else:
            print(f"Handling amount input: {text}")
            app.logger.info(f"Handling amount input: {text}")
            handle_amount_input(chat_id, text)
    except Exception as e:
        print(f"Exception in webhook: {e}")
        app.logger.exception("Failed to send message")

    return "ok", 200

def handle_command(chat_id, command):
    print(f"Command handler: {command}")
    app.logger.info(f"Command handler: {command}")
    
    if command == '/start':
        print("Sending start message")
        app.logger.info("Sending start message")
        send_message(chat_id, "Укажите необходимую сумму оплаты в руб.:")
    
    elif command == '/payment':
        print("Sending payment message")
        app.logger.info("Sending payment message")
        try:
            payment_data = get_payment_credentials_from_epay()
            if payment_data:
                payment_text = format_payment_credentials(payment_data)
            else:
                payment_text = get_static_payment_credentials()
            
            send_message(chat_id, payment_text)
        except Exception as e:
            app.logger.error(f"Error getting payment credentials: {e}")
            send_message(chat_id, get_static_payment_credentials())
    
    elif command == '/help':
        print("Sending help message")
        app.logger.info("Sending help message")
        help_text = """РџРћРњРћР©Р¬:

/payment - РџРѕР»СѓС‡РёС‚СЊ РІСЃРµ РґРѕСЃС‚СѓРїРЅС‹Рµ СЂРµРєРІРёР·РёС‚С‹ РґР»СЏ РѕРїР»Р°С‚С‹
/start - РќР°С‡Р°С‚СЊ СЂР°Р±РѕС‚Сѓ СЃ Р±РѕС‚РѕРј
/help - РџРѕРєР°Р·Р°С‚СЊ СЌС‚Рѕ СЃРѕРѕР±С‰РµРЅРёРµ

Р•СЃР»Рё Сѓ РІР°СЃ РµСЃС‚СЊ РІРѕРїСЂРѕСЃС‹, РѕР±СЂР°С‚РёС‚РµСЃСЊ Рє Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂСѓ."""
        send_message(chat_id, help_text)
    
    else:
        print("Unknown command")
        app.logger.info("Unknown command")
        send_message(chat_id, "РќРµРёР·РІРµСЃС‚РЅР°СЏ РєРѕРјР°РЅРґР°. РСЃРїРѕР»СЊР·СѓР№С‚Рµ /help РґР»СЏ СЃРїРёСЃРєР° РєРѕРјР°РЅРґ.")

def handle_amount_input(chat_id, amount_text):
    print(f"Amount input handler: {amount_text}")
    app.logger.info(f"Amount input handler: {amount_text}")
    
    try:
        amount = float(amount_text.replace(',', '.'))
        send_message(chat_id, "РћР¶РёРґР°РµРј СЂРµРєРІРёР·РёС‚С‹...")
        
        payment_data = get_payment_credentials_from_epay(amount)
        
        if payment_data and not payment_data.get('error_desc'):
            save_order_to_file(payment_data, chat_id, amount)
            payment_text = format_payment_credentials_from_epay(payment_data)
            send_message(chat_id, payment_text)
            send_message(chat_id, "РќР° РѕРїР»Р°С‚Сѓ РґР°РµС‚СЃСЏ 20 РјРёРЅСѓС‚, РїРѕСЃР»Рµ С‡РµРіРѕ СЃСЃС‹Р»РєР° Р±СѓРґРµС‚ РЅРµР°РєС‚РёРІРЅР°")
        else:
            error_msg = payment_data.get('error_desc', 'РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ СЂРµРєРІРёР·РёС‚РѕРІ') if payment_data else 'РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ СЂРµРєРІРёР·РёС‚РѕРІ'
            send_message(chat_id, f"РћС€РёР±РєР°! {error_msg}")
            
    except ValueError:
        send_message(chat_id, "РџРѕР¶Р°Р»СѓР№СЃС‚Р°, РІРІРµРґРёС‚Рµ РєРѕСЂСЂРµРєС‚РЅСѓСЋ СЃСѓРјРјСѓ (РЅР°РїСЂРёРјРµСЂ: 1000 РёР»Рё 1000.50)")
    except Exception as e:
        app.logger.error(f"Error handling amount input: {e}")
        send_message(chat_id, "РџСЂРѕРёР·РѕС€Р»Р° РѕС€РёР±РєР°. РџРѕРїСЂРѕР±СѓР№С‚Рµ РµС‰Рµ СЂР°Р·.")

def send_message(chat_id, text):
    print(f"Sending message to {chat_id}: {text}")
    app.logger.info(f"Sending message to {chat_id}: {text}")
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    data = {
        "chat_id": chat_id, 
        "text": text
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"Telegram API response: {response.status_code}")
        app.logger.info(f"Telegram API response: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Telegram API error: {response.text}")
            app.logger.error(f"Telegram API error: {response.text}")
    except Exception as e:
        print(f"Error sending message: {e}")
        app.logger.error(f"Error sending message: {e}")

def save_order_to_file(payment_data, chat_id, amount):
    try:
        from datetime import datetime
        order_data = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            payment_data.get('order_id', 'N/A'),
            str(chat_id),
            str(amount)
        ]
        
        with open("orders.txt", "a", encoding="utf-8") as f:
            f.write("|".join(order_data) + "\n")
            
    except Exception as e:
        app.logger.error(f"Error saving order to file: {e}")

def get_payment_credentials_from_epay(amount=None):
    if not EPAY_API_KEY:
        app.logger.warning("EPAY API key not configured")
        return None
    
    try:
        data = {
            'amount': str(amount) if amount else '1000',
            'merchant_order_id': 'optional',
            'api_key': EPAY_API_KEY,
            'notice_url': f"{BASE_URL}/callback"
        }
        
        response = requests.post(EPAY_API_URL, data=data, timeout=30)
        app.logger.info(f"EPay API response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            app.logger.error(f"EPAY API error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        app.logger.error(f"EPAY API request failed: {e}")
        return None

def format_payment_credentials_from_epay(payment_data):
    try:
        order_id = payment_data.get('order_id', 'N/A')
        amount = payment_data.get('amount', 'N/A')
        
        receiver_wallet_str = ""
        
        if payment_data.get('card_number'):
            receiver_wallet_str = f"РќРѕРјРµСЂ РєР°СЂС‚С‹ РґР»СЏ РѕРїР»Р°С‚С‹: {payment_data['card_number']}"
        elif payment_data.get('qr_sbp_url') or payment_data.get('card_form_url'):
            url = payment_data.get('qr_sbp_url') or payment_data.get('card_form_url')
            receiver_wallet_str = f"РЎСЃС‹Р»РєР° РЅР° РѕРїР»Р°С‚Сѓ: {url}"
        
        text = f"РЎРѕР·РґР°РЅ Р·Р°РєР°Р·: в„–{order_id}\n\n"
        text += f"{receiver_wallet_str}\n"
        text += f"РЎСѓРјРјР° РїР»Р°С‚РµР¶Р°: {amount} в‚Ѕ\n\n"
        text += f"Р’СЂРµРјСЏ РЅР° РѕРїР»Р°С‚Сѓ: 20 РјРёРЅ"
        
        return text
        
    except Exception as e:
        app.logger.error(f"Error formatting payment data: {e}")
        return "РћС€РёР±РєР° С„РѕСЂРјР°С‚РёСЂРѕРІР°РЅРёСЏ РґР°РЅРЅС‹С…"

def handle_successful_payment(transaction_id):
    try:
        orders_file = "orders.txt"
        
        if os.path.exists(orders_file):
            with open(orders_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                parts = line.strip().split('|')
                if len(parts) >= 4 and int(parts[1]) == int(transaction_id):
                    chat_id = int(parts[2])
                    send_message(chat_id, f'РџРѕР»СѓС‡РµРЅР° РѕРїР»Р°С‚Р° РїРѕ Р·Р°РєР°Р·Сѓ {transaction_id}!')
                    break
                    
    except Exception as e:
        app.logger.error(f"Error handling successful payment: {e}")

def get_static_payment_credentials():
    return """Р Р•РљР’РР—РРўР« Р”Р›РЇ РћРџР›РђРўР«:

Р‘Р°РЅРєРѕРІСЃРєР°СЏ РєР°СЂС‚Р°:
вЂў РќРѕРјРµСЂ: 1234 5678 9012 3456
вЂў РЎСЂРѕРє РґРµР№СЃС‚РІРёСЏ: 12/25
вЂў CVV: 123
вЂў РРјСЏ РґРµСЂР¶Р°С‚РµР»СЏ: IVAN IVANOV

РљСЂРёРїС‚РѕРІР°Р»СЋС‚Р°:
вЂў Bitcoin (BTC): bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
вЂў Ethereum (ETH): 0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6

Р­Р»РµРєС‚СЂРѕРЅРЅС‹Рµ РєРѕС€РµР»СЊРєРё:
вЂў PayPal: payment@example.com
вЂў WebMoney: R123456789012

Р’РЅРёРјР°РЅРёРµ: РџСЂРѕРІРµСЂСЏР№С‚Рµ СЂРµРєРІРёР·РёС‚С‹ РїРµСЂРµРґ РѕРїР»Р°С‚РѕР№!"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

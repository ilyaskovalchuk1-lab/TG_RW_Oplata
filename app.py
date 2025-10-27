# -*- coding: utf-8 -*-
import os
import sys
import requests
import json
from flask import Flask, request

# Настройка кодировки для Railway
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

app = Flask(__name__)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Environment variable TELEGRAM_BOT_TOKEN is not set")

# Конфигурация для epay API
EPAY_API_URL = os.getenv("EPAY_API_URL", "https://infopayments.click/api/request/requisites")
EPAY_API_KEY = os.getenv("EPAY_API_KEY", "754fc9b3bb03cb719d76a18d8c83dcfd2d7758bc595585002c10355a415143d9")
BASE_URL = os.getenv("BASE_URL", "https://your-app-name.up.railway.app")

@app.route("/")
def index():
    return "Бот работает! Версия Railway - Русский язык с полным функционалом"

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
    return "Платеж успешно обработан!"

@app.route("/fail")
def payment_fail():
    return "Ошибка обработки платежа!"

@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
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
        send_message(chat_id, "Введите точную сумму")
    
    elif command == '/payment':
        print("Sending payment message")
        app.logger.info("Sending payment message")
        try:
            payment_data = get_payment_credentials_from_epay()
            if payment_data:
                payment_text = format_payment_credentials_from_epay(payment_data)
            else:
                payment_text = get_static_payment_credentials()
            
            send_message(chat_id, payment_text)
        except Exception as e:
            app.logger.error(f"Error getting payment credentials: {e}")
            send_message(chat_id, get_static_payment_credentials())
    
    elif command == '/help':
        print("Sending help message")
        app.logger.info("Sending help message")
        help_text = """❓ ПОМОЩЬ:

/payment - Получить все доступные реквизиты для оплаты
/start - Начать работу с ботом
/help - Показать это сообщение

Если у вас есть вопросы, обратитесь к администратору."""
        send_message(chat_id, help_text)
    
    else:
        print("Unknown command")
        app.logger.info("Unknown command")
        send_message(chat_id, "❌ Неизвестная команда. Используйте /help для списка команд.")

def handle_amount_input(chat_id, amount_text):
    print(f"Amount input handler: {amount_text}")
    app.logger.info(f"Amount input handler: {amount_text}")
    
    try:
        amount = float(amount_text.replace(',', '.'))
        send_message(chat_id, "⏳ Ожидаем реквизиты...")
        
        payment_data = get_payment_credentials_from_epay(amount)
        
        if payment_data and not payment_data.get('error_desc'):
            save_order_to_file(payment_data, chat_id, amount)
            payment_text = format_payment_credentials_from_epay(payment_data)
            send_message(chat_id, payment_text)
            send_message(chat_id, "⏰ На оплату дается 20 минут, после чего ссылка будет неактивна")
        else:
            error_msg = payment_data.get('error_desc', 'Ошибка получения реквизитов') if payment_data else 'Ошибка получения реквизитов'
            send_message(chat_id, f"❌ Ошибка! {error_msg}")
            
    except ValueError:
        send_message(chat_id, "❌ Пожалуйста, введите корректную сумму (например: 1000 или 1000.50)")
    except Exception as e:
        app.logger.error(f"Error handling amount input: {e}")
        send_message(chat_id, "❌ Произошла ошибка. Попробуйте еще раз.")

def send_message(chat_id, text):
    print(f"Sending message to {chat_id}: {text}")
    app.logger.info(f"Sending message to {chat_id}: {text}")
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    data = {
        "chat_id": chat_id, 
        "text": text,
        "parse_mode": "HTML"
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
            'notice_url': f"{BASE_URL}/callback",
            'success_url': f"{BASE_URL}/success",
            'fail_url': f"{BASE_URL}/fail"
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
            receiver_wallet_str = f"<b>Номер карты для оплаты</b>: <code>{payment_data['card_number']}</code>"
        elif payment_data.get('qr_sbp_url') or payment_data.get('card_form_url'):
            url = payment_data.get('qr_sbp_url') or payment_data.get('card_form_url')
            receiver_wallet_str = f"<b>Ссылка на оплату</b>: <a href='{url}'>{url}</a>"
        
        text = f"📄 <b>Создан заказ</b>: №{order_id}\n\n"
        text += f"💳 {receiver_wallet_str}\n"
        text += f"💰 <b>Сумма платежа</b>: <code>{amount}</code> ₽\n\n"
        text += f"⏰ <b>Время на оплату</b>: 20 мин"
        
        return text
        
    except Exception as e:
        app.logger.error(f"Error formatting payment data: {e}")
        return "❌ Ошибка форматирования данных"

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
                    send_message(chat_id, f'✅ Получена оплата по заказу {transaction_id}!')
                    break
                    
    except Exception as e:
        app.logger.error(f"Error handling successful payment: {e}")

def get_static_payment_credentials():
    return """<b>💳 РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ:</b>

<b>🏦 Банковская карта:</b>
• Номер: <code>1234 5678 9012 3456</code>
• Срок действия: <code>12/25</code>
• CVV: <code>123</code>
• Имя держателя: <code>IVAN IVANOV</code>

<b>💰 Криптовалюта:</b>
• Bitcoin (BTC): <code>bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh</code>
• Ethereum (ETH): <code>0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6</code>

<b>📱 Электронные кошельки:</b>
• PayPal: <code>payment@example.com</code>
• WebMoney: <code>R123456789012</code>

⚠️ <b>Внимание</b>: Проверяйте реквизиты перед оплатой!"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
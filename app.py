# -*- coding: utf-8 -*-
import os
import sys
import requests
import json
import time
import logging
from flask import Flask, request

# Настройка кодировки для Railway
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Environment variable TELEGRAM_BOT_TOKEN is not set")

# Конфигурация для epay API
EPAY_API_URL = os.getenv("EPAY_API_URL", "https://marketplay.info/api/request/requisites")
EPAY_API_KEY = os.getenv("EPAY_API_KEY", "754fc9b3bb03cb719d76a18d8c83dcfd2d7758bc595585002c10355a415143d9")
BASE_URL = os.getenv("BASE_URL", "https://web-production-f0a3.up.railway.app")

@app.route("/")
def index():
    return "Бот работает! Версия Railway - ИСПРАВЛЕНА ОТПРАВКА РЕКВИЗИТОВ - " + str(int(time.time()))

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
        send_message(chat_id, "\u0423\u043a\u0430\u0436\u0438\u0442\u0435 \u043d\u0435\u043e\u0431\u0445\u043e\u0434\u0438\u043c\u0443\u044e \u0441\u0443\u043c\u043c\u0443 \u043e\u043f\u043b\u0430\u0442\u044b \u0432 \u0440\u0443\u0431. (\u043c\u0438\u043d\u0438\u043c\u0443\u043c 1500 \u0440\u0443\u0431.):")
    
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
        help_text = """\u2753 \u041f\u041e\u041c\u041e\u0429\u042c:

/payment - \u041f\u043e\u043b\u0443\u0447\u0438\u0442\u044c \u0432\u0441\u0435 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0435 \u0440\u0435\u043a\u0432\u0438\u0437\u0438\u0442\u044b \u0434\u043b\u044f \u043e\u043f\u043b\u0430\u0442\u044b
/start - \u041d\u0430\u0447\u0430\u0442\u044c \u0440\u0430\u0431\u043e\u0442\u0443 \u0441 \u0431\u043e\u0442\u043e\u043c
/help - \u041f\u043e\u043a\u0430\u0437\u0430\u0442\u044c \u044d\u0442\u043e \u0441\u043e\u043e\u0431\u0449\u0435\u043d\u0438\u0435

\u0415\u0441\u043b\u0438 \u0443 \u0432\u0430\u0441 \u0435\u0441\u0442\u044c \u0432\u043e\u043f\u0440\u043e\u0441\u044b, \u043e\u0431\u0440\u0430\u0442\u0438\u0442\u0435\u0441\u044c \u043a \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0443."""
        send_message(chat_id, help_text)
    
    else:
        print("Unknown command")
        app.logger.info("Unknown command")
        send_message(chat_id, "\u274c \u041d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u0430\u044f \u043a\u043e\u043c\u0430\u043d\u0434\u0430. \u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435 /help \u0434\u043b\u044f \u0441\u043f\u0438\u0441\u043a\u0430 \u043a\u043e\u043c\u0430\u043d\u0434.")

def handle_amount_input(chat_id, amount_text):
    print(f"Amount input handler: {amount_text}")
    app.logger.info(f"Amount input handler: {amount_text}")
    app.logger.info(f"=== STARTING handle_amount_input ===")
    app.logger.info(f"Chat ID: {chat_id}, Amount text: {amount_text}")
    app.logger.info(f"Function called successfully")
    app.logger.info(f"About to start try block")
    
    try:
        app.logger.info(f"Inside try block")
        app.logger.info(f"About to convert amount: {amount_text}")
        amount = float(amount_text.replace(',', '.'))
        app.logger.info(f"Amount converted successfully: {amount}")
        
        # Проверяем минимальную сумму
        min_amount = 1500
        app.logger.info(f"Checking minimum amount: {amount} >= {min_amount}")
        if amount < min_amount:
            app.logger.info(f"Amount is less than minimum, adjusting to {min_amount}")
            send_message(chat_id, f"\u26a0\ufe0f \u041c\u0438\u043d\u0438\u043c\u0430\u043b\u044c\u043d\u0430\u044f \u0441\u0443\u043c\u043c\u0430 \u043e\u043f\u043b\u0430\u0442\u044b: {min_amount} \u0440\u0443\u0431. \u0411\u0443\u0434\u0435\u0442 \u0438\u0441\u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u043d\u0430 \u0441\u0443\u043c\u043c\u0430 {min_amount} \u0440\u0443\u0431.")
            amount = min_amount
        
        app.logger.info(f"About to send waiting message")
        send_message(chat_id, "\u23f3 \u041e\u0436\u0438\u0434\u0430\u0435\u043c \u0440\u0435\u043a\u0432\u0438\u0437\u0438\u0442\u044b...")
        app.logger.info(f"Waiting message sent successfully")
        
        app.logger.info(f"=== AFTER SENDING WAITING MESSAGE ===")
        app.logger.info(f"About to start EPay API call with amount: {amount}")
        app.logger.info(f"Amount type: {type(amount)}")
        app.logger.info(f"Amount value: {amount}")
        
        app.logger.info(f"=== STARTING EPay API CALL ===")
        app.logger.info(f"Calling get_payment_credentials_from_epay with amount: {amount}")
        app.logger.info(f"Amount type: {type(amount)}")
        
        try:
            payment_data = get_payment_credentials_from_epay(amount)
            app.logger.info(f"EPay API call completed successfully")
        except Exception as e:
            app.logger.error(f"Error calling get_payment_credentials_from_epay: {e}")
            app.logger.error(f"Exception type: {type(e)}")
            payment_data = None
        
        app.logger.info(f"Payment data received: {payment_data}")
        app.logger.info(f"=== EPay API CALL FINISHED ===")
        
        if payment_data and not payment_data.get('error_desc'):
            app.logger.info(f"Payment data is valid, processing...")
            try:
                app.logger.info(f"About to save order to file")
                save_order_to_file(payment_data, chat_id, amount)
                app.logger.info(f"Order saved successfully")
            except Exception as e:
                app.logger.error(f"Error saving order to file: {e}")
                # Продолжаем выполнение, даже если не удалось сохранить заказ
            
            app.logger.info(f"About to format payment credentials")
            payment_text = format_payment_credentials_from_epay(payment_data)
            app.logger.info(f"Payment text formatted: {payment_text[:100]}...")
            
            app.logger.info(f"About to send payment text")
            try:
                send_message(chat_id, payment_text)
                app.logger.info(f"Payment text sent successfully")
            except Exception as e:
                app.logger.error(f"Error sending payment text: {e}")
                app.logger.error(f"Exception type: {type(e)}")
                import traceback
                app.logger.error(f"Traceback: {traceback.format_exc()}")
            
            app.logger.info(f"About to send timeout message")
            try:
                send_message(chat_id, "\u23f0 \u041d\u0430 \u043e\u043f\u043b\u0430\u0442\u0443 \u0434\u0430\u0435\u0442\u0441\u044f 20 \u043c\u0438\u043d\u0443\u0442, \u043f\u043e\u0441\u043b\u0435 \u0447\u0435\u0433\u043e \u0441\u0441\u044b\u043b\u043a\u0430 \u0431\u0443\u0434\u0435\u0442 \u043d\u0435\u0430\u043a\u0442\u0438\u0432\u043d\u0430")
                app.logger.info(f"Timeout message sent successfully")
            except Exception as e:
                app.logger.error(f"Error sending timeout message: {e}")
                app.logger.error(f"Exception type: {type(e)}")
                import traceback
                app.logger.error(f"Traceback: {traceback.format_exc()}")
        else:
            app.logger.info(f"Payment data is None or has error_desc: {payment_data}")
            error_msg = payment_data.get('error_desc', '\u041e\u0448\u0438\u0431\u043a\u0430 \u043f\u043e\u043b\u0443\u0447\u0435\u043d\u0438\u044f \u0440\u0435\u043a\u0432\u0438\u0437\u0438\u0442\u043e\u0432') if payment_data else '\u041e\u0448\u0438\u0431\u043a\u0430 \u043f\u043e\u043b\u0443\u0447\u0435\u043d\u0438\u044f \u0440\u0435\u043a\u0432\u0438\u0437\u0438\u0442\u043e\u0432'
            app.logger.info(f"Sending error message: {error_msg}")
            send_message(chat_id, f"\u274c \u041e\u0448\u0438\u0431\u043a\u0430! {error_msg}")
            
    except ValueError:
        send_message(chat_id, "\u274c \u041f\u043e\u0436\u0430\u043b\u0443\u0439\u0441\u0442\u0430, \u0432\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043e\u0440\u0440\u0435\u043a\u0442\u043d\u0443\u044e \u0441\u0443\u043c\u043c\u0443 (\u043d\u0430\u043f\u0440\u0438\u043c\u0435\u0440: 1500 \u0438\u043b\u0438 2500)")
    except Exception as e:
        app.logger.error(f"Error handling amount input: {e}")
        app.logger.error(f"Exception type: {type(e)}")
        app.logger.error(f"Exception args: {e.args}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        send_message(chat_id, "\u274c \u041f\u0440\u043e\u0438\u0437\u043e\u0448\u043b\u0430 \u043e\u0448\u0438\u0431\u043a\u0430. \u041f\u043e\u043f\u0440\u043e\u0431\u0443\u0439\u0442\u0435 \u0435\u0449\u0435 \u0440\u0430\u0437.")

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
            str(payment_data.get('order_id', 'N/A')),
            str(chat_id),
            str(amount)
        ]
        
        with open("orders.txt", "a", encoding="utf-8") as f:
            f.write("|".join(order_data) + "\n")
            
    except Exception as e:
        app.logger.error(f"Error saving order to file: {e}")

def get_payment_credentials_from_epay(amount=None):
    app.logger.info(f"Starting get_payment_credentials_from_epay with amount: {amount}")
    
    if not EPAY_API_KEY:
        app.logger.warning("EPAY API key not configured")
        return None

    try:
        # Минимальная сумма 1500 рублей согласно API
        min_amount = 1500
        actual_amount = max(min_amount, amount) if amount else min_amount
        
        data = {
            'amount': str(actual_amount),
            'merchant_order_id': 'optional',
            'api_key': EPAY_API_KEY,
            'notice_url': f"{BASE_URL}/callback",
            'success_url': f"{BASE_URL}/success",
            'fail_url': f"{BASE_URL}/fail"
        }
        app.logger.info(f"Requesting EPAY API with data: {data}")
        app.logger.info(f"EPAY_API_URL: {EPAY_API_URL}")
        app.logger.info(f"EPAY_API_KEY: {EPAY_API_KEY[:10]}...")
        
        response = requests.post(
            EPAY_API_URL,
            data=data,
            timeout=30
        )

        app.logger.info(f"EPAY API response status: {response.status_code}")
        app.logger.info(f"EPAY API response text: {response.text}")

        if response.status_code == 200:
            try:
                json_response = response.json()
                app.logger.info(f"EPAY API JSON response: {json_response}")
                return json_response
            except Exception as json_error:
                app.logger.error(f"Error parsing JSON response: {json_error}")
                return None
        else:
            app.logger.error(f"EPAY API error: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        app.logger.error(f"EPAY API request failed: {e}")
        return None
    except Exception as e:
        app.logger.error(f"Unexpected error in get_payment_credentials_from_epay: {e}")
        return None

def format_payment_credentials_from_epay(payment_data):
    try:
        order_id = payment_data.get('order_id', 'N/A')
        amount = payment_data.get('amount', 'N/A')
        
        receiver_wallet_str = ""
        
        if payment_data.get('card_number'):
            receiver_wallet_str = f"<b>\u041d\u043e\u043c\u0435\u0440 \u043a\u0430\u0440\u0442\u044b \u0434\u043b\u044f \u043e\u043f\u043b\u0430\u0442\u044b</b>: <code>{payment_data['card_number']}</code>"
        elif payment_data.get('qr_sbp_url') or payment_data.get('card_form_url'):
            url = payment_data.get('qr_sbp_url') or payment_data.get('card_form_url')
            receiver_wallet_str = f"<b>\u0421\u0441\u044b\u043b\u043a\u0430 \u043d\u0430 \u043e\u043f\u043b\u0430\u0442\u0443</b>: <a href='{url}'>{url}</a>"
        
        text = f"\ud83d\udcc4 <b>\u0421\u043e\u0437\u0434\u0430\u043d \u0437\u0430\u043a\u0430\u0437</b>: \u2116{order_id}\n\n"
        text += f"\ud83d\udcb3 {receiver_wallet_str}\n"
        text += f"\ud83d\udcb0 <b>\u0421\u0443\u043c\u043c\u0430 \u043f\u043b\u0430\u0442\u0435\u0436\u0430</b>: <code>{amount}</code> \u20bd\n\n"
        text += f"\u23f0 <b>\u0412\u0440\u0435\u043c\u044f \u043d\u0430 \u043e\u043f\u043b\u0430\u0442\u0443</b>: 20 \u043c\u0438\u043d"
        
        return text
        
    except Exception as e:
        app.logger.error(f"Error formatting payment data: {e}")
        return "\u274c \u041e\u0448\u0438\u0431\u043a\u0430 \u0444\u043e\u0440\u043c\u0430\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f \u0434\u0430\u043d\u043d\u044b\u0445"

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
                    send_message(chat_id, f'\u2705 \u041f\u043e\u043b\u0443\u0447\u0435\u043d\u0430 \u043e\u043f\u043b\u0430\u0442\u0430 \u043f\u043e \u0437\u0430\u043a\u0430\u0437\u0443 {transaction_id}!')
                    break
                    
    except Exception as e:
        app.logger.error(f"Error handling successful payment: {e}")

def get_static_payment_credentials():
    return """<b>\ud83d\udcb3 \u0420\u0415\u041a\u0412\u0418\u0417\u0418\u0422\u042b \u0414\u041b\u042f \u041e\u041f\u041b\u0410\u0422\u042b:</b>

<b>\ud83c\udfe6 \u0411\u0430\u043d\u043a\u043e\u0432\u0441\u043a\u0430\u044f \u043a\u0430\u0440\u0442\u0430:</b>
\u2022 \u041d\u043e\u043c\u0435\u0440: <code>1234 5678 9012 3456</code>
\u2022 \u0421\u0440\u043e\u043a \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u044f: <code>12/25</code>
\u2022 CVV: <code>123</code>
\u2022 \u0418\u043c\u044f \u0434\u0435\u0440\u0436\u0430\u0442\u0435\u043b\u044f: <code>IVAN IVANOV</code>

<b>\ud83d\udcb0 \u041a\u0440\u0438\u043f\u0442\u043e\u0432\u0430\u043b\u044e\u0442\u0430:</b>
\u2022 Bitcoin (BTC): <code>bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh</code>
\u2022 Ethereum (ETH): <code>0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6</code>

<b>\ud83d\udcf1 \u042d\u043b\u0435\u043a\u0442\u0440\u043e\u043d\u043d\u044b\u0435 \u043a\u043e\u0448\u0435\u043b\u044c\u043a\u0438:</b>
\u2022 PayPal: <code>payment@example.com</code>
\u2022 WebMoney: <code>R123456789012</code>

\u26a0\ufe0f <b>\u0412\u043d\u0438\u043c\u0430\u043d\u0438\u0435</b>: \u041f\u0440\u043e\u0432\u0435\u0440\u044f\u0439\u0442\u0435 \u0440\u0435\u043a\u0432\u0438\u0437\u0438\u0442\u044b \u043f\u0435\u0440\u0435\u0434 \u043e\u043f\u043b\u0430\u0442\u043e\u0439!"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
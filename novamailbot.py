import requests
import random
import string
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters
from datetime import datetime
import time
import os
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# تنظیم لاگینگ به جای print
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Telegram bot token و Admin chat_id
TELEGRAM_TOKEN = "8137194776:AAE8ykPUbwtSZELn6tXdXdlOt6EYgOgi7U4"  # توکن خودتون رو بذارید
ADMIN_CHAT_ID = 5739020477  # چت آیدی ادمین رو بذارید

# دیکشنری‌ها برای ذخیره داده‌ها
user_emails = {}
user_info = {}
last_message_ids = {}
user_language = {}
last_message_count = {}

# ترجمه‌ها
translations = {
    "en": {
        "welcome": "✨ *Welcome to TempMail Bot!* ✨\n\nI can create and manage temporary emails for you! Use the buttons below:",
        "create_success": "🎉 *Email Created Successfully!* 🎉\n\n📧 *Email:* `{email}`\n🔑 *Password:* `{password}`\n⏰ *Created At:* {created_at}\n\nWhat would you like to do next?",
        "no_emails": "⚠️ *No Emails Found!* Create one first.",
        "inbox_empty": "📭 Inbox Empty! No messages yet for `{email}`.",
        "select_inbox": "📬 *Select an Email to Check Its Inbox*:",
        "email_list": "📋 *Your Email List*:\n\nSelect an email for details or delete it:",
        "deleted_all": "🗑️ *All Emails Deleted!* What’s next?",
        "limit_reached": "⚠️ *Limit Reached!* You can have up to 5 emails. Delete one to create a new one.",
        "new_email_notification": "📩 *New Email Received!* Check your inbox for `{email}`.",
        "admin_unauthorized": "❌ *Unauthorized Access!* You are not allowed to use this command.",
        "admin_no_users": "ℹ️ *No Users Yet!* No emails have been created.",
        "admin_panel": "👨‍💼 *Admin Panel* 👨‍💼\n══════════════════════\n🌟 *Users and Their Emails* 🌟\n\n",
        "admin_user_info": "👤 *User Info*\n   🆔 *ID:* `{user_id}`\n   📛 *Name:* `{name}`\n   @ *Username:* `{username}`\n   📧 *Emails:*\n",
        "admin_email_info": "      {idx}. `{email}`\n         🔑 `{password}`\n         ⏰ `{created_at}`\n",
        "admin_check_inboxes": "📬 *All Users' Inboxes* 📬\n══════════════════════\n",
        "admin_no_emails_to_check": "ℹ️ *No Emails to Check!* No emails have been created yet.",
        "admin_inbox_empty": "      📧 `{email}`: *Inbox Empty*\n",
        "admin_login_failed": "      📧 `{email}`: *Login Failed*\n",
        "admin_inbox_message": "      📧 `{email}` ({count} messages):\n",
        "admin_message_details": "         ✨ *{idx}. Message*\n            ✉️ *From:* `{from_address}`\n            📑 *Subject:* `{subject}`\n            👀 *Preview:* `{intro}`\n            📅 *Date:* `{date}`\n",
        "admin_error": "      📧 `{email}`: *Error - {error}*\n",
        "admin_exit": "🔙 *Exit Admin Panel*"
    },
    "fa": {
        "welcome": "✨ *به ربات تمپ‌میل خوش اومدی!* ✨\n\nمی‌تونم برات ایمیل موقت بسازم و مدیریتش کنم! از دکمه‌های زیر استفاده کن:",
        "create_success": "🎉 *ایمیل با موفقیت ساخته شد!* 🎉\n\n📧 *ایمیل:* `{email}`\n🔑 *رمز عبور:* `{password}`\n⏰ *زمان ساخت:* {created_at}\n\nحالا چیکار می‌خوای بکنی؟",
        "no_emails": "⚠️ *هیچ ایمیلی پیدا نشد!* اول یکی بساز.",
        "inbox_empty": "📭 اینباکس خالیه! هنوز پیامی برای `{email}` نیومده.",
        "select_inbox": "📬 *یه ایمیل انتخاب کن تا اینباکسش رو ببینی*:",
        "email_list": "📋 *لیست ایمیل‌هات*:\n\nیه ایمیل انتخاب کن یا حذفش کن:",
        "deleted_all": "🗑️ *همه ایمیل‌ها حذف شدن!* حالا چیکار می‌خوای؟",
        "limit_reached": "⚠️ *به حد مجاز رسیدی!* فقط 5 تا ایمیل می‌تونی داشته باشی. یکی رو پاک کن تا جدید بسازی.",
        "new_email_notification": "📩 *ایمیل جدید دریافت شد!* اینباکس `{email}` رو چک کن.",
        "admin_unauthorized": "❌ *دسترسی غیرمجاز!* شما اجازه استفاده از این دستور رو ندارید.",
        "admin_no_users": "ℹ️ *هنوز کاربری وجود نداره!* هیچ ایمیلی ساخته نشده.",
        "admin_panel": "👨‍💼 *پنل ادمین* 👨‍💼\n══════════════════════\n🌟 *کاربران و ایمیل‌هاشون* 🌟\n\n",
        "admin_user_info": "👤 *اطلاعات کاربر*\n   🆔 *شناسه:* `{user_id}`\n   📛 *نام:* `{name}`\n   @ *نام کاربری:* `{username}`\n   📧 *ایمیل‌ها:*\n",
        "admin_email_info": "      {idx}. `{email}`\n         🔑 `{password}`\n         ⏰ `{created_at}`\n",
        "admin_check_inboxes": "📬 *اینباکس همه کاربران* 📬\n══════════════════════\n",
        "admin_no_emails_to_check": "ℹ️ *هیچ ایمیلی برای چک کردن وجود نداره!* هنوز کاربری ایمیل نساخته.",
        "admin_inbox_empty": "      📧 `{email}`: *اینباکس خالی*\n",
        "admin_login_failed": "      📧 `{email}`: *ورود ناموفق*\n",
        "admin_inbox_message": "      📧 `{email}` ({count} پیام):\n",
        "admin_message_details": "         ✨ *{idx}. پیام*\n            ✉️ *از:* `{from_address}`\n            📑 *موضوع:* `{subject}`\n            👀 *پیش‌نمایش:* `{intro}`\n            📅 *تاریخ:* `{date}`\n",
        "admin_error": "      📧 `{email}`: *خطا - {error}*\n",
        "admin_exit": "🔙 *خروج از پنل ادمین*"
    }
}

# نام‌های رایج برای تولید ایمیل
COMMON_NAMES = ["john", "emma", "david", "sophia", "michael", "olivia", "james", "ava", "william", "mia"]

# تنظیم Session با Retry
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429])
session.mount('https://', HTTPAdapter(max_retries=retries))

# توابع کمکی
def get_available_domain():
    try:
        response = session.get("https://api.mail.tm/domains", timeout=5)
        response.raise_for_status()
        return response.json()["hydra:member"][0]["domain"]
    except requests.RequestException:
        return "mail.tm"

def generate_random_email():
    name = random.choice(COMMON_NAMES)
    random_suffix = ''.join(random.choices(string.digits, k=3))
    domain = get_available_domain()
    return f"{name}{random_suffix}@{domain}"

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(characters, k=length))

def get_auth_token(email, password):
    try:
        headers = {"Content-Type": "application/json"}
        response = session.post(
            "https://api.mail.tm/token",
            json={"address": email, "password": password},
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        return response.json().get("token")
    except requests.RequestException:
        return None

def escape_markdown(text):
    if not text:
        return "N/A"
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

# منوها
def get_main_menu(chat_id):
    lang = user_language.get(chat_id, "en")
    keyboard = [
        [InlineKeyboardButton("📧 " + ("Create Email" if lang == "en" else "ساخت ایمیل"), callback_data='create_email')],
        [InlineKeyboardButton("📬 " + ("Check Inbox" if lang == "en" else "چک اینباکس"), callback_data='select_inbox'),
         InlineKeyboardButton("📋 " + ("Show Emails" if lang == "en" else "نمایش ایمیل‌ها"), callback_data='show_emails')],
        [InlineKeyboardButton("ℹ️ " + ("Email Info" if lang == "en" else "اطلاعات ایمیل"), callback_data='info'),
         InlineKeyboardButton("🗑️ " + ("Delete All" if lang == "en" else "حذف همه"), callback_data='delete_all')],
        [InlineKeyboardButton("🌐 " + ("Change Language" if lang == "en" else "تغییر زبان"), callback_data='change_language')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_email_list_menu(chat_id):
    lang = user_language.get(chat_id, "en")
    if chat_id not in user_emails or not user_emails[chat_id]:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 " + ("Back" if lang == "en" else "برگشت"), callback_data='back')]])
    keyboard = []
    for idx, email_data in enumerate(user_emails[chat_id]):
        email = email_data["email"]
        keyboard.append([
            InlineKeyboardButton(f"{email}", callback_data=f"info_{idx}"),
            InlineKeyboardButton("🗑️", callback_data=f"delete_{idx}"),
            InlineKeyboardButton("📋", callback_data=f"copy_{idx}")
        ])
    keyboard.append([InlineKeyboardButton("🔙 " + ("Back" if lang == "en" else "برگشت"), callback_data='back')])
    return InlineKeyboardMarkup(keyboard)

def get_inbox_selection_menu(chat_id):
    lang = user_language.get(chat_id, "en")
    if chat_id not in user_emails or not user_emails[chat_id]:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 " + ("Back" if lang == "en" else "برگشت"), callback_data='back')]])
    keyboard = []
    for idx, email_data in enumerate(user_emails[chat_id]):
        email = email_data["email"]
        keyboard.append([InlineKeyboardButton(f"{email}", callback_data=f"inbox_{idx}")])
    keyboard.append([InlineKeyboardButton("🔙 " + ("Back" if lang == "en" else "برگشت"), callback_data='back')])
    return InlineKeyboardMarkup(keyboard)

def get_admin_menu(chat_id):
    lang = user_language.get(chat_id, "en")
    keyboard = [
        [InlineKeyboardButton("📬 " + ("Check All Inboxes" if lang == "en" else "چک کردن همه اینباکس‌ها"), callback_data='admin_check_inboxes')],
        [InlineKeyboardButton("🗑️ " + ("Delete Emails" if lang == "en" else "حذف ایمیل‌ها"), callback_data='admin_delete_emails')],
        [InlineKeyboardButton("📩 " + ("Send Message to Users" if lang == "en" else "ارسال پیام به کاربران"), callback_data='admin_send_message')],
        [InlineKeyboardButton("🔙 " + ("Exit Admin Panel" if lang == "en" else "خروج از پنل ادمین"), callback_data='admin_exit')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_email_list_menu(chat_id):
    lang = user_language.get(chat_id, "en")
    if not user_emails:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 " + ("Back to Admin Panel" if lang == "en" else "برگشت به پنل ادمین"), callback_data='admin_back')]])
    keyboard = []
    for user_id, emails in user_emails.items():
        name = user_info.get(user_id, {}).get("name", "Unknown")
        for idx, email_data in enumerate(emails):
            email = email_data["email"]
            keyboard.append([
                InlineKeyboardButton(f"{name} - {email}", callback_data=f"admin_info_{user_id}_{idx}"),
                InlineKeyboardButton("🗑️", callback_data=f"admin_delete_{user_id}_{idx}")
            ])
    keyboard.append([InlineKeyboardButton("🔙 " + ("Back to Admin Panel" if lang == "en" else "برگشت به پنل ادمین"), callback_data='admin_back')])
    return InlineKeyboardMarkup(keyboard)

def get_admin_user_list_menu(chat_id):
    lang = user_language.get(chat_id, "en")
    if not user_emails:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 " + ("Back to Admin Panel" if lang == "en" else "برگشت به پنل ادمین"), callback_data='admin_back')]])
    keyboard = []
    for user_id in user_emails.keys():
        name = user_info.get(user_id, {}).get("name", "Unknown")
        username = user_info.get(user_id, {}).get("username", "N/A")
        keyboard.append([InlineKeyboardButton(f"{name} (@{username})", callback_data=f"admin_message_user_{user_id}")])
    keyboard.append([InlineKeyboardButton("📢 " + ("Send to All Users" if lang == "en" else "ارسال به همه کاربران"), callback_data='admin_message_all')])
    keyboard.append([InlineKeyboardButton("🔙 " + ("Back to Admin Panel" if lang == "en" else "برگشت به پنل ادمین"), callback_data='admin_back')])
    return InlineKeyboardMarkup(keyboard)

# ارسال یا ویرایش پیام
async def send_or_edit_message(chat_id, text, context, reply_markup, message_id=None, parse_mode='Markdown'):
    if message_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            message = await context.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            last_message_ids[chat_id] = message.message_id
    else:
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
        last_message_ids[chat_id] = message.message_id

# دستورات
async def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    logger.info(f"User chat_id: {chat_id}")
    user = update.message.from_user
    user_info[chat_id] = {"name": user.first_name, "username": user.username or "N/A"}
    user_language[chat_id] = user_language.get(chat_id, "en")
    lang = user_language[chat_id]
    await send_or_edit_message(chat_id, translations[lang]["welcome"], context, get_main_menu(chat_id))

async def create_email(chat_id, context: CallbackContext, update=None):
    lang = user_language.get(chat_id, "en")
    if chat_id in user_emails and len(user_emails[chat_id]) >= 5:
        message_id = last_message_ids.get(chat_id)
        await send_or_edit_message(chat_id, translations[lang]["limit_reached"], context, get_email_list_menu(chat_id), message_id)
        return

    try:
        email = generate_random_email()
        password = generate_random_password()
        response = session.post(
            "https://api.mail.tm/accounts",
            json={"address": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        response.raise_for_status()

        if chat_id not in user_emails:
            user_emails[chat_id] = []
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_emails[chat_id].append({"email": email, "password": password, "created_at": created_at})
        last_message_count[email] = 0

        message = translations[lang]["create_success"].format(
            email=escape_markdown(email),
            password=escape_markdown(password),
            created_at=created_at
        )
        message_id = last_message_ids.get(chat_id)
        await send_or_edit_message(chat_id, message, context, get_main_menu(chat_id), message_id)

    except requests.exceptions.HTTPError as e:
        error_msg = "❌ *Error!* " + ("Too many requests. Try again later." if e.response.status_code == 429 else str(e))
        message_id = last_message_ids.get(chat_id)
        await send_or_edit_message(chat_id, error_msg, context, get_main_menu(chat_id), message_id)

async def select_inbox(chat_id, context: CallbackContext, update=None):
    lang = user_language.get(chat_id, "en")
    message = translations[lang]["no_emails"] if chat_id not in user_emails or not user_emails[chat_id] else translations[lang]["select_inbox"]
    message_id = last_message_ids.get(chat_id)
    await send_or_edit_message(chat_id, message, context, get_inbox_selection_menu(chat_id), message_id)

async def check_inbox(chat_id, context: CallbackContext, email_idx):
    lang = user_language.get(chat_id, "en")
    user_data = user_emails[chat_id][email_idx]
    token = get_auth_token(user_data["email"], user_data["password"])
    if not token:
        message_id = last_message_ids.get(chat_id)
        await send_or_edit_message(chat_id, "❌ *Login Failed!* " + ("Please create a new email." if lang == "en" else "لطفاً یه ایمیل جدید بساز."), context, get_main_menu(chat_id), message_id)
        return

    try:
        messages_response = session.get(
            "https://api.mail.tm/messages",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        messages_response.raise_for_status()
        messages = messages_response.json().get("hydra:member", [])

        if not messages:
            msg = translations[lang]["inbox_empty"].format(email=user_data["email"])
            await send_or_edit_message(chat_id, msg, context, get_main_menu(chat_id), last_message_ids.get(chat_id))
        else:
            msg = f"📬 *{'Inbox for' if lang == 'en' else 'اینباکس برای'} `{user_data['email']}`* ({min(5, len(messages))} {'messages' if lang == 'en' else 'پیام آخر'}):\n\n"
            keyboard = []
            for i, msg_data in enumerate(messages[:5], 1):
                from_address = msg_data.get("from", {}).get("address", "Unknown")
                subject = msg_data.get("subject", "No Subject")
                intro = msg_data.get("intro", "No Preview")
                date = msg_data.get("createdAt", "Unknown Time")[:10]
                msg += (
                    f"✨ *{i}. {'Message' if lang == 'en' else 'پیام'}*\n"
                    f"   ✉️ *{'From' if lang == 'en' else 'از'}:* `{from_address}`\n"
                    f"   📑 *{'Subject' if lang == 'en' else 'موضوع'}:* `{subject}`\n"
                    f"   👀 *{'Preview' if lang == 'en' else 'پیش‌نمایش'}:* `{intro}`\n"
                    f"   📅 *{'Date' if lang == 'en' else 'تاریخ'}:* `{date}`\n\n"
                )
                keyboard.append([InlineKeyboardButton(f"📥 {'Download Message' if lang == 'en' else 'دانلود پیام'} {i}", callback_data=f"download_{email_idx}_{msg_data['id']}")])
            keyboard.append([InlineKeyboardButton("🔙 " + ("Back" if lang == "en" else "برگشت"), callback_data='back')])
            await send_or_edit_message(chat_id, msg, context, InlineKeyboardMarkup(keyboard), last_message_ids.get(chat_id))

    except requests.RequestException as e:
        await send_or_edit_message(chat_id, f"❌ *{'Error' if lang == 'en' else 'خطا'}!* {str(e)}", context, get_main_menu(chat_id), last_message_ids.get(chat_id))

async def download_email(chat_id, context: CallbackContext, email_idx, message_id):
    user_data = user_emails[chat_id][email_idx]
    token = get_auth_token(user_data["email"], user_data["password"])
    if not token:
        await send_or_edit_message(chat_id, "❌ *Login Failed!*", context, get_main_menu(chat_id), last_message_ids.get(chat_id))
        return

    file_name = None
    try:
        response = session.get(
            f"https://api.mail.tm/messages/{message_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        response.raise_for_status()
        email_content = response.json()
        subject = email_content.get("subject", "No Subject")
        html_content = email_content.get("text") or email_content.get("html", "No content available")
        
        file_name = f"{subject[:20]}.txt"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(html_content)
        with open(file_name, "rb") as f:
            await context.bot.send_document(chat_id=chat_id, document=f, filename=file_name)
    except requests.RequestException as e:
        await send_or_edit_message(chat_id, f"❌ *Download Failed!* {str(e)}", context, get_main_menu(chat_id), last_message_ids.get(chat_id))
    finally:
        if file_name and os.path.exists(file_name):
            os.remove(file_name)

async def check_inboxes_periodically(context: CallbackContext):
    logger.info(f"Checking inboxes at {datetime.now()}")
    for chat_id, emails in user_emails.items():
        lang = user_language.get(chat_id, "en")
        for email_data in emails:
            token = get_auth_token(email_data["email"], email_data["password"])
            if token:
                try:
                    response = session.get(
                        "https://api.mail.tm/messages",
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=5
                    )
                    response.raise_for_status()
                    messages = response.json().get("hydra:member", [])
                    current_count = len(messages)
                    last_count = last_message_count.get(email_data["email"], 0)
                    if current_count > last_count:
                        logger.info(f"New email for {email_data['email']}: {current_count - last_count} new messages")
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=translations[lang]["new_email_notification"].format(email=email_data["email"]),
                            parse_mode='Markdown'
                        )
                    last_message_count[email_data["email"]] = current_count
                except requests.RequestException as e:
                    logger.error(f"Error checking inbox for {email_data['email']}: {e}")

# پنل ادمین
async def admin_panel(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    logger.info(f"Admin panel accessed by chat_id: {chat_id}")
    lang = user_language.get(chat_id, "en")
    
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text(translations[lang]["admin_unauthorized"], parse_mode='Markdown')
        return

    if not user_emails:
        await update.message.reply_text(translations[lang]["admin_no_users"], parse_mode='Markdown')
        return

    total_users = len(user_emails)
    total_emails = sum(len(emails) for emails in user_emails.values())
    
    admin_msg = translations[lang]["admin_panel"]
    admin_msg += (
        f"📊 *{'Statistics' if lang == 'en' else 'آمار'}*\n"
        f"   👥 *{'Total Users' if lang == 'en' else 'تعداد کاربران'}:* {total_users}\n"
        f"   📧 *{'Total Emails' if lang == 'en' else 'تعداد ایمیل‌ها'}:* {total_emails}\n"
        f"══════════════════════\n"
    )
    for user_id, emails in user_emails.items():
        name = user_info.get(user_id, {}).get("name", "Unknown")
        username = user_info.get(user_id, {}).get("username", "N/A")
        admin_msg += translations[lang]["admin_user_info"].format(
            user_id=user_id,
            name=escape_markdown(name),
            username=escape_markdown(username)
        )
        for idx, email_data in enumerate(emails):
            admin_msg += translations[lang]["admin_email_info"].format(
                idx=idx + 1,
                email=escape_markdown(email_data['email']),
                password=escape_markdown(email_data['password']),
                created_at=email_data['created_at']
            )
        admin_msg += "══════════════════════\n"

    await send_or_edit_message(chat_id, admin_msg, context, get_admin_menu(chat_id))

async def admin_check_inboxes(chat_id, context: CallbackContext):
    lang = user_language.get(chat_id, "en")
    if chat_id != ADMIN_CHAT_ID:
        return

    if not user_emails:
        msg = translations[lang]["admin_no_emails_to_check"]
        await send_or_edit_message(chat_id, msg, context, get_admin_menu(chat_id))
        return

    inbox_msg = translations[lang]["admin_check_inboxes"]
    for user_id, emails in user_emails.items():
        name = user_info.get(user_id, {}).get("name", "Unknown")
        username = user_info.get(user_id, {}).get("username", "N/A")
        inbox_msg += translations[lang]["admin_user_info"].format(
            user_id=user_id,
            name=escape_markdown(name),
            username=escape_markdown(username)
        )
        for email_data in emails:
            token = get_auth_token(email_data["email"], email_data["password"])
            if not token:
                inbox_msg += translations[lang]["admin_login_failed"].format(email=email_data["email"])
                continue

            try:
                messages_response = session.get(
                    "https://api.mail.tm/messages",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5
                )
                messages_response.raise_for_status()
                messages = messages_response.json().get("hydra:member", [])

                if not messages:
                    inbox_msg += translations[lang]["admin_inbox_empty"].format(email=email_data["email"])
                else:
                    inbox_msg += translations[lang]["admin_inbox_message"].format(email=email_data["email"], count=len(messages))
                    for i, msg_data in enumerate(messages[:5], 1):
                        from_address = msg_data.get("from", {}).get("address", "Unknown")
                        subject = msg_data.get("subject", "No Subject")
                        intro = msg_data.get("intro", "No Preview")
                        date = msg_data.get("createdAt", "Unknown Time")[:10]
                        inbox_msg += translations[lang]["admin_message_details"].format(
                            idx=i,
                            from_address=from_address,
                            subject=subject,
                            intro=intro,
                            date=date
                        )
            except requests.RequestException as e:
                inbox_msg += translations[lang]["admin_error"].format(email=email_data["email"], error=str(e))
        inbox_msg += "══════════════════════\n"

    message_id = last_message_ids.get(chat_id)
    await send_or_edit_message(chat_id, inbox_msg, context, get_admin_menu(chat_id), message_id)

async def handle_admin_message(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id != ADMIN_CHAT_ID:
        return

    target = context.user_data.get("admin_message_target")
    if not target:
        return

    message_text = update.message.text
    if target == "all":
        for user_id in user_emails.keys():
            try:
                await context.bot.send_message(chat_id=user_id, text=f"📢 *پیام از ادمین*:\n\n{message_text}", parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
        await update.message.reply_text("✅ *پیام به همه کاربران ارسال شد!*", parse_mode='Markdown')
    else:
        try:
            await context.bot.send_message(chat_id=target, text=f"📢 *پیام از ادمین*:\n\n{message_text}", parse_mode='Markdown')
            await update.message.reply_text(f"✅ *پیام به کاربر {target} ارسال شد!*", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ *خطا در ارسال پیام به کاربر {target}:* {str(e)}", parse_mode='Markdown')

    context.user_data.pop("admin_message_target", None)

async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat_id
    lang = user_language.get(chat_id, "en")
    await query.answer()

    if query.data == "create_email":
        await create_email(chat_id, context)
    elif query.data == "select_inbox":
        await select_inbox(chat_id, context)
    elif query.data == "show_emails":
        msg = translations[lang]["email_list"] if chat_id in user_emails and user_emails[chat_id] else translations[lang]["no_emails"]
        await send_or_edit_message(chat_id, msg, context, get_email_list_menu(chat_id), last_message_ids.get(chat_id))
    elif query.data == "delete_all":
        if chat_id in user_emails and user_emails[chat_id]:
            del user_emails[chat_id]
        await send_or_edit_message(chat_id, translations[lang]["deleted_all"], context, get_main_menu(chat_id), last_message_ids.get(chat_id))
    elif query.data == "info":
        if chat_id in user_emails and user_emails[chat_id]:
            user_data = user_emails[chat_id][-1]
            msg = (
                f"ℹ️ *{'Email Info' if lang == 'en' else 'اطلاعات ایمیل'}*\n\n"
                f"📧 *{'Email' if lang == 'en' else 'ایمیل'}:* `{escape_markdown(user_data['email'])}`\n"
                f"🔑 *{'Password' if lang == 'en' else 'رمز عبور'}:* `{escape_markdown(user_data['password'])}`\n"
                f"⏰ *{'Created At' if lang == 'en' else 'زمان ساخت'}:* `{user_data['created_at']}`"
            )
        else:
            msg = translations[lang]["no_emails"]
        await send_or_edit_message(chat_id, msg, context, get_main_menu(chat_id), last_message_ids.get(chat_id))
    elif query.data == "back":
        await send_or_edit_message(chat_id, "🔙 " + ("Back to Main Menu" if lang == "en" else "برگشت به منوی اصلی"), context, get_main_menu(chat_id), last_message_ids.get(chat_id))
    elif query.data.startswith("delete_"):
        idx = int(query.data.split("_")[1])
        if chat_id in user_emails and 0 <= idx < len(user_emails[chat_id]):
            deleted_email = user_emails[chat_id].pop(idx)
            msg = f"🗑️ *{'Deleted' if lang == 'en' else 'حذف شد'}:* `{escape_markdown(deleted_email['email'])}`\n\n" + translations[lang]["email_list"]
            await send_or_edit_message(chat_id, msg, context, get_email_list_menu(chat_id), last_message_ids.get(chat_id))
    elif query.data.startswith("info_"):
        idx = int(query.data.split("_")[1])
        if chat_id in user_emails and 0 <= idx < len(user_emails[chat_id]):
            user_data = user_emails[chat_id][idx]
            msg = (
                f"ℹ️ *{'Email Info' if lang == 'en' else 'اطلاعات ایمیل'}*\n\n"
                f"📧 *{'Email' if lang == 'en' else 'ایمیل'}:* `{escape_markdown(user_data['email'])}`\n"
                f"🔑 *{'Password' if lang == 'en' else 'رمز عبور'}:* `{escape_markdown(user_data['password'])}`\n"
                f"⏰ *{'Created At' if lang == 'en' else 'زمان ساخت'}:* `{user_data['created_at']}`"
            )
            await send_or_edit_message(chat_id, msg, context, get_main_menu(chat_id), last_message_ids.get(chat_id))
    elif query.data.startswith("inbox_"):
        idx = int(query.data.split("_")[1])
        if chat_id in user_emails and 0 <= idx < len(user_emails[chat_id]):
            await check_inbox(chat_id, context, idx)
    elif query.data.startswith("copy_"):
        idx = int(query.data.split("_")[1])
        if chat_id in user_emails and 0 <= idx < len(user_emails[chat_id]):
            email = user_emails[chat_id][idx]["email"]
            await context.bot.send_message(chat_id=chat_id, text=f"`{email}`\n" + ("Copy this!" if lang == "en" else "اینو کپی کن!"), parse_mode='Markdown')
    elif query.data.startswith("download_"):
        _, email_idx, message_id = query.data.split("_")
        await download_email(chat_id, context, int(email_idx), message_id)
    elif query.data == "change_language":
        user_language[chat_id] = "fa" if user_language.get(chat_id, "en") == "en" else "en"
        await send_or_edit_message(chat_id, translations[user_language[chat_id]]["welcome"], context, get_main_menu(chat_id), last_message_ids.get(chat_id))
    elif query.data == "admin_check_inboxes" and chat_id == ADMIN_CHAT_ID:
        await admin_check_inboxes(chat_id, context)
    elif query.data == "admin_delete_emails" and chat_id == ADMIN_CHAT_ID:
        msg = "🗑️ *Delete Emails*\n\nSelect an email to delete:"
        message_id = last_message_ids.get(chat_id)
        await send_or_edit_message(chat_id, msg, context, get_admin_email_list_menu(chat_id), message_id)
    elif query.data.startswith("admin_delete_") and chat_id == ADMIN_CHAT_ID:
        _, user_id, idx = query.data.split("_")[1:]
        user_id = int(user_id)
        idx = int(idx)
        if user_id in user_emails and 0 <= idx < len(user_emails[user_id]):
            deleted_email = user_emails[user_id].pop(idx)
            if not user_emails[user_id]:
                del user_emails[user_id]
            msg = f"🗑️ *Deleted:* `{escape_markdown(deleted_email['email'])}`\n\nSelect another email to delete:"
            message_id = last_message_ids.get(chat_id)
            await send_or_edit_message(chat_id, msg, context, get_admin_email_list_menu(chat_id), message_id)
    elif query.data == "admin_send_message" and chat_id == ADMIN_CHAT_ID:
        msg = "📩 *Send Message to Users*\n\nSelect a user to send a message to:"
        message_id = last_message_ids.get(chat_id)
        await send_or_edit_message(chat_id, msg, context, get_admin_user_list_menu(chat_id), message_id)
    elif query.data.startswith("admin_message_user_") and chat_id == ADMIN_CHAT_ID:
        user_id = int(query.data.split("_")[2])
        context.user_data["admin_message_target"] = user_id
        msg = "📝 *Enter your message*\n\nPlease type the message you want to send to this user:"
        message_id = last_message_ids.get(chat_id)
        await send_or_edit_message(chat_id, msg, context, get_admin_menu(chat_id), message_id)
    elif query.data == "admin_message_all" and chat_id == ADMIN_CHAT_ID:
        context.user_data["admin_message_target"] = "all"
        msg = "📝 *Enter your message*\n\nPlease type the message you want to send to all users:"
        message_id = last_message_ids.get(chat_id)
        await send_or_edit_message(chat_id, msg, context, get_admin_menu(chat_id), message_id)
    elif query.data == "admin_back" and chat_id == ADMIN_CHAT_ID:
        await admin_panel(None, context)
    elif query.data == "admin_exit" and chat_id == ADMIN_CHAT_ID:
        msg = translations[lang]["admin_exit"]
        message_id = last_message_ids.get(chat_id)
        await send_or_edit_message(chat_id, msg, context, get_main_menu(chat_id), message_id)

# تابع برای ارسال درخواست به خود سرور (برای جلوگیری از خاموش شدن)
async def keep_alive():
    while True:
        try:
            # ارسال یه درخواست ساده به یه سرویس خارجی یا خود سرور
            # اینجا من از یه درخواست ساده به google.com استفاده می‌کنم
            # شما می‌تونید این رو به یه endpoint روی سرورتون تغییر بدید
            response = requests.get("https://www.google.com", timeout=5)
            logger.info(f"Keep-alive request sent, status: {response.status_code}")
        except Exception as e:
            logger.error(f"Keep-alive request failed: {e}")
        # هر 5 دقیقه یه درخواست ارسال می‌کنه
        await asyncio.sleep(300)

# تابع اصلی
async def main():
    # ساخت برنامه
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # ثبت Handlerها
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.Text() & ~filters.Command(), handle_admin_message))

    # ثبت Job برای چک کردن اینباکس‌ها هر 5 دقیقه
    app.job_queue.run_repeating(check_inboxes_periodically, interval=300, first=10)

    try:
        # مقداردهی اولیه ربات
        logger.info("Initializing bot...")
        await app.initialize()

        # شروع ربات
        logger.info("Starting bot...")
        await app.start()

        # شروع polling
        logger.info("Bot is starting with polling...")
        await app.updater.start_polling()

        # شروع تابع keep_alive برای جلوگیری از خاموش شدن
        logger.info("Starting keep-alive task...")
        asyncio.create_task(keep_alive())

        # نگه داشتن ربات در حالت اجرا
        while True:
            await asyncio.sleep(1)  # جلوگیری از مصرف بیش از حد CPU

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise

    finally:
        # متوقف کردن ربات
        logger.info("Stopping bot...")
        await app.updater.stop()

        # خاموش کردن ربات
        logger.info("Shutting down bot...")
        await app.shutdown()

        # متوقف کردن همه کارها
        logger.info("Stopping application...")
        await app.stop()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
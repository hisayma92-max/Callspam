import os
import json
import random
import string
from datetime import datetime
import requests
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ==========================================
# কনফিগারেশন - আপনার বট টোকেন ও আইডি সেট করা হয়েছে
# ==========================================
BOT_TOKEN = "6406898131:AAECT9Nd7EJwtMqbwRZx-IVfi4eZNU5RWr4"
ADMIN_CHAT_ID = "6735111930"

# প্র্যাঙ্ক অডিও অপশন লিস্ট
PRANK_IDS = {
    '8810': 'গাধার মতো ফুসকা!',
    '8805': 'পিজ্জা ডেলিভারি',
    '8808': 'আপনি কেন আমাকে কল করেন?',
    '8809': 'আপনি আমার ওয়াইফকে চুরি করেছেন!',
    '8803': 'আপনার কামারের টেস্ট রেজাল্ট',
    '8804': 'আপনার টয়লেট ব্যবহার জন্য অপেক্ষা করছে',
    '8806': 'আপনার কুকুরটি খুবই বিরক্তিকর!'
}

# ==========================================
# প্র্যাঙ্ক এপিআই লজিক (API Logic)
# ==========================================
def generate_device_id():
    return os.urandom(8).hex() + '@jokesphone'

def generate_unique_task_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=15))

def send_prank_call(target_number, prank_id):
    device_id = generate_device_id()
    headers = {'Content-Type': 'application/json; charset=utf-8'}

    # Step 1: Create User
    create_url = 'https://master.appha.es/lua/jokesphone/user/create.lua'
    create_payload = {
        "uv": "jokesphone", "dtype": "adr", "did": device_id, "route": "jo_1",
        "timezone": "Asia/Dhaka",
        "tags": {
            "mf": "OPPO", "mcc": 470, "mnc": 1, "r": "12", "v": "4.0.030826.346",
            "l": "en_BD", "c": "BD", "lnf": "en", "platform": "gplay",
            "aid": device_id[:16], "class": "Jokesphone_o"
        },
        "root": True, "imeiex": False, "version": "4.0.030826.346", "version_num": 346, "recommender": ""
    }

    try:
        res1 = requests.post(create_url, json=create_payload, headers=headers, timeout=10)
        if res1.status_code != 200 or res1.json().get('res') != 'OK':
            return False
    except Exception:
        return False

    # Step 2: Send Call (Create Task)
    task_url = 'https://master.appha.es/lua/jokesphone/user/create_task.lua'
    current_time = datetime.now().strftime('%Y-%m-%dT%H:%m:%S')
    task_id = generate_unique_task_id()

    task_payload = {
        'real_f': current_time, 'f': current_time, 'uid': device_id,
        'dst': target_number, 'dial': prank_id, 'titulo': 'প্র্যাঙ্ক কল',
        'credit': 1, 'smscredit': 0, 'tz': 'Asia/Dhaka', 'c': 'bd',
        'sc': 'bd', 'rec': False, 'landline': False, 'odid': device_id, '_id': task_id
    }

    try:
        res2 = requests.post(task_url, json=task_payload, headers=headers, timeout=10)
        if res2.status_code == 200 and res2.json().get('res') == 'OK':
            return True
    except Exception:
        pass

    return False

# ==========================================
# Telegram Bot Handlers
# ==========================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    context.user_data['state'] = 'idle'

    # Main Keyboard UI
    keyboard = [
        ['👤 প্রোফাইল', '📞 প্র্যাঙ্ক কল'],
        ['🔗 রেফারেল', '💬 সাপোর্ট']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    welcome_text = (
        f"🔰 **স্বাগতম {user.first_name}!**\n\n"
        "আপনি সফলভাবে যুক্ত হয়েছেন!\n"
        "💰 **স্বাগতম বোনাস:** +২০ কয়েন\n\n"
        "নিচের মেনু থেকে প্র্যাঙ্ক কল সিলেক্ট করুন।"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_state = context.user_data.get('state', 'idle')

    if text == '📞 প্র্যাঙ্ক কল':
        context.user_data['state'] = 'awaiting_number'
        msg = (
            "📞 **প্র্যাঙ্ক কল সেটআপ**\n\n"
            "১১ ডিজিটের ফোন নাম্বার দিন:\n"
            "যেমন: `019XXXXXXXX`"
        )
        await update.message.reply_text(msg, parse_mode='Markdown')

    elif user_state == 'awaiting_number':
        # Mobile number validation (Bangladesh)
        if len(text) == 11 and text.startswith(('013', '014', '015', '016', '017', '018', '019')):
            context.user_data['target_number'] = text
            context.user_data['state'] = 'awaiting_prank'

            # Inline Buttons for Prank Selection
            keyboard = [
                [InlineKeyboardButton(f"🔹 {title}", callback_data=f"prank_{p_id}")]
                for p_id, title in PRANK_IDS.items()
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            msg = (
                "⚡ **সার্ভারের সাথে কানেক্ট করা হচ্ছে...**\n\n"
                "⚙️ **প্র্যাঙ্ক সেটআপ:**\n"
                f"🎯 **টার্গেট:** `{text}`\n"
                "💰 **খরচ:** ১০ কয়েন\n\n"
                "👇 **প্র্যাঙ্ক সিলেক্ট করুন:**"
            )
            await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.message.reply_text("❌ **ভুল নম্বর!** অনুগ্রহ করে সঠিক ১১ ডিজিটের বাংলাদেশী নম্বর দিন।")

    elif text == '👤 প্রোফাইল':
        await update.message.reply_text("👤 **প্রোফাইল তথ্য:**\n\n💰 আপনার ব্যালেন্স: ২০ কয়েন")
    elif text == '🔗 রেফারেল':
        await update.message.reply_text("🔗 প্রতি রেফারে পাবেন ১০ কয়েন!")
    elif text == '💬 সাপোর্ট':
        await update.message.reply_text("💬 যেকোনো সহায়তার জন্য অ্যাডমিনের সাথে যোগাযোগ করুন।")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("prank_"):
        prank_id = data.split("_")[1]
        target_number = context.user_data.get('target_number')

        if target_number:
            # Show processing message
            await query.edit_message_text(
                "⏳ **কল প্রসেসিং চলছে...**\n⏱️ ৩-১০ মিনিটের মধ্যে কল আপনার টার্গেটের কাছে চলে যাবে।",
                parse_mode='Markdown'
            )

            # Send Call
            success = send_prank_call(target_number, prank_id)

            if success:
                prank_title = PRANK_IDS.get(prank_id, "প্র্যাঙ্ক কল")
                final_msg = (
                    "✅ **প্র্যাঙ্ক সফল!**\n\n"
                    f"🎯 **টার্গেট:** `{target_number}`\n"
                    f"🎭 **প্র্যাঙ্ক:** {prank_title}\n"
                    "🇧🇩 **দেশ:** বাংলাদেশ\n\n"
                    "📞 **কল প্রসেসিং চলছে...**\n"
                    "⏱️ ৩-১০ মিনিটের মধ্যে ফোন আসবে।"
                )
                await query.message.reply_text(final_msg, parse_mode='Markdown')
            else:
                await query.message.reply_text("❌ **কল পাঠাতে ব্যর্থ হয়েছে!** কিছুক্ষণ পর আবার চেষ্টা করুন।")

            context.user_data['state'] = 'idle'

# ==========================================
# App Execution
# ==========================================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
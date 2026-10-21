# -*- coding: utf-8 -*-
"""
بوت توزيع عينات Red Dead Online
الأوامر الإدارية تكون بالرد على رسالتك الأصلية:
توزيع / قائمة / وقف توزيع
يسجل الأعضاء عندما يردون على الرسالة الأصلية ويكتبون ID اللعبة.
"""

import json
import os
import re
from datetime import datetime

from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

TOKEN = os.getenv("BOT_TOKEN", "ضع_توكن_البوت_هنا")
DATA_FILE = "distributions.json"
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def dist_key(chat_id, message_id):
    return f"{chat_id}:{message_id}"


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id, update.effective_user.id
        )
        return member.status in ("administrator", "creator")
    except Exception:
        return False


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not msg or not chat or not user or chat.type == "private":
        return

    text = (msg.text or "").strip()
    normalized = text.translate(ARABIC_DIGITS)
    replied = msg.reply_to_message
    data = load_data()

    # بدء التوزيع: المشرف يرد على رسالته الأصلية بكلمة "توزيع".
    if normalized == "توزيع":
        if not await is_admin(update, context):
            return
        if not replied:
            await msg.reply_text("رد على رسالتك الأصلية بكلمة «توزيع» لبدء التوزيع.")
            return

        data[dist_key(chat.id, replied.message_id)] = {
            "chat_id": chat.id,
            "source_message_id": replied.message_id,
            "active": True,
            "participants": [],
            "started_at": datetime.now().isoformat(timespec="minutes"),
        }
        save_data(data)
        await msg.reply_text(
            "💞 تم بدء التوزيع لأعضاء قروبنا الكرام\n"
            f"🗓️ {datetime.now().strftime('%d/%m/%Y')}\n"
            f"⏰ {datetime.now().strftime('%H:%M')}"
        )
        return

    # أوامر القائمة والإيقاف يجب أن تكون رداً على الرسالة الأصلية.
    if normalized in ("قائمة", "وقف توزيع"):
        if not await is_admin(update, context):
            return
        if not replied:
            await msg.reply_text("رد على رسالتك الأصلية للتوزيع واكتب «قائمة» أو «وقف توزيع».")
            return

        key = dist_key(chat.id, replied.message_id)
        dist = data.get(key)
        if not dist:
            await msg.reply_text("لم أجد توزيعاً مرتبطاً بهذه الرسالة.")
            return

        people = dist["participants"]

        if normalized == "قائمة":
            lines = ["📋 قائمة طلبات التوزيع", ""]
            if not people:
                lines.append("🌸 لا توجد طلبات حتى الآن.")
            else:
                decorations = ["🎟️", "💗", "🎀", "✨", "🌷", "💜"]
                for number, person in enumerate(people, 1):
                    sticker = decorations[(number - 1) % len(decorations)]
                    username = f" (@{person['username']})" if person.get("username") else ""
                    lines.append(
                        f"{sticker} {number}. {person.get('name', 'عضو')}{username}"
                        f" — ID: {person.get('game_id', '')}"
                    )
            lines += ["", f"👥 إجمالي الطلبات: {len(people)}"]
            await msg.reply_text("\n".join(lines))
            return

        dist["active"] = False
        dist["stopped_at"] = datetime.now().isoformat(timespec="minutes")
        save_data(data)
        lines = [
            "انتهى التوزيع وإن شاء الله ما قصرنا مع أحد،",
            "🎉💗🔮",
            "ترقبوا التوزيع القادم",
            "",
            "📊 إحصائيات التوزيع:",
        ]
        if people:
            for number, person in enumerate(people, 1):
                lines.append(f"🎟️ {number}. {person.get('name', 'عضو')}: {person.get('game_id', '')}")
        else:
            lines.append("🌸 لم يتم تسجيل أي طلبات.")
        lines.append(f"\n👥 إجمالي المشاركين: {len(people)}")
        await msg.reply_text("\n".join(lines))
        return

    # تسجيل ID العضو بالرد على رسالة المستخدم الأصلية التي بدأ عليها التوزيع.
    if replied:
        key = dist_key(chat.id, replied.message_id)
        dist = data.get(key)
        if dist and dist.get("active") and text:
            if normalized in ("توزيع", "قائمة", "وقف توزيع") or re.fullmatch(r"\d+", normalized):
                return

            participant = {
                "user_id": user.id,
                "name": user.full_name,
                "username": user.username,
                "game_id": text,
                "message_id": msg.message_id,
            }
            existing = next(
                (p for p in dist["participants"] if p["user_id"] == user.id), None
            )
            if existing:
                existing.update(participant)
                number = dist["participants"].index(existing) + 1
            else:
                dist["participants"].append(participant)
                number = len(dist["participants"])
            save_data(data)
            await msg.reply_text(f"👍 تم تسجيل الأيدي ورقمك هو {number}")
            return

    # المشرف يرد على رسالة ID المسجلة بأي رقم، فيرسل البوت تهنئة.
    if re.fullmatch(r"\d+", normalized) and replied and await is_admin(update, context):
        for dist in data.values():
            if dist.get("chat_id") != chat.id:
                continue
            person = next(
                (p for p in dist.get("participants", []) if p.get("message_id") == replied.message_id),
                None,
            )
            if person:
                await msg.reply_text("🎉🤩 وصل دورك ✅ اقبل وجون")
                return


def main():
    if TOKEN == "ضع_توكن_البوت_هنا":
        raise SystemExit("ضع توكن BotFather في TOKEN أو عيّنه في متغير البيئة BOT_TOKEN.")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("البوت يعمل الآن...")
    app.run_polling()


if __name__ == "__main__":
    main()

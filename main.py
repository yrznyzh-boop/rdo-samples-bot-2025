import os, json, logging
from pathlib import Path
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

logging.basicConfig(level=logging.INFO)
log=logging.getLogger(__name__)
TOKEN=os.getenv("TELEGRAM_BOT_TOKEN","").strip()
DATA=Path("data.json")
STICKERS={k:os.getenv("STICKER_"+k.upper(),"").strip() for k in
          ["start","request","turn","stop","list"]}

def load():
    try: return json.loads(DATA.read_text(encoding="utf-8"))
    except Exception: return {"chats":{}}
db=load()
def save(): DATA.write_text(json.dumps(db,ensure_ascii=False,indent=2),encoding="utf-8")
def state(cid):
    return db["chats"].setdefault(str(cid),{"active":False,"target":None,
        "owner":None,"requests":[],"assigned":{}})
def name(u): return "@"+u.username if u.username else (u.full_name or str(u.id))

async def reply_sticker_or_text(msg,key,text):
    sid=STICKERS.get(key)
    if sid:
        try: await msg.reply_sticker(sid); return
        except Exception: log.exception("Sticker failed")
    await msg.reply_text(text)

async def handle(update:Update, context:ContextTypes.DEFAULT_TYPE):
    m=update.effective_message; u=update.effective_user; c=update.effective_chat
    if not m or not u or u.is_bot: return
    t=(m.text or "").strip(); s=state(c.id)

    if t=="توزيع":
        if not m.reply_to_message or m.reply_to_message.from_user.id!=u.id:
            await m.reply_text("ابدأ التوزيع بالرد على رسالتك أنت التي تريد استقبال الطلبات عليها.")
            return
        s.update(active=True,target=m.reply_to_message.message_id,owner=u.id,
                 requests=[],assigned={})
        save()
        await reply_sticker_or_text(m,"start","💞 تم بدء التوزيع لأعضاء قروبنا الكرام!")
        return

    if t=="وقف توزيع":
        if s["owner"]!=u.id or not s["active"]:
            await m.reply_text("ما فيه توزيع نشط لك حالياً."); return
        s["active"]=False; save()
        lines=["🎉 انتهى التوزيع، شكراً للجميع!","📊 إحصائيات التوزيع:"]
        lines += [f"{i}. {x['name']} — {x['id_text']}" for i,x in enumerate(s["requests"],1)]
        await reply_sticker_or_text(m,"stop","\n".join(lines)); return

    if t=="قائمة":
        if s["owner"]!=u.id:
            await m.reply_text("قائمة الطلبات متاحة لصاحب التوزيع فقط."); return
        if not s["requests"]:
            await m.reply_text("📋 لا توجد طلبات حتى الآن."); return
        lines=["📋 قائمة الطلبات"]
        lines += [f"🏷️ {i}. {x['name']} — {x['id_text']}" for i,x in enumerate(s["requests"],1)]
        await reply_sticker_or_text(m,"list","\n".join(lines)); return

    # Member submits an ID by replying to the owner's original message.
    if s["active"] and m.reply_to_message and m.reply_to_message.message_id==s["target"]:
        if u.id==s["owner"]: return
        value=t or (m.caption or "").strip()
        if not value:
            await m.reply_text("اكتب الآيدي كرد على رسالة التوزيع."); return
        if any(x["user_id"]==u.id for x in s["requests"]):
            await m.reply_text("💗 طلبك مسجل من قبل."); return
        s["requests"].append({"user_id":u.id,"name":name(u),"id_text":value,
                              "message_id":m.message_id})
        save()
        await reply_sticker_or_text(m,"request",
            f"👍 تم تسجيل الآيدي ورقمك هو {len(s['requests'])}")
        return

    # Owner assigns any numeric position by replying to that member's submitted message.
    if u.id==s["owner"] and t.isdigit() and m.reply_to_message:
        target=next((x for x in s["requests"]
                     if x["message_id"]==m.reply_to_message.message_id),None)
        if target:
            s["assigned"][str(target["user_id"])]=int(t); save()
            await context.bot.send_message(c.id,"🎉🤩 وصل دورك ✅ اقبل وجون",
                                           reply_to_message_id=target["message_id"])

def main():
    if not TOKEN: raise RuntimeError("Set TELEGRAM_BOT_TOKEN in environment variables")
    app=Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.COMMAND,handle))
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__": main()

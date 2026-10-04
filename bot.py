import os, logging, asyncio
from decimal import Decimal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import db
from provider import MockProvider

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
TOKEN = os.getenv("BOT_TOKEN", "").strip()
SUPER_ADMIN = int(os.getenv("ADMIN_ID", "6882165252"))
EARN = Decimal(os.getenv("EARN_PER_EVENT", "0.10"))
MIN_WITHDRAW = Decimal(os.getenv("MIN_WITHDRAW", "10"))
provider = MockProvider()

def is_admin(uid):
    return uid == SUPER_ADMIN or db.is_admin(uid)

def user_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Test Number", callback_data="number"),
         InlineKeyboardButton("🧪 Test SMS", callback_data="event")],
        [InlineKeyboardButton("📊 Test Ranges", callback_data="ranges"),
         InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance"),
         InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("🔗 Referral", callback_data="referral"),
         InlineKeyboardButton("📢 Notice", callback_data="notice")],
    ])

def admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔐 Join Verify ON/OFF", callback_data="join_toggle"),
         InlineKeyboardButton("📋 Channels", callback_data="channels")],
        [InlineKeyboardButton("👥 Admins", callback_data="admins"),
         InlineKeyboardButton("💸 Withdrawals", callback_data="withdrawals")],
        [InlineKeyboardButton("📣 Broadcast", callback_data="broadcast"),
         InlineKeyboardButton("📝 Set Notice", callback_data="set_notice")],
        [InlineKeyboardButton("🧪 Create Test SMS", callback_data="make_event"),
         InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
        [InlineKeyboardButton("⬅️ User Menu", callback_data="home")],
    ])

async def joined(context, uid):
    if db.get_setting("join_verify", "0") != "1":
        return True
    channels = db.channels()
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(ch["chat_id"], uid)
            if member.status in ("left", "kicked"):
                return False
        except Exception:
            return False
    return True

async def send_gate(message, context, uid):
    rows = [[InlineKeyboardButton("📢 " + c["title"], url=c["url"])] for c in db.channels()]
    rows.append([InlineKeyboardButton("✅ Verify Join", callback_data="verify")])
    await message.reply_text("🔒 সম্পূর্ণ মেনু খুলতে প্রয়োজনীয় চ্যানেলগুলো Join করুন।",
                             reply_markup=InlineKeyboardMarkup(rows))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    db.ensure_user(u.id, u.username or "")
    if context.args:
        ref = context.args[0]
        if ref.isdigit() and int(ref) != u.id:
            db.set_referrer(u.id, int(ref))
    if not await joined(context, u.id):
        await send_gate(update.message, context, u.id)
        return
    await update.message.reply_text("🌐 NEXORAX PANEL\nস্বাগতম!", reply_markup=admin_kb() if is_admin(u.id) else user_kb())

async def admin_cmd(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Admin only.")
        return
    await update.message.reply_text("👑 NEXORAX ADMIN", reply_markup=admin_kb())

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    db.ensure_user(uid, q.from_user.username or "")
    d = q.data

    if d == "verify":
        if await joined(context, uid):
            await q.edit_message_text("✅ Join verified. Menu unlocked.", reply_markup=user_kb())
        else:
            await q.edit_message_text("❌ সব required channel Join হয়নি।", reply_markup=q.message.reply_markup)
        return
    if d == "home":
        await q.edit_message_text("🌐 NEXORAX PANEL", reply_markup=admin_kb() if is_admin(uid) else user_kb()); return
    if d == "number":
        n = provider.get_number()
        await q.edit_message_text(f"📱 TEST NUMBER\n`{n}`\n\nএটি demo placeholder number; বাস্তব SMS receive করে না।",
                                  parse_mode="Markdown", reply_markup=user_kb()); return
    if d == "event":
        ev = provider.latest()
        if not ev:
            await q.edit_message_text("এখনো test event নেই।", reply_markup=user_kb()); return
        await q.edit_message_text(f"🧪 TEST SMS EVENT\nService: {ev['service']}\nNumber: {ev['number']}\nCode: `{ev['code']}`\nTime: {ev['time']}",
                                  parse_mode="Markdown", reply_markup=user_kb()); return
    if d == "ranges":
        txt = "📊 TEST RANGES\n" + "\n".join(f"• {x['range']} | {x['service']} | hits {x['hits']}" for x in provider.ranges())
        await q.edit_message_text(txt, reply_markup=user_kb()); return
    if d == "balance":
        u = db.user(uid)
        await q.edit_message_text(f"💰 Balance: ৳{u['balance']:.2f}\n🧪 Test events: {u['events']}\n🏅 Earned: ৳{u['earned']:.2f}", reply_markup=user_kb()); return
    if d == "leaderboard":
        rows = db.leaderboard()
        txt = "🏆 LEADERBOARD\n\n" + ("\n".join(f"{i+1}. {r['username'] or r['user_id']} — {r['events']} events — ৳{r['earned']:.2f}" for i,r in enumerate(rows)) if rows else "এখনো কোনো activity নেই।")
        await q.edit_message_text(txt, reply_markup=user_kb()); return
    if d == "referral":
        me = await context.bot.get_me()
        await q.edit_message_text(f"🔗 তোমার referral link:\nhttps://t.me/{me.username}?start={uid}\n\nApproved referral হলে commission admin নির্ধারণ করবে।", reply_markup=user_kb()); return
    if d == "notice":
        await q.edit_message_text(db.get_setting("notice", "কোনো notice নেই।"), reply_markup=user_kb()); return
    if d == "withdraw":
        u = db.user(uid)
        await q.edit_message_text(f"💸 Withdrawal\nBalance: ৳{u['balance']:.2f}\nMinimum: ৳{MIN_WITHDRAW:.2f}\nRequest করতে /withdraw AMOUNT METHOD ACCOUNT লিখুন।", reply_markup=user_kb()); return

    if not is_admin(uid):
        await q.edit_message_text("⛔ Admin only."); return
    if d == "join_toggle":
        val = "0" if db.get_setting("join_verify","0") == "1" else "1"
        db.set_setting("join_verify", val)
        await q.edit_message_text("Join verification: " + ("ON" if val == "1" else "OFF"), reply_markup=admin_kb()); return
    if d == "channels":
        cs = db.channels()
        txt = "📋 Channels\n" + ("\n".join(f"{c['title']} | {c['chat_id']}" for c in cs) if cs else "No channels configured.")
        txt += "\n\nAdd: /addchannel @channel Title https://t.me/channel\nRemove: /delchannel @channel"
        await q.edit_message_text(txt, reply_markup=admin_kb()); return
    if d == "admins":
        await q.edit_message_text("Admins: " + ", ".join(map(str, db.admins())) + f"\nSuper Admin: {SUPER_ADMIN}\nAdd: /addadmin ID\nRemove: /deladmin ID", reply_markup=admin_kb()); return
    if d == "withdrawals":
        rows = db.withdrawals()
        txt = "💸 Withdrawal requests\n" + ("\n".join(f"#{r['id']} user={r['user_id']} ৳{r['amount']:.2f} {r['method']} {r['account']} [{r['status']}]" for r in rows) if rows else "No requests.")
        txt += "\nApprove: /approve ID\nReject: /reject ID"
        await q.edit_message_text(txt, reply_markup=admin_kb()); return
    if d == "broadcast":
        await q.edit_message_text("Broadcast পাঠাতে /broadcast আপনার বার্তা লিখুন", reply_markup=admin_kb()); return
    if d == "set_notice":
        await q.edit_message_text("Notice বদলাতে /notice আপনার বার্তা লিখুন", reply_markup=admin_kb()); return
    if d == "make_event":
        ev = provider.create_event()
        db.record_event(uid, EARN)
        await q.edit_message_text(f"🧪 Test event created\n{ev['service']} | {ev['number']} | {ev['code']}\nAdmin test balance credited ৳{EARN:.2f}", reply_markup=admin_kb()); return
    if d == "settings":
        await q.edit_message_text(f"Event credit: ৳{EARN:.2f}\nMinimum withdrawal: ৳{MIN_WITHDRAW:.2f}\nJoin verification: {db.get_setting('join_verify','0')}", reply_markup=admin_kb()); return

async def text_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg = update.message.text.strip()
    if msg.startswith("/withdraw "):
        parts = msg.split(maxsplit=3)
        if len(parts) != 4:
            await update.message.reply_text("Format: /withdraw AMOUNT METHOD ACCOUNT"); return
        try: amount = Decimal(parts[1])
        except: await update.message.reply_text("Amount ভুল।"); return
        u = db.user(uid)
        if amount < MIN_WITHDRAW or amount > Decimal(str(u["balance"])):
            await update.message.reply_text("Minimum-এর কম অথবা balance অপর্যাপ্ত।"); return
        db.withdraw(uid, amount, parts[2], parts[3])
        await update.message.reply_text("✅ Withdrawal request জমা হয়েছে।"); return
    if not is_admin(uid): return
    if msg.startswith("/addadmin "):
        try: db.add_admin(int(msg.split()[1])); await update.message.reply_text("Admin added.")
        except: await update.message.reply_text("ব্যবহার: /addadmin USER_ID")
    elif msg.startswith("/deladmin "):
        try: db.remove_admin(int(msg.split()[1])); await update.message.reply_text("Admin removed.")
        except: await update.message.reply_text("ব্যবহার: /deladmin USER_ID")
    elif msg.startswith("/addchannel "):
        p=msg.split(maxsplit=3)
        if len(p)==4:
            db.add_channel(p[1],p[2],p[3]); await update.message.reply_text("Channel saved. Bot-কে channel admin করুন।")
        else: await update.message.reply_text("/addchannel @channel Title https://t.me/channel")
    elif msg.startswith("/delchannel "):
        db.remove_channel(msg.split()[1]); await update.message.reply_text("Channel removed.")
    elif msg.startswith("/notice "):
        db.set_setting("notice", msg[8:]); await update.message.reply_text("Notice updated.")
    elif msg.startswith("/broadcast "):
        users=db.user_ids()
        sent=0
        for target in users:
            try: await context.bot.send_message(target, msg[11:]); sent+=1
            except Exception: pass
        await update.message.reply_text(f"Broadcast attempted: {sent}")
    elif msg.startswith("/approve "):
        try:
            wid=int(msg.split()[1]); db.withdraw_status(wid,"approved"); await update.message.reply_text("Approved.")
        except: await update.message.reply_text("ব্যবহার: /approve ID")
    elif msg.startswith("/reject "):
        try:
            wid=int(msg.split()[1]); db.withdraw_status(wid,"rejected"); await update.message.reply_text("Rejected.")
        except: await update.message.reply_text("ব্যবহার: /reject ID")

async def post_init(app):
    db.init_db()

def main():
    if not TOKEN:
        raise RuntimeError("Set BOT_TOKEN in Render Environment Variables")
    db.init_db()
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_commands))
    app.add_handler(MessageHandler(filters.COMMAND, text_commands))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

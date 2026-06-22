import telebot
import requests
import sqlite3
import time
import re
from flask import Flask
BOT_TOKEN = "8646657182:AAGDAIcJVR_5tnPVNHmh1PJ3V-ifmAStM80"
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

bot_running = False
bot_thread = None
# =========================
# LEVEL UP DATABASE
# =========================

ADMIN_ID = 7970107324  # এখানে তোমার Telegram ID দাও

conn = sqlite3.connect("lvlup.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS lvlup (
    uid TEXT PRIMARY KEY,
    exp INTEGER,
    added_time INTEGER
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT,
    username TEXT,
    chat_type TEXT,
    joined_time INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS groups (
    chat_id INTEGER PRIMARY KEY
)
""")

conn.commit()
# =========================
# SAVE USERS / GROUPS
# =========================

def save_user(user):

    try:

        user_id = user.id
        first_name = user.first_name or "N/A"
        username = user.username or "N/A"

        cursor.execute("""
        INSERT OR REPLACE INTO users
        (user_id, first_name, username, chat_type, joined_time)
        VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            first_name,
            username,
            "private",
            int(time.time())
        ))

        conn.commit()

    except Exception as e:
        print("SAVE USER ERROR:", e)
# =========================
# EXP EXTRACT FUNCTION
# =========================

def get_player_exp(uid):
    url = f"https://player-info-ob53.vercel.app/player-info?uid={uid}&t={int(time.time())}"

    response = requests.get(url, timeout=10)

    if response.status_code != 200:
        return None

    data = response.json()

    basic = data.get("basicInfo", {})

    return {
        "name": basic.get("nickname", "N/A"),
        "uid": basic.get("accountId", uid),
        "level": basic.get("level", "N/A"),
        "exp": basic.get("exp", 0),
        "region": basic.get("region", "N/A"),
        "likes": basic.get("liked", "N/A"),
        "honor": data.get("creditScoreInfo", {}).get("creditScore", "N/A")
    }


# =========================
# PROGRESS BAR
# =========================

def make_progress_bar(seconds_left):
    total = 21600

    passed = total - seconds_left

    percent = int((passed / total) * 100)

    filled = int(percent / 10)

    empty = 10 - filled

    bar = "█" * filled + "░" * empty

    return bar, percent
#acces to jwt
@bot.message_handler(commands=['access_to_jwt'])
def access_to_jwt(message):
    try:
        args = message.text.split(" ", 1)

        if len(args) < 2:
            bot.reply_to(message, "❌ Usage:\n/access_to_jwt {access_token}")
            return

        access_token = args[1]

        msg = bot.reply_to(message, "⏳ Processing...")

        url = f"https://ff-jwt-api-ob53.vercel.app/acces_to_jwt?access_token={access_token}"
        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            try:
                json_data = response.json()

                # ❌ যেগুলো দেখাতে চাও না
                hidden_keys = ["OWNER", "TG", "url"]

                formatted = "🔐 *JWT Conversion Result*\n\n"

                for key, value in json_data.items():
                    if key in hidden_keys:
                        continue   # skip করবে

                    formatted += f"• *{key}* : `{value}`\n"

                bot.edit_message_text(
                    formatted,
                    message.chat.id,
                    msg.message_id,
                    parse_mode="Markdown"
                )

            except:
                bot.edit_message_text(
                    f"✅ Result:\n\n`{response.text}`",
                    message.chat.id,
                    msg.message_id,
                    parse_mode="Markdown"
                )

        else:
            bot.edit_message_text(
                f"❌ API Error: {response.status_code}",
                message.chat.id,
                msg.message_id
            )

    except Exception as e:
        bot.reply_to(message, f"❌ Error:\n{str(e)}")

@bot.message_handler(commands=['my_tg_info'])
def my_tg_info(message):
    import html
    user = message.from_user
    # ইউজারের তথ্য
    first_name = html.escape(user.first_name or "N/A")
    last_name = html.escape(user.last_name or "")
    username = f"@{user.username}" if user.username else "N/A"
    user_id = user.id

    # নাম এবং ইউজারনেম চেঞ্জের count (Telegram API থেকে direct info নেই, তাই আমরা simple historic info রাখি)
    # এখানে placeholder 0 দেওয়া হলো; পরে ডাটাবেস/সেশন ব্যবহার করে track করা যাবে
    first_name_changes = 0
    username_changes = 0

    text = f"""
👤 <b>YOUR TELEGRAM INFO</b>

• Name: <code>{first_name} {last_name}</code>
• Username: <code>{username}</code>
• User ID: <code>{user_id}</code>
• First Name Changed: <code>{first_name_changes} times</code>
• Username Changed: <code>{username_changes} times</code>
"""

    # profile photo দেখানো
    try:
        photos = bot.get_user_profile_photos(user.id)
        if photos.total_count > 0:
            bot.send_photo(
                message.chat.id,
                photos.photos[0][-1].file_id,
                caption=text,
                parse_mode="HTML"
            )
        else:
            bot.send_message(
                message.chat.id,
                text,
                parse_mode="HTML"
            )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            text + f"\n❌ Error fetching profile photo: {str(e)}",
            parse_mode="HTML"
        )
#guest to token
@bot.message_handler(commands=['token'])
def guest_to_jwt(message):
    try:
        args = message.text.split(" ", 2)

        if len(args) < 3:
            bot.reply_to(message, "❌ Usage:\n/token {uid} {password}")
            return

        uid = args[1]
        password = args[2]

        msg = bot.reply_to(message, "Token genareting please wait...")

        url = f"https://ff-jwt-api-ob53.vercel.app/guest_to_jwt?uid={uid}&password={password}"
        response = requests.get(url, timeout=15)

        if response.status_code == 200:
            try:
                data = response.json()

                # 🔐 short token function
                def short(t):
                    return t[:6] + "..." + t[-4:] if t and len(t) > 15 else t

                # 🔪 long text split function
                def split_text(text, size=4000):
                    return [text[i:i+size] for i in range(0, len(text), size)]

                clan = data.get("clan", {})

                formatted = f"""
🔐 *Guest → JWT Result*

👤 *Account Info*
• UID : `{data.get("account_uid")}`
• Nickname : `{data.get("nickname")}`
• Level : `{data.get("level")}`
• Region : `{data.get("region")}`

🎮 *Game Stats*
• Rank : `{data.get("rank")}`
• CS Rank : `{data.get("csRank")}`
• Likes : `{data.get("likes")}`

🏰 *Clan Info*
• Name : `{clan.get("clanName")}`
• Level : `{clan.get("clanLevel")}`
• Members : `{clan.get("memberCount")}`

🔑 *Tokens (Short View)*
• Access Token : `{short(data.get("access_token"))}`
• JWT Token : `{short(data.get("jwt_token"))}`

✅ *Status* : `{data.get("success")}`
"""

                bot.edit_message_text(
                    formatted,
                    message.chat.id,
                    msg.message_id,
                    parse_mode="Markdown"
                )

                # 🔥 Full token message (split safe)
                full_text = (
                    "🔑 *Full Tokens*\n\n"
                    "🎯 *Access Token:*\n"
                    f"`{data.get('access_token')}`\n\n"
                    "🛡️ *JWT Token:*\n"
                    f"`{data.get('jwt_token')}`"
                )

                for part in split_text(full_text):
                    bot.send_message(
                        message.chat.id,
                        part,
                        parse_mode="Markdown"
                )
            except:
                bot.edit_message_text(
                    f"✅ Result:\n\n`{response.text}`",
                    message.chat.id,
                    msg.message_id,
                    parse_mode="Markdown"
                )

        else:
            bot.edit_message_text(
                f"❌ API Error: {response.status_code}",
                message.chat.id,
                msg.message_id
            )

    except Exception as e:
        bot.reply_to(message, f"❌ Error:\n{str(e)}")
#bot status 
# =========================
# STATUS COMMAND
# =========================
ADMIN_PAGE_SIZE = 5

@bot.message_handler(commands=['status'])
def bot_status(message):

    try:

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM groups")
        total_groups = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM lvlup")
        total_tracking = cursor.fetchone()[0]

        # normal user
        if message.from_user.id != ADMIN_ID:

            text = f"""
📊 <b>BOT STATUS</b>

━━━━━━━━━━━━━━

👥 Total Users:
<code>{total_users}</code>

👨‍👩‍👦 Total Groups:
<code>{total_groups}</code>

🎮 Active Level Tracking:
<code>{total_tracking}</code>

━━━━━━━━━━━━━━

🤖 Bot Running Successfully
"""

            bot.reply_to(
                message,
                text,
                parse_mode="HTML"
            )

            return

        # admin panel
        send_admin_page(message.chat.id, 0)

    except Exception as e:
        bot.reply_to(message, f"❌ Error:\n{str(e)}")


# =========================
# ADMIN PAGE SYSTEM
# =========================

def send_admin_page(chat_id, page):

    offset = page * ADMIN_PAGE_SIZE

    cursor.execute("""
    SELECT user_id, first_name, username, joined_time
    FROM users
    ORDER BY joined_time DESC
    LIMIT ? OFFSET ?
    """, (ADMIN_PAGE_SIZE, offset))

    users = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    total_pages = (total_users + ADMIN_PAGE_SIZE - 1) // ADMIN_PAGE_SIZE

    text = f"""
👑 <b>ADMIN USER PANEL</b>

📊 Total Users: <code>{total_users}</code>
📄 Page: <code>{page+1}/{total_pages}</code>

━━━━━━━━━━━━━━
"""

    for i, user in enumerate(users, start=1):

        user_id = user[0]
        first_name = user[1]
        username = user[2]
        joined = time.strftime(
            "%Y-%m-%d %H:%M",
            time.localtime(user[3])
        )

        text += f"""
👤 <b>User {i}</b>

├─ Name: <code>{first_name}</code>
├─ Username: <code>@{username}</code>
├─ User ID: <code>{user_id}</code>
└─ Saved: <code>{joined}</code>

━━━━━━━━━━━━━━
"""

    markup = InlineKeyboardMarkup(row_width=2)

    buttons = []

    if page > 0:
        buttons.append(
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data=f"admin_page_{page-1}"
            )
        )

    if page < total_pages - 1:
        buttons.append(
            InlineKeyboardButton(
                "➡️ Next",
                callback_data=f"admin_page_{page+1}"
            )
        )

    if buttons:
        markup.add(*buttons)

    bot.send_message(
        chat_id,
        text,
        parse_mode="HTML",
        reply_markup=markup
    )


# =========================
# ADMIN CALLBACK
# =========================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("admin_page_")
)
def admin_page_callback(call):

    try:

        page = int(call.data.split("_")[2])

        offset = page * ADMIN_PAGE_SIZE

        cursor.execute("""
        SELECT user_id, first_name, username, joined_time
        FROM users
        ORDER BY joined_time DESC
        LIMIT ? OFFSET ?
        """, (ADMIN_PAGE_SIZE, offset))

        users = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        total_pages = (
            total_users + ADMIN_PAGE_SIZE - 1
        ) // ADMIN_PAGE_SIZE

        text = f"""
👑 <b>ADMIN USER PANEL</b>

📊 Total Users: <code>{total_users}</code>
📄 Page: <code>{page+1}/{total_pages}</code>

━━━━━━━━━━━━━━
"""

        for i, user in enumerate(users, start=1):

            user_id = user[0]
            first_name = user[1]
            username = user[2]

            joined = time.strftime(
                "%Y-%m-%d %H:%M",
                time.localtime(user[3])
            )

            text += f"""
👤 <b>User {i}</b>

├─ Name: <code>{first_name}</code>
├─ Username: <code>@{username}</code>
├─ User ID: <code>{user_id}</code>
└─ Saved: <code>{joined}</code>

━━━━━━━━━━━━━━
"""

        markup = InlineKeyboardMarkup(row_width=2)

        buttons = []

        if page > 0:
            buttons.append(
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data=f"admin_page_{page-1}"
                )
            )

        if page < total_pages - 1:
            buttons.append(
                InlineKeyboardButton(
                    "➡️ Next",
                    callback_data=f"admin_page_{page+1}"
                )
            )

        if buttons:
            markup.add(*buttons)

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )

        bot.answer_callback_query(call.id)

    except Exception as e:
        bot.answer_callback_query(
            call.id,
            f"Error: {str(e)}"
        )

#tg info
@bot.message_handler(commands=['info'])
def info_command(message):
    import html

    try:
        # যদি গ্রুপে কাউকে রিপ্লাই করে কমান্ড করা হয়
        if message.reply_to_message:
            user = message.reply_to_message.from_user
        else:
            # অন্যথায় নিজের তথ্য দেখাবে
            user = message.from_user

        first_name = html.escape(user.first_name or "N/A")
        last_name = html.escape(user.last_name or "")
        username = f"@{user.username}" if user.username else "N/A"
        user_id = user.id

        # historic info placeholder
        first_name_changes = 0
        username_changes = 0

        text = f"""
👤 <b>USER INFO</b>

• Name: <code>{first_name} {last_name}</code>
• Username: <code>{username}</code>
• User ID: <code>{user_id}</code>
• First Name Changed: <code>{first_name_changes} times</code>
• Username Changed: <code>{username_changes} times</code>
"""

        # profile photo
        photos = bot.get_user_profile_photos(user.id)
        if photos.total_count > 0:
            bot.send_photo(
                message.chat.id,
                photos.photos[0][-1].file_id,
                caption=text,
                parse_mode="HTML",
                reply_to_message_id=message.message_id
            )
        else:
            bot.send_message(
                message.chat.id,
                text,
                parse_mode="HTML",
                reply_to_message_id=message.message_id
            )

    except Exception as e:
        bot.reply_to(message, f"❌ Error:\n{str(e)}")

#group new member welcame msg
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import html

# নতুন সদস্যকে স্বাগত জানান
@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for user in message.new_chat_members:
        if user.id == bot.get_me().id:
            # যদি বট যোগ হয়, আলাদা মেসেজ
            bot.send_message(
                message.chat.id,
                "🤖 Thanks for adding me!\nUse /help to see all commands.",
            )
        else:
            # নতুন ইউজারের ইনফো
            first_name = html.escape(user.first_name or "N/A")
            last_name = html.escape(user.last_name or "")
            username = f"@{user.username}" if user.username else "N/A"
            user_id = user.id

            # Historic info placeholder
            first_name_changes = 0
            username_changes = 0

            user_info_text = f"""
👋 Welcome <b>{first_name} {last_name}</b>!

👤 <b>USER INFO</b>
• Name: <code>{first_name} {last_name}</code>
• Username: <code>{username}</code>
• User ID: <code>{user_id}</code>
• First Name Changed: <code>{first_name_changes} times</code>
• Username Changed: <code>{username_changes} times</code>

🤖 <b>HOW TO USE THIS BOT</b>
• /get UID → Player info
• /token UID PASSWORD → Guest → JWT + Access Token
• /access_to_jwt ACCESS_TOKEN → JWT conversion
• /change_vio JWT_TOKEN BIO → Change account bio
• /insta_info USERNAME → Instagram info
• /info → Show user info (reply to someone to see their info)
"""

            # Start button (referral style)
            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton(
                    "🚀 Start Bot",
                    url=f"https://t.me/{bot.get_me().username}?start={user_id}"
                )
            )

            # Profile photo সহ মেসেজ পাঠানো
            try:
                photos = bot.get_user_profile_photos(user.id)
                if photos.total_count > 0:
                    bot.send_photo(
                        message.chat.id,
                        photos.photos[0][-1].file_id,
                        caption=user_info_text,
                        parse_mode="HTML",
                        reply_markup=markup
                    )
                else:
                    bot.send_message(
                        message.chat.id,
                        user_info_text,
                        parse_mode="HTML",
                        reply_markup=markup
                    )
            except:
                bot.send_message(
                    message.chat.id,
                    user_info_text,
                    parse_mode="HTML",
                    reply_markup=markup
                )

#guest to frnd request

@bot.message_handler(commands=['add_frnd_guest'])
def add_friend_guest(message):
    try:
        args = message.text.split(" ")

        if len(args) < 4:
            bot.reply_to(message, "❌ Usage:\n/add_frnd_guest GUEST_ID GUEST_PASSWORD FRIEND_UID")
            return

        uid = args[1]
        password = args[2]
        friend_uid = args[3]

        msg = bot.reply_to(message, "⏳ Sending Friend Request...")

        url = f"https://friend-sable.vercel.app/adding_friend?uid={uid}&password={password}&friend_uid={friend_uid}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            import json, html

            try:
                data = json.loads(response.text)
            except:
                bot.edit_message_text(
                    f"📩 Response:\n<code>{html.escape(response.text)}</code>",
                    message.chat.id,
                    msg.message_id,
                    parse_mode="HTML"
                )
                return

            def esc(x):
                return html.escape(str(x)) if x else "N/A"

            # 🔥 smart format (new structure)
            formatted = f"""

⚙️ <b>REQUEST INFO</b>
• Author UID : <code>{esc(data.get("author_uid"))}</code>
• Friend UID : <code>{esc(friend_uid)}</code>
• Status : <code>{esc(data.get("status"))}</code>
•  <b>Time: </b>{esc(data.get("time"))}
• Version : <code>{esc(data.get("release_version"))}</code>

📌 <b>Friend Info</b>
• Nickname : <code>{esc(data.get("nickname"))}</code>
• UID : <code>{esc(data.get("uid"))}</code>
• Level : <code>{esc(data.get("level"))}</code>
• Likes : <code>{esc(data.get("likes"))}</code>
• Region : <code>{esc(data.get("region"))}</code>

"""

            bot.edit_message_text(
                formatted,
                message.chat.id,
                msg.message_id,
                parse_mode="HTML"
            )

        else:
            bot.edit_message_text(
                f"❌ API Error: {response.status_code}",
                message.chat.id,
                msg.message_id
            )

    except Exception as e:
        bot.reply_to(message, f"❌ Error:\n{str(e)}")
#ff all info comand
@bot.message_handler(commands=['get'])
def get_player_info(message):
    try:
        args = message.text.split(" ", 1)

        if len(args) < 2:
            bot.reply_to(message, "❌ Usage:\n/get {uid}")
            return

        uid = args[1]
        msg = bot.reply_to(message, "⏳ Fetching Player Info...")

        url = f"https://player-info-ob53.vercel.app/player-info?uid={uid}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            import json, html
            from datetime import datetime, timezone, timedelta

            data = json.loads(response.text)

            basic = data.get("basicInfo", {})
            profile = data.get("profileInfo", {})
            clan = data.get("clanBasicInfo", {})
            captain = data.get("captainBasicInfo", {})
            pet = data.get("petInfo", {})
            social = data.get("socialInfo", {})

            def esc(x):
                return html.escape(str(x)) if x else "N/A"

            # 🔥 timezone format (+08 like your example)
            def format_time(ts):
                try:
                    dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
                    dt = dt.astimezone(timezone(timedelta(hours=8)))
                    return dt.strftime("%Y-%m-%d %H:%M:%S +08")
                except:
                    return "N/A"

            text = f"""
<b>ACCOUNT INFO:</b>

┌ 👤 <b>ACCOUNT BASIC INFO</b>
├─ Name: <code>{esc(basic.get("nickname"))}</code>
├─ UID: <code>{esc(basic.get("accountId"))}</code>
├─ Level: <code>{esc(basic.get("level"))}</code> (Exp: {esc(basic.get("exp"))})
├─ Region: <code>{esc(basic.get("region"))}</code>
├─ Likes: <code>{esc(basic.get("liked"))}</code>
├─ Honor Score: <code>{esc(data.get("creditScoreInfo", {}).get("creditScore"))}</code>
├─ Celebrity Status: <code>False</code>
├─ Evo Access Badge: <code>{esc(basic.get("badgeId"))}</code>
└─ Signature:
<code>{esc(social.get("signature"))}</code>

┌ 🎮 <b>ACCOUNT ACTIVITY</b>
├─ Most Recent OB: <code>{esc(basic.get("releaseVersion"))}</code>
├─ Fire Pass: <code>N/A</code>
├─ Current BP Badges: <code>{esc(basic.get("badgeCnt"))}</code>
├─ Account Type: <code>{esc(basic.get("accountType"))}</code>
├─ BR Rank: <code>{esc(basic.get("rank"))}</code> ({esc(basic.get("rankingPoints"))})
├─ CS Points: <code>{esc(basic.get("csRankingPoints"))}</code>
├─ Created At: <code>{format_time(basic.get("createAt"))}</code>
└─ Last Login: <code>{format_time(basic.get("lastLoginAt"))}</code>

┌ 👕 <b>ACCOUNT OVERVIEW</b>
├─ Avatar & Banner: <code>{esc(basic.get("bannerId"))}</code>
├─ Equipped Gun ID: <code>{esc(basic.get("weaponSkinShows"))}</code>
├─ Equipped Anime ID: <code>N/A</code>
└─ Transform Animation ID: <code>N/A</code>

┌ 🐾 <b>PET DETAILS</b>
├─ Equipped?: <code>{esc(pet.get("isSelected"))}</code>
├─ Pet Name: <code>{esc(pet.get("name"))}</code>
├─ Pet Type: <code>{esc(pet.get("id"))}</code>
├─ Pet Exp: <code>{esc(pet.get("exp"))}</code>
├─ IsSelected: <code>{esc(pet.get("isSelected"))}</code>
└─ Pet Level: <code>{esc(pet.get("level"))}</code>

┌ 🛡️ <b>GUILD INFO</b>
├─ Guild Name: <code>{esc(clan.get("clanName"))}</code>
├─ Guild ID: <code>{esc(clan.get("clanId"))}</code>
├─ Guild Level: <code>{esc(clan.get("clanLevel"))}</code>
├─ Guild Capacity: <code>{esc(clan.get("capacity"))}</code>
├─ Live Members: <code>{esc(clan.get("memberNum"))}</code>
└─ Leader Info:
 ├─ Leader Name: <code>{esc(captain.get("nickname"))}</code>
 ├─ Leader UID: <code>{esc(captain.get("accountId"))}</code>
 ├─ Leader Level: <code>{esc(captain.get("level"))}</code> (Exp: {esc(captain.get("exp"))})
 ├─ Leader Title: <code>{esc(captain.get("title"))}</code>
 ├─ Leader Current BP Badges: <code>{esc(captain.get("badgeCnt"))}</code>
 ├─ Leader BR Points: <code>{esc(captain.get("rank"))}</code>
 └─ Leader CS Points: <code>{esc(captain.get("csRankingPoints"))}</code>

┌ 🛠️ <b>EXTRA INFO</b>
├─ Release Version: <code>{esc(basic.get("releaseVersion"))}</code>
├─ Show BR Rank: <code>{esc(basic.get("showBrRank"))}</code>
├─ Show CS Rank: <code>{esc(basic.get("showCsRank"))}</code>
└─ External Icon Info:
 ├─ Status: <code>{esc(basic.get("externalIconInfo", {}).get("status"))}</code>
 └─ Show Type: <code>{esc(basic.get("externalIconInfo", {}).get("showType"))}</code>
"""

            bot.edit_message_text(
                text,
                message.chat.id,
                msg.message_id,
                parse_mode="HTML"
            )

        else:
            bot.edit_message_text(
                f"❌ API Error: {response.status_code}",
                message.chat.id,
                msg.message_id
            )

    except Exception as e:
        bot.reply_to(message, f"❌ Error:\n{str(e)}")
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
# =========================
# HELP PAGES (5 COMMANDS EACH PAGE)
# =========================

HELP_PAGES = [

# PAGE 1
"""
🏠 <b>FF_TG_INSTA_INFO BOT</b>

━━━━━━━━━━━━━━━━━━

📖 <b>COMMAND LIST — PAGE 1</b>

🎮 <b>/get PLAYER_UID</b>
➤ Get Free Fire player info

🔐 <b>/access_to_jwt ACCESS_TOKEN</b>
➤ Convert access token to JWT

👤 <b>/token GUEST_ID GUEST_PASSWORD</b>
➤ Generate JWT + Access Token

📸 <b>/insta_info INSTA_USERNAME</b>
➤ Get Instagram info

👤 <b>/info</b>
➤ Show Telegram user info

━━━━━━━━━━━━━━━━━━

➡️ Click NEXT
""",

# PAGE 2
"""
⚡ <b>COMMAND LIST — PAGE 2</b>

━━━━━━━━━━━━━━━━━━

✏️ <b>/change_vio ACCESS_TOKEN BIO</b>
➤ Change Free Fire bio

👤 <b>/my_tg_info</b>
➤ Show your Telegram info

➕ <b>/add_frnd_guest GUEST_ID GUEST_PASS FRIEND_UID</b>
➤ Send FF friend request

❓ <b>/help</b>
➤ Open help menu

🚀 <b>/start</b>
➤ Start the bot

━━━━━━━━━━━━━━━━━━

➡️ More commands coming soon...
""",

# PAGE 3
"""
🔥 <b>BOT FEATURES</b>

━━━━━━━━━━━━━━━━━━

✅ Free Fire Info
✅ JWT Generator
✅ Instagram Info
✅ Telegram Info
✅ Bio Changer
✅ Friend Request Sender

━━━━━━━━━━━━━━━━━━

🤖 Developed For:
• FF INFO
• TG INFO
• INSTA INFO

━━━━━━━━━━━━━━━━━━

🚀 Add Bot To Your Group
"""
]

# =========================
# BUTTON SYSTEM
# =========================

def help_buttons(page):

    markup = InlineKeyboardMarkup(row_width=2)

    buttons = []

    if page > 0:
        buttons.append(
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data=f"help_{page-1}"
            )
        )

    if page < len(HELP_PAGES) - 1:
        buttons.append(
            InlineKeyboardButton(
                "➡️ Next",
                callback_data=f"help_{page+1}"
            )
        )

    markup.add(*buttons)

    # last page extra button
    if page == len(HELP_PAGES) - 1:
        markup.add(
            InlineKeyboardButton(
                "➕ Add Me To Your Group",
                url="https://t.me/ff_insta_tg_tool_bot?startgroup=true"
            )
        )

    return markup

# =========================
# START COMMAND
# =========================

@bot.message_handler(commands=['start'])
def start_command(message):
    save_user(message.from_user)
    import html

    user = message.from_user

    first_name = html.escape(user.first_name or "N/A")
    last_name = html.escape(user.last_name or "")
    username = f"@{user.username}" if user.username else "N/A"
    user_id = user.id

    welcome_text = f"""
👋 <b>WELCOME TO FF_TG_INSTA_INFO BOT</b>

━━━━━━━━━━━━━━━━━━

👤 <b>YOUR INFO</b>

• Name : <code>{first_name} {last_name}</code>
• Username : <code>{username}</code>
• User ID : <code>{user_id}</code>

━━━━━━━━━━━━━━━━━━

🤖 <b>BOT FEATURES</b>

✅ Free Fire Info
✅ JWT Generator
✅ Instagram Info
✅ Telegram Info
✅ Bio Changer

━━━━━━━━━━━━━━━━━━

📖 <b>COMMAND LIST — PAGE 1</b>

🎮 <b>/get UID</b>
➤ Get Free Fire player info

🔐 <b>/access_to_jwt TOKEN</b>
➤ Convert access token to JWT

👤 <b>/token UID PASSWORD</b>
➤ Generate JWT + Access Token

📸 <b>/insta_info USERNAME</b>
➤ Get Instagram info

👤 <b>/info</b>
➤ Show Telegram user info
"""

    # buttons
    markup = help_buttons(0)

    try:

        photos = bot.get_user_profile_photos(user.id)

        # যদি profile photo থাকে
        if photos.total_count > 0:

            bot.send_photo(
                message.chat.id,
                photos.photos[0][-1].file_id,
                caption=welcome_text,
                parse_mode="HTML",
                reply_markup=markup
            )

        else:

            bot.send_message(
                message.chat.id,
                welcome_text,
                parse_mode="HTML",
                reply_markup=markup
            )

    except:

        bot.send_message(
            message.chat.id,
            welcome_text,
            parse_mode="HTML",
            reply_markup=markup
        )

# =========================
# HELP COMMAND
# =========================

@bot.message_handler(commands=['help'])
def help_command(message):
    save_user(message.from_user)
    bot.send_message(
        message.chat.id,
        HELP_PAGES[0],
        parse_mode="HTML",
        reply_markup=help_buttons(0)
    )

# =========================
# CALLBACK SYSTEM
# =========================

@bot.callback_query_handler(func=lambda call: call.data.startswith("help_"))
def callback_help(call):

    try:

        page = int(call.data.split("_")[1])

        # pages
        pages = HELP_PAGES.copy()

        # first page dynamic user info
        user = call.from_user

        import html

        first_name = html.escape(user.first_name or "N/A")
        last_name = html.escape(user.last_name or "")
        username = f"@{user.username}" if user.username else "N/A"
        user_id = user.id

        pages[0] = f"""
👋 <b>WELCOME TO FF_TG_INSTA_INFO BOT</b>

━━━━━━━━━━━━━━━━━━

👤 <b>YOUR INFO</b>

• Name : <code>{first_name} {last_name}</code>
• Username : <code>{username}</code>
• User ID : <code>{user_id}</code>

━━━━━━━━━━━━━━━━━━

📖 <b>COMMAND LIST — PAGE 1</b>

🎮 <b>/get UID</b>
➤ Get Free Fire player info

❤️<b> /like REGION UID </b>
➤ Send likes Your free fire id 

🔐 <b>/access_to_jwt TOKEN</b>
➤ Convert access token to JWT

👤 <b>/token UID PASSWORD</b>
➤ Generate JWT + Access Token

📸 <b>/insta_info USERNAME</b>
➤ Get Instagram info

👤 <b>/info</b>
➤ Show Telegram user info
"""

        # photo message হলে caption edit করবে
        if call.message.content_type == "photo":

            bot.edit_message_caption(
                caption=pages[page],
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML",
                reply_markup=help_buttons(page)
            )

        else:

            bot.edit_message_text(
                pages[page],
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=help_buttons(page)
            )

        bot.answer_callback_query(call.id)

    except Exception as e:

        bot.answer_callback_query(
            call.id,
            f"Error: {str(e)}"
        )
# 🔥 যখন bot group এ add হবে
@bot.message_handler(content_types=['new_chat_members'])
def welcome_group(message):
    for user in message.new_chat_members:
        if user.id == bot.get_me().id:
            bot.send_message(
                message.chat.id,
                "🤖 Thanks for adding me!\n\nUse /help to see all commands 🚀"
            )

# =========================
# ADMIN ADD LVL UP
# =========================

@bot.message_handler(commands=['admin_add_lvl_up'])
def admin_add_lvl_up(message):

    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ You are not admin")
        return

    try:
        args = message.text.split()

        if len(args) < 2:
            bot.reply_to(message, "❌ Usage:\n/admin_add_lvl_up UID")
            return

        uid = args[1]

        msg = bot.reply_to(message, "⏳ Saving player EXP...")

        info = get_player_exp(uid)

        if not info:
            bot.edit_message_text(
                "❌ Failed to fetch player info",
                message.chat.id,
                msg.message_id
            )
            return

        exp = int(info["exp"])

        now = int(time.time())

        cursor.execute("""
        INSERT OR REPLACE INTO lvlup(uid, exp, added_time)
        VALUES (?, ?, ?)
        """, (uid, exp, now))

        conn.commit()

        text = f"""
✅ <b>LEVEL TRACKING ADDED</b>

👤 Name: <code>{info['name']}</code>
🆔 UID: <code>{uid}</code>

📊 Saved EXP: <code>{exp}</code>

⏰ Tracking Time:
<code>6 Hours</code>
"""

        bot.edit_message_text(
            text,
            message.chat.id,
            msg.message_id,
            parse_mode="HTML"
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error:\n{str(e)}")

# =========================
# LEVEL STATUS
# =========================

@bot.message_handler(commands=['lvl_status'])
def lvl_status(message):

    try:
        args = message.text.split()

        if len(args) < 2:
            bot.reply_to(message, "❌ Usage:\n/lvl_status UID")
            return

        uid = args[1]

        cursor.execute("SELECT exp, added_time FROM lvlup WHERE uid=?", (uid,))
        row = cursor.fetchone()

        if not row:
            bot.reply_to(message, "❌ UID not found in database")
            return

        saved_exp = row[0]
        added_time = row[1]

        now = int(time.time())

        passed = now - added_time

        remain = 21600 - passed

        if remain <= 0:
            cursor.execute("DELETE FROM lvlup WHERE uid=?", (uid,))
            conn.commit()

            bot.reply_to(message, "⌛ Tracking expired")
            return

        info = get_player_exp(uid)

        if not info:
            bot.reply_to(message, "❌ Failed to fetch player info")
            return

        current_exp = int(info["exp"])

        gained = current_exp - saved_exp

        hours = remain // 3600
        minutes = (remain % 3600) // 60

        bar, percent = make_progress_bar(remain)

        text = f"""
🎮 <b>LEVEL UP STATUS</b>

👤 Name: <code>{info['name']}</code>
├─ UID: <code>{uid}</code>
├─ Level: <code>{info['level']}</code> (Exp: {current_exp})
├─ Region: <code>{info['region']}</code>
├─ Likes: <code>{info['likes']}</code>
└─ Honor Score: <code>{info['honor']}</code>

━━━━━━━━━━━━━━

📦 Saved EXP:
<code>{saved_exp}</code>

📈 Current EXP:
<code>{current_exp}</code>

🚀 EXP Gained:
<code>{gained}</code>

━━━━━━━━━━━━━━

⏳ Time Left:
<code>{hours}h {minutes}m</code>

📊 Progress:
<code>{bar}</code> {percent}%

━━━━━━━━━━━━━━
"""

        bot.reply_to(
            message,
            text,
            parse_mode="HTML"
        )

    except Exception as e:
        bot.reply_to(message, f"❌ Error:\n{str(e)}")
# =========================
# FREE FIRE LIKE COMMAND
# =========================

@bot.message_handler(commands=['like'])
def send_like(message):
    try:
        args = message.text.split()

        if len(args) < 3:
            bot.reply_to(
                message,
                "❌ Usage:\n/like {region} {uid}"
            )
            return

        region = args[1]
        uid = args[2]

        msg = bot.reply_to(
            message,
            "⏳ <b>Sending Likes please wait...</b>\n\nঅপেক্ষা করতে বলেছি দেখে কি রাগ করলা 😅"
        )

        url = f"https://mypremiumlikeblqbla.vercel.app/like?uid={uid}"

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            bot.edit_message_text(
                "⏳ <b>Api server slow\nদয়া করে কিছুক্ষণ পর ট্রাই করুন।\nরাগ করলা</b> 😅",
                message.chat.id,
                msg.message_id
            )
            return

        data = response.json()

        # যদি status 2 বা max like হয়
        if data.get("status") == 2:
            bot.edit_message_text(
                "<b>আপনি আপনার আইডি already maxlike নিয়ে ফেলেছেন।\nরাগ করলেন</b> 😅\n━━━━━━━━━━━━━━\n\n"
                f"• Likes After : {data.get('LikesafterCommand', 'N/A')}\n"
                f"• Likes Before : {data.get('LikesbeforeCommand', 'N/A')}\n"
                f"• Player Name : {data.get('PlayerNickname', 'N/A')}\n"
                f"• UID : {data.get('UID', 'N/A')}\n\n━━━━━━━━━━━━━━",
                message.chat.id,
                msg.message_id
            )
            return

        # সাধারণ like success
        text = "❤️ <b>LIKE SENT SUCCESSFULLY\nএত কম লাইক দিছি দেখেকি রাগ করলা 😅</b>\n\n━━━━━━━━━━━━━━\n"

        if data.get("LikesGivenByAPI", 0) != 0:
            text += f"• <b>Likes Given</b> : <code>{data.get('LikesGivenByAPI')}</code>\n"

        text += f"• <b>Likes After</b> : <code>{data.get('LikesafterCommand', 'N/A')}</code>\n"
        text += f"• <b>Likes Before</b> : <code>{data.get('LikesbeforeCommand', 'N/A')}</code>\n"
        text += f"• <b>Player Name</b> : <code>{data.get('PlayerNickname', 'N/A')}</code>\n"
        text += f"• <b>UID</b> : <code>{data.get('UID', 'N/A')}</code>\n"
        text += "\n━━━━━━━━━━━━━━"

        bot.edit_message_text(
            text,
            message.chat.id,
            msg.message_id,
            parse_mode="HTML"
        )

    except Exception as e:
        bot.reply_to(
            message,
            f"❌ Error:\n{str(e)}"
        )

#instagram info comand
@bot.message_handler(commands=['insta_info'])
def insta_info(message):
    try:
        args = message.text.split(" ", 1)

        if len(args) < 2:
            bot.reply_to(message, "❌ Usage:\n/insta_info {username}")
            return

        username = args[1]
        msg = bot.reply_to(message, "⏳ Fetching Instagram Info...")

        url = f"https://xerox-insta-info.vercel.app/api/userinfo?username={username}&api_key=XEORX"
        response = requests.get(url, timeout=20)

        if response.status_code == 200:

            # 🔥 Force JSON load (fix issue)
            import json
            data = json.loads(response.text)

            # ❌ remove unwanted keys
            for k in ["API_OWNER", "TALEGRAM"]:
                data.pop(k, None)

            def g(k):
                return data.get(k, "N/A")

            formatted = f"""
            📸 <b>Instagram Profile</b>

            👤 <b>Basic Info</b>
            • Username : <code>{g('username')}</code>
            • Full Name : <code>{g('full_name')}</code>
            • User ID : <code>{g('user_id')}</code>

            📝 <b>Bio</b>
            {g('biography')}

            📊 <b>Stats</b>
            • Followers : <code>{g('followers')}</code>
            • Following : <code>{g('following')}</code>
            • Posts : <code>{g('posts_count')}</code>

            🔒 <b>Account Info</b>
            • Private : <code>{g('is_private')}</code>
            • Verified : <code>{g('is_verified')}</code>

            🔗 <b>Profile</b>
https://instagram.com/{g('username')}
"""

            # 🖼 photo + caption
            bot.send_photo(
                message.chat.id,
                g("profile_pic"),
                caption=formatted,
                parse_mode="HTML"
            )

            bot.delete_message(message.chat.id, msg.message_id)

        else:
            bot.edit_message_text(
                f"❌ API Error: {response.status_code}",
                message.chat.id,
                msg.message_id
            )

    except Exception as e:
        bot.reply_to(message, f"❌ Error:\n{str(e)}")
@bot.message_handler(commands=['change_vio'])
def change_vio(message):
    try:
        args = message.text.split(" ", 2)

        if len(args) < 3:
            bot.reply_to(message, "❌ Usage:\n/change_vio {token} {bio}")
            return

        token = args[1]
        bio = args[2]

        msg = bot.reply_to(message, "⏳ Updating Bio...")

        url = f"https://long-bio-ob53.vercel.app/send_bio?token={token}&bio={bio}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            try:
                json_data = response.json()

                formatted = "✏️ *Bio Update Result*\n\n"

                for key, value in json_data.items():
                    if key.lower() in ["owner", "api_owner"]:
                        continue

                    formatted += f"• *{key}* : `{value}`\n"

                bot.edit_message_text(
                    formatted,
                    message.chat.id,
                    msg.message_id,
                    parse_mode="Markdown"
                )

            except:
                bot.edit_message_text(
                    f"✅ Result:\n\n`{response.text}`",
                    message.chat.id,
                    msg.message_id,
                    parse_mode="Markdown"
                )

        else:
            bot.edit_message_text(
                f"❌ API Error: {response.status_code}",
                message.chat.id,
                msg.message_id
            )

    except Exception as e:
        bot.reply_to(message, f"❌ Error:\n{str(e)}")
#all user database save
@bot.message_handler(func=lambda m: m.text and m.text.startswith("/"))
def auto_save_users(message):

    try:

        # save user
        save_user(message.from_user)

        # save group
        if message.chat.type in ["group", "supergroup"]:
            save_group(message.chat.id)

    except Exception as e:
        print("AUTO SAVE ERROR:", e)
# =========================
# AUTO FINISH CHECKER
# =========================

import threading

def auto_check_lvlup():

    while True:

        try:

            current_time = int(time.time())

            cursor.execute(
                "SELECT uid, exp, added_time FROM lvlup"
            )

            rows = cursor.fetchall()

            for row in rows:

                uid = row[0]
                old_exp = int(row[1])
                added_time = int(row[2])

                passed = current_time - added_time

                # 6 hour completed
                if passed >= 21600:

                    info = get_player_exp(uid)

                    if info:

                        current_exp = int(info.get("exp", 0))

                        gained = current_exp - old_exp

                        if gained < 0:
                            gained = 0

                        text = f"""
🎉 <b>LEVEL UP TRACKING FINISHED</b>

👤 Name: <code>{info['name']}</code>
├─ UID: <code>{uid}</code>
├─ Level: <code>{info['level']}</code>
├─ Region: <code>{info['region']}</code>
└─ Honor Score: <code>{info['honor']}</code>

━━━━━━━━━━━━━━

📦 Old EXP:
<code>{old_exp}</code>

📈 Current EXP:
<code>{current_exp}</code>

🚀 EXP Gained:
<code>{gained}</code>

━━━━━━━━━━━━━━

📊 Status:
<code>██████████</code> 100%

✅ 6 Hours Completed
"""

                        # send all users
                        cursor.execute("SELECT user_id FROM users")

                        users = cursor.fetchall()

                        for u in users:
                            try:
                                bot.send_message(
                                    u[0],
                                    text,
                                    parse_mode="HTML"
                                )
                            except:
                                pass

                        # send all groups
                        cursor.execute("SELECT chat_id FROM groups")

                        groups = cursor.fetchall()

                        for g in groups:
                            try:
                                bot.send_message(
                                    g[0],
                                    text,
                                    parse_mode="HTML"
                                )
                            except:
                                pass

                    # delete after completed
                    cursor.execute(
                        "DELETE FROM lvlup WHERE uid=?",
                        (uid,)
                    )

                    conn.commit()

        except Exception as e:
            print("AUTO CHECK ERROR:", e)

        time.sleep(60)


# background thread
threading.Thread(
    target=auto_check_lvlup,
    daemon=True
).start()

# =========================
# BOT START FUNCTION
# =========================

def run_bot():
    global bot_running

    if not bot_running:
        bot_running = True

        try:
            print("🤖 Bot Started...")
            bot.infinity_polling()

        except Exception as e:
            print("BOT ERROR:", e)

        finally:
            bot_running = False


# =========================
# FLASK API
# =========================

@app.route("/")
def home():
    return "Flask Bot Server Running"


@app.route("/on")
def bot_on():
    global bot_thread, bot_running

    if bot_running:
        return "✅ Bot Already Running"

    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    return "🟢 Bot Started"


@app.route("/off")
def bot_off():
    global bot_running

    try:
        bot.stop_polling()
        bot_running = False

        return "🔴 Bot_Stopped"

    except Exception as e:
        return f"Error: {e}"


# =========================
# FLASK RUN
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

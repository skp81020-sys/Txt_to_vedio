import os
import sys
import asyncio
import requests
import subprocess
import time
import instaloader

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web, ClientSession
from vars import API_ID, API_HASH, BOT_TOKEN, WEBHOOK, PORT, CLASSPLUS_TOKENS, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD
from utils import progress_bar, TokenManager, get_classplus_signed_url
from style import Ashu

# Initialize Token Manager with multiple tokens
token_manager = TokenManager(CLASSPLUS_TOKENS)

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Define aiohttp routes for webhook
routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("https://github.com/AshutoshGoswami24")

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

@bot.on_message(filters.command(["start"]))
async def account_login(bot: Client, m: Message):
    editable = await m.reply_text(
       Ashu.START_TEXT,
       reply_markup=InlineKeyboardMarkup([
           [
               InlineKeyboardButton("✜ ᴀsʜᴜᴛᴏsʜ ɢᴏsᴡᴀᴍɪ 𝟸𝟺 ✜", url="https://t.me/AshutoshGoswami24")
           ],
           [
               InlineKeyboardButton("🦋 𝐅𝐨𝐥𝐥𝐨𝐰 𝐌𝐞 🦋", url="https://t.me/AshuSupport")
           ]
       ])
    )

@bot.on_message(filters.command("stop"))
async def restart_handler(_, m):
    await m.reply_text("♦ 𝐒𝐭𝐨𝐩𝐩𝐞𝐭 ♦", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command(["upload"]))
async def upload_handler(bot: Client, m: Message):
    editable = await m.reply_text('sᴇɴᴅ ᴍᴇ .ᴛxᴛ ғɪʟᴇ  ⏍')
    input_msg: Message = await bot.listen(editable.chat.id)
    x = await input_msg.download()
    await input_msg.delete(True)

    try:
       with open(x, "r") as f:
           content = f.read()
       content = content.split("\n")
       links = []
       for i in content:
           if i.strip():
               links.append(i)
       os.remove(x)
    except Exception as e:
       await m.reply_text(f"∝ 𝐈𝐧𝐯𝐚𝐥𝐢𝐝 ᴜʀʟ ғɪʟᴇ.\nError: {str(e)}")
       os.remove(x)
       return

    await editable.edit(f"ɪɴ ᴛxᴛ ғɪʟᴇ ᴛɪᴛʟᴇ ʟɪɴᴋ 🔗** **{len(links)}**\n\nsᴇɴᴅ ғʀᴏᴍ  ᴡʜᴇʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ɪɴɪᴛᴀʟ ɪs `1`")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)

    await editable.edit("∝ 𝐍𝐨𝐰 𝐏𝐥𝐞𝐚𝐬𝐞 𝐒𝐞𝐧𝐝 𝐌𝐞 𝐘𝐨𝐮𝐫 𝐁𝐚𝐭𝐜𝐡 𝐍𝐚𝐦𝐞")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)

    await editable.edit(Ashu.Q1_TEXT)
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    await input2.delete(True)

    try:
        if raw_text2 == "144":
            res = "256x144"
        elif raw_text2 == "240":
            res = "426x240"
        elif raw_text2 == "360":
            res = "640x360"
        elif raw_text2 == "480":
            res = "854x480"
        elif raw_text2 == "720":
            res = "1280x720"
        elif raw_text2 == "1080":
            res = "1920x1080"
        else:
            res = "UN"
    except Exception:
        res = "UN"

    await editable.edit(Ashu.C1_TEXT)
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)

    highlighter = f"️ ⁪⁬⁮⁮⁮"
    if raw_text3 == 'Robin':
        MR = highlighter
    else:
        MR = raw_text3

    await editable.edit(Ashu.T1_TEXT)
    input6 = await bot.listen(editable.chat.id)
    raw_text6 = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = input6.text
    if thumb.startswith("http://") or thumb.startswith("https://"):
        subprocess.getoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb = "no"

    if len(links) == 1:
        count = 1
    else:
        count = int(raw_text)

    for i, url in enumerate(links):
        name1 = url.replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
        name = f'{str(count).zfill(3)}) {name1[:60]}'

        try:
            if 'videos.classplusapp' in url or 'classplusapp' in url:
                await m.reply_text(f"🔐 Resolving ClassPlus URL...")
                try:
                    # Try primary method with token rotation
                    url = get_classplus_signed_url(url, token_manager)
                    await m.reply_text(f"✅ URL resolved!")
                except Exception as cp_error:
                    await m.reply_text(f"⚠️ Token rotation failed: {str(cp_error)[:50]}...")
                    # Fallback to direct API call
                    headers = {
                        'x-access-token': CLASSPLUS_TOKENS[0] if CLASSPLUS_TOKENS else '',
                        'api-version': '8',
                        'accept-encoding': 'gzip',
                        'authority': 'api.classplusapp.com'
                    }
                    response = requests.get(
                        f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}',
                        headers=headers
                    )
                    if response.status_code == 403:
                        await m.reply_text("🚫 Token expired or invalid. Please check your CLASSPLUS_TOKENS.")
                        continue
                    url = response.json().get('url', url)

            elif 'instagram.com' in url or 'instagr.am' in url:
                await m.reply_text(f"🔐 Fetching Instagram post...")
                try:
                    L = instaloader.Instaloader()
                    L.login(user=INSTAGRAM_USERNAME, passwd=INSTAGRAM_PASSWORD)
                    post = instaloader.Post.from_shortcode(L.context, url.split('/')[-2])
                    media = post.url
                    await m.reply_text(f"✅ Instagram post fetched!")
                except Exception as ig_error:
                    await m.reply_text(f"⚠️ Failed to fetch Instagram post: {str(ig_error)[:50]}...")
                    continue

            # Prepare Captions
            cc = f'**[ 🎥 ] Vid_ID:** {str(count).zfill(3)}.** {name1}{MR}.mkv\n✉️ 𝐁𝐚𝐭𝐜𝐡 » **{raw_text0}**'

            # yt-dlp Format Selection
            ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"

            # Command Construction
            cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            # Download video using helper
            Show = f"❊⟱ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 ⟱❊ »\n\n📝 𝐍𝐚𝐦𝐞 » `{name}\n⌨ 𝐐𝐮𝐥𝐢𝐭𝐲 » {raw_text2}`\n\n**🔗 𝐔𝐑𝐋 »** `{url}`"
            prog = await m.reply_text(Show)

            res_file = await helper.download_video(url, cmd, name)
            filename = res_file

            await prog.delete(True)
            await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
            count += 1
            time.sleep(1)

        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg:
                error_msg += "\n\n💡 **Tip:** Token expired or invalid. Check CLASSPLUS_TOKENS in vars.py"
            await m.reply_text(
                f"⌘ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐈𝐧𝐭𝐞𝐫𝐫𝐮𝐩𝐭𝐞𝐝\n{error_msg}\n⌘ 𝐍𝐚𝐦𝐞 » {name}\n⌘ 𝐋𝐢𝐧𝐤 » `{url}`"
            )
            continue

    await m.reply_text("✅ 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐃𝐨𝐧𝐞")

async def main():
    """Start web server for webhook support"""
    if WEBHOOK:
        app = await web_server()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()
        print(f"🌐 Web server started on port {PORT}")

if __name__ == "__main__":
    print("""
    █░█░█ █▀█ █▀█ █▀▄ █▀▀ █▀█ ▄▀█ █▀▀ ▀█▀    ▄▀█ █▀ █░█ █░█ ▀█▀ █▀█ █▀ █░█  
    ▀▄▀▄▀ █▄█ █▄█ █▄▀ █▄▄ █▀▄ █▀█ █▀░ ░█░    █▀█ ▄█ █▀█ █▄█ ░█░ █▄█ ▄█ █▀█ """)

    async def start_bot():
        await bot.start()
        print("🤖 Bot started")

    async def start_web():
        await main()

    loop = asyncio.get_event_loop()
    try:
        loop.create_task(start_bot())
        loop.create_task(start_web())
        loop.run_forever()
    except KeyboardInterrupt:
        print("🛑 Stopped")
    finally:
        loop.stop()

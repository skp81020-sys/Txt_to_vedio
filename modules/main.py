import os
import re
import sys
import json
import time
import asyncio
import requests
import subprocess
import random
import glob
import urllib.parse

import core as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN, WEBHOOK, PORT
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput
from aiohttp import web

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from style import Ashu 

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

routes = web.RouteTableDef()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.0.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.0.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0",
]

# ClassPlus API Configuration
CLASSPLUS_HEADERS = {
    'x-access-token': 'eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MzgzNjkyMTIsIm9yZ0lkIjoyNjA1LCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwODI3NzQyODkiLCJuYW1lIjoiQWNlIiwiZW1haWwiOm51bGwsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjpudWxsLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpYXQiOjE2NDMyODE4NzcsImV4cCI6MTY0Mzg4NjY3N30.hM33P2ai6ivdzxPPfm01LAd4JWv-vnrSxGXqvCirCSpUfhhofpeqyeHPxtstXwe0',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.0.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://web.classplusapp.com',
    'Referer': 'https://web.classplusapp.com/',
}

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("https://github.com/AshutoshGoswami24")

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

@bot.on_message(filters.command(["start"]))
async def account_login(bot: Client, m: Message):
    await m.reply_text(
       Ashu.START_TEXT, reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("✜ ᴀsʜᴜᴛᴏsʜ ɢᴏsᴡᴀᴍɪ 𝟸𝟺 ✜", url="https://t.me/AshutoshGoswami24")],
                [InlineKeyboardButton("🦋 𝐅𝐨𝐥𝐥𝐨𝐰 𝐌𝐞 🦋", url="https://t.me/AshuSupport")]
            ]))

@bot.on_message(filters.command("stop"))
async def restart_handler(_, m):
    await m.reply_text("♦ 𝐒𝐭𝐨𝐩𝐩𝐞𝐭 ♦", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

def clean_filename(name):
    """Clean filename for safe file operations"""
    name = str(name)
    # Remove invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace multiple spaces with single
    name = re.sub(r'\s+', ' ', name).strip()
    # Limit length
    return name[:100]

async def get_classplus_stream_url(original_url):
    """
    Get fresh stream URL from ClassPlus API
    """
    try:
        # Extract video ID from URL
        # URL format: https://media-cdn.classplusapp.com/.../master.m3u8
        # Or: classplusapp://... or other formats
        
        # Try to get fresh URL from API
        api_url = f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={urllib.parse.quote(original_url)}'
        
        response = requests.get(
            api_url,
            headers=CLASSPLUS_HEADERS,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'url' in data and data['url']:
                return data['url']
        
        # If API fails, try alternative method
        # Extract direct token from URL if present
        if 'token=' in original_url:
            return original_url
            
        return None
        
    except Exception as e:
        print(f"ClassPlus API Error: {e}")
        return None

async def download_with_ytdlp_classplus(url, name, resolution="480", max_retries=3):
    """
    Specialized downloader for ClassPlus with anti-403 measures
    """
    clean_name = clean_filename(name)
    
    for attempt in range(max_retries):
        try:
            # Get fresh URL if it's ClassPlus
            fresh_url = await get_classplus_stream_url(url)
            if fresh_url:
                download_url = fresh_url
                print(f"Using fresh URL: {download_url[:100]}...")
            else:
                download_url = url
            
            # yt-dlp command with ClassPlus-specific options
            cmd = [
                "yt-dlp",
                "--no-check-certificates",
                "--user-agent", random.choice(USER_AGENTS),
                "--add-header", f"Referer:https://web.classplusapp.com/",
                "--add-header", "Origin:https://web.classplusapp.com",
                "--add-header", f"Authorization:Bearer {CLASSPLUS_HEADERS['x-access-token']}",
                "--retries", "10",
                "--fragment-retries", "10",
                "--socket-timeout", "30",
                "--force-ipv4",
                "--no-warnings",
                "--allow-unplayable-formats",  # Important for DRM/encrypted streams
                "--fixup", "never",
                "-f", f"b[height<={resolution}]/bv[height<={resolution}]+ba/b/bv+ba",
                "-o", f"{clean_name}.%(ext)s",
                download_url
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=600  # 10 minute timeout
            )
            
            stderr_str = stderr.decode() if stderr else ""
            
            if process.returncode == 0:
                # Find downloaded file
                possible_exts = ['.mp4', '.mkv', '.webm', '.ts', '.mov']
                for ext in possible_exts:
                    if os.path.exists(f"{clean_name}{ext}"):
                        return True, f"{clean_name}{ext}", None
                
                # Check for any matching file
                files = glob.glob(f"{clean_name}*")
                if files:
                    return True, files[0], None
                
                return False, None, "File not found after download"
            
            # Check for 403 error
            if "403" in stderr_str or "Forbidden" in stderr_str:
                if attempt < max_retries - 1:
                    wait_time = 3 * (attempt + 1)
                    print(f"403 Error, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                return False, None, f"403 Forbidden after {max_retries} attempts"
            
            return False, None, stderr_str
            
        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                return False, None, "Download timeout"
            await asyncio.sleep(5)
            
        except Exception as e:
            if attempt == max_retries - 1:
                return False, None, str(e)
            await asyncio.sleep(2)
    
    return False, None, "Max retries exceeded"

async def download_pdf_direct(url, output_path, max_retries=3):
    """Direct PDF download"""
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'application/pdf,*/*',
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=60, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True, None
            return False, "Empty file"
            
        except Exception as e:
            if attempt == max_retries - 1:
                return False, str(e)
            time.sleep(2 ** attempt)
    
    return False, "Max retries exceeded"

@bot.on_message(filters.command(["upload"]))
async def account_login(bot: Client, m: Message):
    editable = await m.reply_text('sᴇɴᴅ ᴍᴇ .ᴛxᴛ ғɪʟᴇ  ⏍')
    input_msg: Message = await bot.listen(editable.chat.id)
    x = await input_msg.download()
    await input_msg.delete(True)

    download_dir = f"./downloads/{m.chat.id}"
    os.makedirs(download_dir, exist_ok=True)
    original_dir = os.getcwd()
    os.chdir(download_dir)

    try:
        with open(x, "r", encoding="utf-8") as f:
            content = f.read()
        
        lines = [line.strip() for line in content.split("\n") if line.strip()]
        links = []
        for line in lines:
            if "://" in line:
                parts = line.split("://", 1)
                if len(parts) == 2:
                    links.append([parts[0], parts[1]])
        
        os.remove(x)
        
        if not links:
            await m.reply_text("∝ 𝐍𝐨 𝐯𝐚𝐥𝐢𝐝 𝐥𝐢𝐧𝐤𝐬 𝐟𝐨𝐮𝐧𝐝 𝐢𝐧 𝐟𝐢𝐥𝐞.")
            return
            
    except Exception as e:
        await m.reply_text(f"∝ 𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐟𝐢𝐥𝐞 𝐢𝐧𝐩𝐮𝐭.\nError: {str(e)}")
        if os.path.exists(x):
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
    
    res_map = {"144": "256x144", "240": "426x240", "360": "640x360", 
               "480": "854x480", "720": "1280x720", "1080": "1920x1080"}
    res = res_map.get(raw_text2, "UN")
    
    await editable.edit(Ashu.C1_TEXT)
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    
    highlighter = f"️ ⁪⁬⁮⁮⁮"
    MR = highlighter if raw_text3 == 'Robin' else raw_text3
   
    await editable.edit(Ashu.T1_TEXT)
    input6 = await bot.listen(editable.chat.id)
    raw_text6 = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = input6.text
    if thumb.startswith("http://") or thumb.startswith("https://"):
        getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb = "no"

    try:
        count = int(raw_text) if raw_text.isdigit() else 1
    except:
        count = 1

    failed_downloads = []
    success_count = 0

    try:
        for i in range(count - 1, len(links)):
            try:
                # Process URL
                url_part = links[i][1]
                url_part = (url_part
                    .replace("file/d/","uc?export=download&id=")
                    .replace("www.youtube-nocookie.com/embed", "youtu.be")
                    .replace("?modestbranding=1", "")
                    .replace("/view?usp=sharing",""))
                
                url = "https://" + url_part
                raw_name = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace("https", "").replace("http", "").strip()
                
                name1 = clean_filename(raw_name)
                display_name = f'{str(count).zfill(3)}) {name1[:60]}'
                file_safe_name = f'{str(count).zfill(3)})_{name1[:50]}'

                cc = f'**[ 🎥 ] Vid_ID:** {str(count).zfill(3)}.** {name1}{MR}.mkv\n✉️ 𝐁𝐚𝐭𝐜𝐡 » **{raw_text0}**'
                cc1 = f'**[ 📁 ] Pdf_ID:** {str(count).zfill(3)}. {name1}{MR}.pdf \n✉️ 𝐁𝐚𝐭𝐜𝐡 » **{raw_text0}**'

                # VisionIAS Handling
                if "visionias" in url:
                    try:
                        async with ClientSession() as session:
                            headers = {'User-Agent': random.choice(USER_AGENTS), 'Referer': 'http://www.visionias.in/'}
                            async with session.get(url, headers=headers) as resp:
                                text = await resp.text()
                                url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)
                    except Exception as e:
                        await m.reply_text(f"⚠️ VisionIAS Error: {str(e)}")
                        count += 1
                        continue

                # Google Drive
                if "drive" in url:
                    try:
                        ka = await helper.download(url, file_safe_name)
                        if os.path.exists(ka):
                            await bot.send_document(chat_id=m.chat.id, document=ka, caption=cc1)
                            success_count += 1
                            os.remove(ka)
                        else:
                            failed_downloads.append((display_name, "Drive failed"))
                    except Exception as e:
                        failed_downloads.append((display_name, f"Drive: {str(e)}"))
                    count += 1
                    continue
                
                # PDF Handling
                elif ".pdf" in url.lower():
                    prog = await m.reply_text(f"📄 Downloading PDF: {display_name}")
                    pdf_path = f"{file_safe_name}.pdf"
                    
                    success, error = await download_pdf_direct(url, pdf_path)
                    
                    if success and os.path.exists(pdf_path):
                        try:
                            await bot.send_document(chat_id=m.chat.id, document=pdf_path, caption=cc1)
                            success_count += 1
                            os.remove(pdf_path)
                        except Exception as e:
                            failed_downloads.append((display_name, f"Send: {str(e)}"))
                    else:
                        failed_downloads.append((display_name, error or "PDF failed"))
                    
                    await prog.delete()
                    count += 1
                    await asyncio.sleep(1)
                    continue
                
                # Video Handling (including ClassPlus)
                else:
                    is_classplus = "classplusapp.com" in url or "media-cdn.classplusapp.com" in url
                    
                    Show = f"❊⟱ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 ⟱❊ »\n\n📝 𝐍𝐚𝐦𝐞 » `{display_name}`\n⌨ 𝐐𝐮𝐥𝐢𝐭𝐲 » {raw_text2}\n{'🎓 ClassPlus' if is_classplus else ''}\n\n**🔗 𝐔𝐑𝐋 »** `{url[:60]}...`"
                    prog = await m.reply_text(Show)
                    
                    if is_classplus:
                        # Use specialized ClassPlus downloader
                        success, filename, error = await download_with_ytdlp_classplus(
                            url, file_safe_name, raw_text2
                        )
                    else:
                        # Regular download
                        ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]" if "youtu" in url else f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"
                        cmd = f"yt-dlp -f '{ytf}' '{url}' -o '{file_safe_name}.%(ext)s'"
                        success, filename, error = True, None, None
                        try:
                            res_file = await helper.download_video(url, cmd, file_safe_name)
                            filename = res_file
                        except Exception as e:
                            success, error = False, str(e)
                    
                    if success and filename and os.path.exists(filename):
                        await prog.delete()
                        await helper.send_vid(bot, m, cc, filename, thumb, display_name, prog)
                        success_count += 1
                        try:
                            os.remove(filename)
                        except:
                            pass
                    else:
                        failed_downloads.append((display_name, error or "Download failed"))
                        await prog.edit(f"❌ Failed: {display_name}\nError: {error}")
                    
                    count += 1
                    await asyncio.sleep(1)

            except Exception as e:
                failed_downloads.append((links[i][0] if i < len(links) else "Unknown", str(e)))
                await m.reply_text(f"⚠️ Error: {str(e)}")
                count += 1
                continue

    except Exception as e:
        await m.reply_text(f"Main Error: {str(e)}")
    
    # Report
    report = f"✅ 𝐃𝐨𝐧𝐞\n\n📊 𝐒𝐭𝐚𝐭𝐬:\n✓ Success: {success_count}\n✗ Failed: {len(failed_downloads)}"
    if failed_downloads:
        report += "\n\n❌ 𝐅𝐚𝐢𝐥𝐞𝐝:\n"
        for name, error in failed_downloads[:5]:
            report += f"• {name[:30]}: {error[:40]}\n"
    
    await m.reply_text(report)
    
    # Cleanup
    os.chdir(original_dir)
    import shutil
    shutil.rmtree(download_dir, ignore_errors=True)

async def main():
    if WEBHOOK:
        app = await web_server()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()
        print(f"Web server started on port {PORT}")

if __name__ == "__main__":
    print("""
    █░█░█ █▀█ █▀█ █▀▄ █▀▀ █▀█ ▄▀█ █▀▀ ▀█▀     ▄▀█ █▀ █░█ █░█ ▀█▀ █▀█ █▀ █░█   
    ▀▄▀▄▀ █▄█ █▄█ █▄▀ █▄▄ █▀▄ █▀█ █▀░ ░█░     █▀█ ▄█ █▀█ █▄█ ░█░ █▄█ ▄█ █▀█ """)

    async def start_bot():
        await bot.start()

    async def start_web():
        await main()

    loop = asyncio.get_event_loop()
    try:
        loop.create_task(start_bot())
        loop.create_task(start_web())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.stop()
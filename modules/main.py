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
import base64

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

bot = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
routes = web.RouteTableDef()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.0.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.0",
]

def get_fresh_classplus_token():
    """
    Generate fresh token or use working token
    """
    # Try multiple tokens
    tokens = [
        "eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MTg3MzYzNDMsIm9yZ0lkIjoyNTM0LCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwODI3NzQyODkiLCJuYW1lIjoiU3VkaGFuc2h1IiwiZW1haWwiOm51bGwsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjpudWxsLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpYXQiOjE3MDQ2MTQ2MDAsImV4cCI6MTcwNTIxOTQwMH0",
        "eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MzgzNjkyMTIsIm9yZ0lkIjoyNjA1LCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwODI3NzQyODkiLCJuYW1lIjoiQWNlIiwiZW1haWwiOm51bGwsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjpudWxsLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpYXQiOjE2NDMyODE4NzcsImV4cCI6MTY0Mzg4NjY3N30",
    ]
    return random.choice(tokens)

def get_classplus_headers():
    return {
        'x-access-token': get_fresh_classplus_token(),
        'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.0.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://web.classplusapp.com',
        'Referer': 'https://web.classplusapp.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("https://t.me/AshutoshGoswami24")

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

@bot.on_message(filters.command(["start"]))
async def account_login(bot: Client, m: Message):
    await m.reply_text(Ashu.START_TEXT, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("✜ ᴀsʜᴜᴛᴏsʜ ɢᴏsᴡᴀᴍɪ 𝟸𝟺 ✜", url="https://t.me/AshutoshGoswami24")],
        [InlineKeyboardButton("🦋 𝐅𝐨𝐥𝐥𝐨𝐰 𝐌𝐞 🦋", url="https://t.me/AshuSupport")]
    ]))

@bot.on_message(filters.command("stop"))
async def restart_handler(_, m):
    await m.reply_text("♦ 𝐒𝐭𝐨𝐩𝐩𝐞𝐭 ♦", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

def clean_filename(name):
    name = str(name)
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:80]

async def extract_classplus_video_id(url):
    """
    Extract video ID from various ClassPlus URL formats
    """
    patterns = [
        r'/lc/([a-zA-Z0-9-]+)/',  # /lc/761xg-4237129/
        r'/v2/([a-zA-Z0-9-]+)/',  # /v2/xyz-123/
        r'([a-f0-9-]{36})',       # UUID format
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

async def get_classplus_direct_url(m3u8_url, max_retries=3):
    """
    Get playable URL from ClassPlus m3u8
    """
    headers = get_classplus_headers()
    
    for attempt in range(max_retries):
        try:
            # Method 1: Try API endpoint
            api_base = "https://api.classplusapp.com/cams/uploader/video/jw-signed-url"
            encoded_url = urllib.parse.quote(m3u8_url, safe='')
            
            response = requests.get(
                f"{api_base}?url={encoded_url}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'url' in data and data['url']:
                    return data['url']
            
            # Method 2: Try alternative API
            video_id = await extract_classplus_video_id(m3u8_url)
            if video_id:
                alt_api = f"https://api.classplusapp.com/v2/course/content/get?content_id={video_id}"
                alt_response = requests.get(alt_api, headers=headers, timeout=30)
                if alt_response.status_code == 200:
                    alt_data = alt_response.json()
                    if 'data' in alt_data and 'url' in alt_data['data']:
                        return alt_data['data']['url']
            
            # Method 3: Direct m3u8 with headers
            return {
                'url': m3u8_url,
                'headers': {
                    'User-Agent': headers['User-Agent'],
                    'Referer': 'https://web.classplusapp.com/',
                    'Origin': 'https://web.classplusapp.com',
                    'Authorization': f"Bearer {headers['x-access-token']}"
                }
            }
            
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)
            continue
    
    return None

async def download_classplus_video(url, name, resolution="480", m=None):
    """
    Specialized ClassPlus downloader with multiple fallback methods
    """
    clean_name = clean_filename(name)
    
    # Get direct URL
    result = await get_classplus_direct_url(url)
    
    if not result:
        return False, None, "Failed to get valid URL"
    
    # Prepare download
    if isinstance(result, dict) and 'headers' in result:
        download_url = result['url']
        custom_headers = result['headers']
    else:
        download_url = result
        custom_headers = None
    
    print(f"Downloading from: {download_url[:100]}...")
    
    # Method 1: yt-dlp with custom headers
    cmd = [
        "yt-dlp",
        "--no-check-certificates",
        "--user-agent", USER_AGENTS[0],
        "--retries", "10",
        "--fragment-retries", "10",
        "--socket-timeout", "30",
        "--force-ipv4",
        "--no-warnings",
        "-f", f"b[height<={resolution}]/bv[height<={resolution}]+ba/b/bv+ba",
        "-o", f"{clean_name}.%(ext)s",
    ]
    
    # Add custom headers if available
    if custom_headers:
        for key, value in custom_headers.items():
            cmd.extend(["--add-header", f"{key}:{value}"])
    
    cmd.append(download_url)
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)
        
        if process.returncode == 0:
            # Find downloaded file
            for ext in ['.mp4', '.mkv', '.webm', '.ts']:
                filepath = f"{clean_name}{ext}"
                if os.path.exists(filepath):
                    return True, filepath, None
            
            files = glob.glob(f"{clean_name}*")
            if files:
                return True, files[0], None
        
        stderr_str = stderr.decode() if stderr else "Unknown error"
        
        # If yt-dlp failed with 403, try alternative method
        if "403" in stderr_str:
            return await download_with_ffmpeg(download_url, clean_name, custom_headers, resolution)
        
        return False, None, stderr_str
        
    except Exception as e:
        return False, None, str(e)

async def download_with_ffmpeg(url, name, headers, resolution):
    """
    Fallback download using ffmpeg
    """
    output_file = f"{name}.mp4"
    
    # Build ffmpeg command
    cmd = ["ffmpeg", "-y", "-i", url]
    
    # Add headers
    if headers:
        header_str = "\r\n".join([f"{k}: {v}" for k, v in headers.items()])
        cmd.extend(["-headers", header_str])
    
    cmd.extend([
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        output_file
    ])
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)
        
        if process.returncode == 0 and os.path.exists(output_file):
            return True, output_file, None
        
        return False, None, "FFmpeg failed"
        
    except Exception as e:
        return False, None, f"FFmpeg error: {str(e)}"

@bot.on_message(filters.command(["upload"]))
async def account_login(bot: Client, m: Message):
    editable = await m.reply_text('sᴇɴᴅ ᴍᴇ .ᴛxᴛ ғɪʟᴇ  ⏍')
    input_msg = await bot.listen(editable.chat.id)
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
            await m.reply_text("∝ 𝐍𝐨 𝐯𝐚𝐥𝐢𝐝 𝐥𝐢𝐧𝐤𝐬 𝐟𝐨𝐮𝐧𝐝.")
            return
            
    except Exception as e:
        await m.reply_text(f"∝ 𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐟𝐢𝐥𝐞.\nError: {str(e)}")
        return
    
    await editable.edit(f"**Total Links:** {len(links)}\n\nSend starting number (default: 1)")
    input0 = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)

    await editable.edit("Send Batch Name:")
    input1 = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    
    await editable.edit(Ashu.Q1_TEXT)
    input2 = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    await input2.delete(True)
    
    await editable.edit(Ashu.C1_TEXT)
    input3 = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    
    MR = f"️ ⁪⁬⁮⁮⁮" if raw_text3 == 'Robin' else raw_text3
   
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

    for i in range(count - 1, len(links)):
        try:
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

            # Check if ClassPlus URL
            is_classplus = any(x in url for x in ['classplusapp.com', 'media-cdn.classplusapp.com', 'cpvod.test'])
            
            if "drive" in url:
                try:
                    ka = await helper.download(url, file_safe_name)
                    if ka and os.path.exists(ka):
                        await bot.send_document(chat_id=m.chat.id, document=ka, caption=cc1)
                        success_count += 1
                        os.remove(ka)
                except Exception as e:
                    failed_downloads.append((display_name, f"Drive: {str(e)}"))
                count += 1
                continue
            
            elif ".pdf" in url.lower():
                try:
                    r = requests.get(url, headers={'User-Agent': USER_AGENTS[0]}, timeout=60)
                    pdf_path = f"{file_safe_name}.pdf"
                    with open(pdf_path, 'wb') as f:
                        f.write(r.content)
                    
                    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                        await bot.send_document(chat_id=m.chat.id, document=pdf_path, caption=cc1)
                        success_count += 1
                        os.remove(pdf_path)
                except Exception as e:
                    failed_downloads.append((display_name, f"PDF: {str(e)}"))
                count += 1
                continue
            
            else:  # Video
                prog = await m.reply_text(f"⬇️ Downloading: {display_name}{' (ClassPlus)' if is_classplus else ''}")
                
                if is_classplus:
                    success, filename, error = await download_classplus_video(url, file_safe_name, raw_text2, m)
                else:
                    # Regular video
                    ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"
                    cmd = f"yt-dlp -f '{ytf}' '{url}' -o '{file_safe_name}.%(ext)s'"
                    try:
                        res_file = await helper.download_video(url, cmd, file_safe_name)
                        success, filename, error = True, res_file, None
                    except Exception as e:
                        success, filename, error = False, None, str(e)
                
                if success and filename and os.path.exists(filename):
                    await prog.delete()
                    await helper.send_vid(bot, m, cc, filename, thumb, display_name, prog)
                    success_count += 1
                    try:
                        os.remove(filename)
                    except:
                        pass
                else:
                    failed_downloads.append((display_name, error or "Failed"))
                    await prog.edit(f"❌ Failed: {display_name}\nError: {error}")
                
                count += 1
                await asyncio.sleep(1)

        except Exception as e:
            failed_downloads.append((links[i][0] if i < len(links) else "Unknown", str(e)))
            count += 1
            continue

    # Report
    report = f"✅ 𝐃𝐨𝐧𝐞\n\n📊 𝐒𝐭𝐚𝐭𝐬:\n✓ Success: {success_count}\n✗ Failed: {len(failed_downloads)}"
    if failed_downloads:
        report += "\n\n❌ 𝐅𝐚𝐢𝐥𝐞𝐝:\n"
        for name, error in failed_downloads[:5]:
            report += f"• {name[:30]}: {str(error)[:40]}\n"
    
    await m.reply_text(report)
    
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

    loop = asyncio.get_event_loop()
    try:
        loop.create_task(bot.start())
        loop.create_task(main())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.stop()
# modules/main.py - COMPLETE FIXED VERSION
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
import shutil
import logging
import urllib.parse
from datetime import datetime

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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize bot
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

# ============== CLASSPLUS CONFIGURATION ==============
CLASSPLUS_TOKENS = [
    "eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MTg3MzYzNDMsIm9yZ0lkIjoyNTM0LCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwODI3NzQyODkiLCJuYW1lIjoiU3VkaGFuc2h1IiwiZW1haWwiOm51bGwsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjpudWxsLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpYXQiOjE3MDQ2MTQ2MDAsImV4cCI6MTcwNTIxOTQwMH0",
    "eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MzgzNjkyMTIsIm9yZ0lkIjoyNjA1LCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwODI3NzQyODkiLCJuYW1lIjoiQWNlIiwiZW1haWwiOm51bGwsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjpudWxsLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpYXQiOjE2NDMyODE4NzcsImV4cCI6MTY0Mzg4NjY3N30",
]

def get_classplus_headers():
    """Get fresh headers with random token"""
    return {
        'x-access-token': random.choice(CLASSPLUS_TOKENS),
        'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.0.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.0',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://web.classplusapp.com',
        'Referer': 'https://web.classplusapp.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }

# ============== WEB SERVER ==============
@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response({
        "status": "running",
        "bot": "Txt_to_Video_Bot",
        "github": "https://github.com/skp81020-sys"
    })

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

# ============== BOT COMMANDS ==============
@bot.on_message(filters.command(["start"]))
async def start_handler(bot: Client, m: Message):
    await m.reply_text(
        Ashu.START_TEXT if hasattr(Ashu, 'START_TEXT') else "🤖 **Bot Started!**\n\nSend /upload to begin.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✜ Developer ✜", url="https://t.me/AshutoshGoswami24")],
            [InlineKeyboardButton("📢 Updates", url="https://t.me/AshuSupport")]
        ])
    )

@bot.on_message(filters.command("stop"))
async def stop_handler(_, m):
    await m.reply_text("♦️ **Stopping Bot...**", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on_message(filters.command("status"))
async def status_handler(_, m):
    """Check bot status"""
    uptime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await m.reply_text(f"✅ **Bot Running**\n🕐 Time: {uptime}")

# ============== UTILITY FUNCTIONS ==============
def clean_filename(name):
    """Clean filename for safe file operations"""
    if not name:
        return "unknown"
    
    name = str(name)
    # Remove invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Remove control characters
    name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name)
    # Replace multiple spaces/dots
    name = re.sub(r'\s+', ' ', name).strip()
    name = re.sub(r'\.+', '.', name)
    # Limit length
    return name[:80].strip('.')

def safe_remove(filepath):
    """Safely remove file if exists"""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception as e:
        logger.error(f"Failed to remove {filepath}: {e}")
    return False

async def download_with_progress(url, output_path, chunk_size=8192):
    """Download file with progress tracking"""
    try:
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, stream=True, timeout=120)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
        
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except Exception as e:
        logger.error(f"Download error: {e}")
        return False

# ============== CLASSPLUS HANDLER ==============
async def get_classplus_stream_url(m3u8_url):
    """Get fresh stream URL from ClassPlus API"""
    headers = get_classplus_headers()
    
    try:
        # Try API endpoint
        encoded_url = urllib.parse.quote(m3u8_url, safe='')
        api_url = f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={encoded_url}'
        
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'url' in data and data['url']:
                logger.info("Got fresh URL from ClassPlus API")
                return data['url']
        
        # If API fails, return original with headers
        logger.warning("API failed, using original URL with headers")
        return {
            'url': m3u8_url,
            'headers': {
                'User-Agent': headers['User-Agent'],
                'Referer': 'https://web.classplusapp.com/',
                'Origin': 'https://web.classplusapp.com',
            }
        }
        
    except Exception as e:
        logger.error(f"ClassPlus API error: {e}")
        return None

async def download_video_ytdlp(url, name, resolution="480", is_classplus=False):
    """
    Universal video downloader with retry logic
    """
    clean_name = clean_filename(name)
    output_template = f"{clean_name}.%(ext)s"
    
    for attempt in range(3):
        try:
            cmd = [
                "yt-dlp",
                "--no-check-certificates",
                "--user-agent", random.choice(USER_AGENTS),
                "--retries", "10",
                "--fragment-retries", "10",
                "--socket-timeout", "30",
                "--force-ipv4",
                "--no-warnings",
                "--newline",
                "-f", f"b[height<={resolution}]/bv[height<={resolution}]+ba/b/bv+ba",
                "-o", output_template,
            ]
            
            # Add ClassPlus specific headers
            if is_classplus:
                result = await get_classplus_stream_url(url)
                if isinstance(result, dict):
                    download_url = result['url']
                    for key, value in result.get('headers', {}).items():
                        cmd.extend(["--add-header", f"{key}:{value}"])
                else:
                    download_url = result or url
                
                cmd.extend([
                    "--add-header", f"Authorization:Bearer {get_classplus_headers()['x-access-token']}",
                    "--add-header", "Referer:https://web.classplusapp.com/",
                ])
            else:
                download_url = url
            
            cmd.append(download_url)
            
            logger.info(f"Download attempt {attempt + 1}: {clean_name}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600)
            
            if process.returncode == 0:
                # Find downloaded file
                for ext in ['.mp4', '.mkv', '.webm', '.ts', '.mov']:
                    filepath = f"{clean_name}{ext}"
                    if os.path.exists(filepath):
                        return True, filepath, None
                
                # Check for any matching file
                files = glob.glob(f"{clean_name}*")
                if files:
                    return True, files[0], None
                
                return False, None, "File not found after download"
            
            stderr_str = stderr.decode() if stderr else "Unknown error"
            
            # Check for specific errors
            if "403" in stderr_str:
                logger.warning(f"403 error on attempt {attempt + 1}")
                if attempt < 2:
                    await asyncio.sleep(3 * (attempt + 1))
                    continue
                return False, None, "403 Forbidden - Token expired or IP blocked"
            
            return False, None, stderr_str
            
        except asyncio.TimeoutError:
            logger.error("Download timeout")
            if attempt == 2:
                return False, None, "Download timeout after 3 attempts"
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            if attempt == 2:
                return False, None, str(e)
            await asyncio.sleep(2)

# ============== MAIN UPLOAD HANDLER ==============
@bot.on_message(filters.command(["upload"]))
async def upload_handler(bot: Client, m: Message):
    """Main upload command handler"""
    start_time = time.time()
    
    # Get input file
    editable = await m.reply_text('📁 **Send me .txt file**')
    try:
        input_msg = await bot.listen(editable.chat.id, timeout=300)
        if not input_msg.document or not input_msg.document.file_name.endswith('.txt'):
            await editable.edit("❌ **Please send a valid .txt file**")
            return
        
        x = await input_msg.download()
        await input_msg.delete()
    except Exception as e:
        await editable.edit(f"❌ **Error:** {str(e)}")
        return

    # Setup download directory
    download_dir = f"./downloads/{m.chat.id}_{int(time.time())}"
    os.makedirs(download_dir, exist_ok=True)
    original_dir = os.getcwd()
    os.chdir(download_dir)

    # Parse links
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
        
        safe_remove(x)
        
        if not links:
            await editable.edit("❌ **No valid links found in file**")
            os.chdir(original_dir)
            shutil.rmtree(download_dir, ignore_errors=True)
            return
            
    except Exception as e:
        await editable.edit(f"❌ **Failed to parse file:** {str(e)}")
        safe_remove(x)
        os.chdir(original_dir)
        shutil.rmtree(download_dir, ignore_errors=True)
        return

    # Get user inputs
    await editable.edit(f"**📊 Total Links:** `{len(links)}`\n\nSend starting number (default: 1)")
    try:
        input0 = await bot.listen(editable.chat.id, timeout=60)
        raw_text = input0.text
        await input0.delete()
    except:
        raw_text = "1"

    await editable.edit("**📝 Send Batch Name:**")
    try:
        input1 = await bot.listen(editable.chat.id, timeout=60)
        raw_text0 = input1.text
        await input1.delete()
    except:
        raw_text0 = "Batch"

    await editable.edit("**🎥 Send Quality (144/240/360/480/720/1080):**")
    try:
        input2 = await bot.listen(editable.chat.id, timeout=60)
        raw_text2 = input2.text
        await input2.delete()
    except:
        raw_text2 = "480"

    await editable.edit("**✏️ Send Caption (or 'Robin' for default):**")
    try:
        input3 = await bot.listen(editable.chat.id, timeout=60)
        raw_text3 = input3.text
        await input3.delete()
    except:
        raw_text3 = ""

    MR = f"️ ⁪⁬⁮⁮⁮" if raw_text3 == 'Robin' else raw_text3

    await editable.edit("**🖼️ Send Thumbnail URL (or 'no'):**")
    try:
        input6 = await bot.listen(editable.chat.id, timeout=120)
        thumb = input6.text
        await input6.delete()
    except:
        thumb = "no"
    
    await editable.delete()

    # Process thumbnail
    if thumb.startswith("http://") or thumb.startswith("https://"):
        try:
            os.system(f"wget -q '{thumb}' -O 'thumb.jpg'")
            thumb = "thumb.jpg" if os.path.exists("thumb.jpg") else "no"
        except:
            thumb = "no"

    # Parse start count
    try:
        count = max(1, int(raw_text))
    except:
        count = 1

    # Statistics
    success_count = 0
    failed_downloads = []
    total_links = len(links)

    # Process links
    for i in range(count - 1, total_links):
        try:
            # Process URL
            url_part = links[i][1]
            url_part = (url_part
                .replace("file/d/", "uc?export=download&id=")
                .replace("www.youtube-nocookie.com/embed", "youtu.be")
                .replace("?modestbranding=1", "")
                .replace("/view?usp=sharing", ""))
            
            url = "https://" + url_part
            
            # Clean name
            raw_name = links[i][0]
            for char in ["\t", ":", "/", "+", "#", "|", "@", "*", "https", "http"]:
                raw_name = raw_name.replace(char, "")
            raw_name = raw_name.strip()
            
            name1 = clean_filename(raw_name)
            display_name = f'{str(count).zfill(3)}) {name1[:60]}'
            file_safe_name = f'{str(count).zfill(3)})_{name1[:50]}'

            # Captions
            cc = f'**[ 🎥 ] Vid_ID:** {str(count).zfill(3)}.** {name1}{MR}.mkv\n✉️ **Batch:** {raw_text0}'
            cc1 = f'**[ 📁 ] Pdf_ID:** {str(count).zfill(3)}. {name1}{MR}.pdf\n✉️ **Batch:** {raw_text0}'

            # Check link type
            is_classplus = any(x in url.lower() for x in ['classplusapp.com', 'media-cdn.classplusapp.com', 'cpvod.test'])
            is_youtube = "youtu" in url.lower()
            is_drive = "drive.google.com" in url.lower() or "drive" in url.lower()
            is_pdf = url.lower().endswith('.pdf') or '.pdf' in url.lower()

            progress_text = f"⏳ **Progress:** {i+1}/{total_links}\n🎬 **Current:** {display_name[:40]}"
            
            # Handle Google Drive
            if is_drive:
                try:
                    prog = await m.reply_text(f"⬇️ **Drive Download:** {display_name}\n{progress_text}")
                    ka = await helper.download(url, file_safe_name)
                    
                    if ka and os.path.exists(ka):
                        await bot.send_document(chat_id=m.chat.id, document=ka, caption=cc1)
                        success_count += 1
                        safe_remove(ka)
                    else:
                        failed_downloads.append((display_name, "Drive download failed"))
                    
                    await prog.delete()
                except Exception as e:
                    failed_downloads.append((display_name, f"Drive: {str(e)}"))
                count += 1
                continue

            # Handle PDF
            if is_pdf:
                try:
                    prog = await m.reply_text(f"📄 **PDF Download:** {display_name}\n{progress_text}")
                    pdf_path = f"{file_safe_name}.pdf"
                    
                    if await download_with_progress(url, pdf_path):
                        await bot.send_document(chat_id=m.chat.id, document=pdf_path, caption=cc1)
                        success_count += 1
                        safe_remove(pdf_path)
                    else:
                        failed_downloads.append((display_name, "PDF download failed"))
                    
                    await prog.delete()
                except Exception as e:
                    failed_downloads.append((display_name, f"PDF: {str(e)}"))
                count += 1
                continue

            # Handle Video (YouTube, ClassPlus, Others)
            try:
                prog = await m.reply_text(
                    f"🎥 **Video Download:** {display_name}\n"
                    f"{'🎓 ClassPlus' if is_classplus else '📺 YouTube' if is_youtube else '🌐 Direct'}\n"
                    f"{progress_text}"
                )

                success, filename, error = await download_video_ytdlp(
                    url, file_safe_name, raw_text2, is_classplus
                )

                if success and filename and os.path.exists(filename):
                    # Send video
                    try:
                        await helper.send_vid(bot, m, cc, filename, thumb, display_name, prog)
                        success_count += 1
                    except FloodWait as e:
                        await asyncio.sleep(e.x)
                        await helper.send_vid(bot, m, cc, filename, thumb, display_name, prog)
                        success_count += 1
                    except Exception as e:
                        failed_downloads.append((display_name, f"Send: {str(e)}"))
                    
                    safe_remove(filename)
                else:
                    failed_downloads.append((display_name, error or "Download failed"))
                    await prog.edit(f"❌ **Failed:** {display_name}\n**Error:** {error}")

                await prog.delete()
                
            except Exception as e:
                failed_downloads.append((display_name, f"Video: {str(e)}"))
                logger.error(f"Video processing error: {e}")

            count += 1
            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Loop error: {e}")
            failed_downloads.append((links[i][0] if i < len(links) else "Unknown", str(e)))
            count += 1
            continue

    # Final report
    elapsed_time = time.time() - start_time
    hours, remainder = divmod(int(elapsed_time), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    report = (
        f"✅ **Batch Complete!**\n\n"
        f"📊 **Statistics:**\n"
        f"✓ Success: `{success_count}`\n"
        f"✗ Failed: `{len(failed_downloads)}`\n"
        f"⏱ Time: `{hours:02d}:{minutes:02d}:{seconds:02d}`\n\n"
    )
    
    if failed_downloads:
        report += "❌ **Failed Items:**\n"
        for idx, (name, error) in enumerate(failed_downloads[:10], 1):
            report += f"{idx}. `{name[:30]}...` - {error[:30]}\n"
        if len(failed_downloads) > 10:
            report += f"...and {len(failed_downloads)-10} more"

    await m.reply_text(report)
    
    # Cleanup
    os.chdir(original_dir)
    shutil.rmtree(download_dir, ignore_errors=True)
    logger.info(f"Cleanup completed: {download_dir}")

# ============== WEBHOOK & MAIN ==============
async def main():
    if WEBHOOK:
        app = await web_server()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()
        logger.info(f"Web server started on port {PORT}")

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║           🤖 TXT TO VIDEO BOT - PRO VERSION              ║
    ║              Fixed & Enhanced by AI                      ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    logger.info("Starting bot...")
    
    loop = asyncio.get_event_loop()
    try:
        loop.create_task(bot.start())
        loop.create_task(main())
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        loop.stop()
        logger.info("Cleanup completed")
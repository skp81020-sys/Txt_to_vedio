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

# Define aiohttp routes
routes = web.RouteTableDef()

# Random User Agents list for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

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
                    [
                    InlineKeyboardButton("✜ ᴀsʜᴜᴛᴏsʜ ɢᴏsᴡᴀᴍɪ 𝟸𝟺 ✜" ,url="https://t.me/AshutoshGoswami24") ],
                    [
                    InlineKeyboardButton("🦋 𝐅𝐨𝐥𝐥𝐨𝐰 𝐌𝐞 🦋" ,url="https://t.me/AshuSupport") ]                               
            ]))

@bot.on_message(filters.command("stop"))
async def restart_handler(_, m):
    await m.reply_text("♦ 𝐒𝐭𝐨𝐩𝐩𝐞𝐭 ♦", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

def clean_filename(name):
    """Clean filename for safe file operations"""
    # Remove or replace invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:100]  # Limit length

async def download_pdf_direct(url, output_path, max_retries=3):
    """
    Direct PDF download with requests (more reliable for PDFs)
    """
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'application/pdf,application/xhtml+xml,application/xml;q=0.9,image/webp,/;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url, 
                headers=headers, 
                timeout=60,
                stream=True,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Check if content is actually PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and 'application' not in content_type:
                # Try anyway, might be misconfigured server
                pass
            
            # Save with progress
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify file was created and has content
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True, None
            else:
                return False, "Downloaded file is empty"
                
        except Exception as e:
            if attempt == max_retries - 1:
                return False, str(e)
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return False, "Max retries exceeded"

async def download_with_ytdlp(url, output_name, m=None):
    """
    Download using yt-dlp with proper error handling
    """
    clean_name = clean_filename(output_name)
    output_template = f"{clean_name}.%(ext)s"
    
    cmd = [
        "yt-dlp",
        "--no-check-certificates",
        "--user-agent", random.choice(USER_AGENTS),
        "--retries", "10",
        "--fragment-retries", "10",
        "--socket-timeout", "30",
        "--no-warnings",
        "-o", output_template,
        url
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), 
            timeout=300  # 5 minute timeout
        )
        
        if process.returncode != 0:
            return False, stderr.decode() if stderr else "Unknown error"
        
        # Find downloaded file
        await asyncio.sleep(1)  # Wait for filesystem
        
        # Check for any file with similar name
        possible_files = (
            glob.glob(f"{clean_name}.*") + 
            glob.glob(f"{clean_name}*")
        )
        
        pdf_files = [f for f in possible_files if f.endswith('.pdf')]
        
        if pdf_files:
            return True, pdf_files[0]
        elif possible_files:
            # Rename to .pdf if different extension
            downloaded = possible_files[0]
            if not downloaded.endswith('.pdf'):
                new_name = f"{clean_name}.pdf"
                os.rename(downloaded, new_name)
                return True, new_name
            return True, downloaded
        
        return False, "File not found after download"
        
    except asyncio.TimeoutError:
        return False, "Download timeout"
    except Exception as e:
        return False, str(e)

@bot.on_message(filters.command(["upload"]))
async def account_login(bot: Client, m: Message):
    editable = await m.reply_text('sᴇɴᴅ ᴍᴇ .ᴛxᴛ ғɪʟᴇ  ⏍')
    input_msg: Message = await bot.listen(editable.chat.id)
    x = await input_msg.download()
    await input_msg.delete(True)

    # Create downloads directory
    download_dir = f"./downloads/{m.chat.id}"
    os.makedirs(download_dir, exist_ok=True)
    os.chdir(download_dir)  # Change to download directory

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
    
   
    await editable.edit(f"ɪɴ ᴛxᴛ ғɪʟᴇ ᴛɪᴛʟᴇ ʟɪɴᴋ 🔗* *{len(links)}**\n\nsᴇɴᴅ ғʀᴏᴍ  ᴡʜᴇʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ɪɴɪᴛᴀʟ ɪs 1")
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
    
    # Resolution mapping
    res_map = {
        "144": "256x144",
        "240": "426x240", 
        "360": "640x360",
        "480": "854x480",
        "720": "1280x720",
        "1080": "1920x1080"
    }
    res = res_map.get(raw_text2, "UN")
    

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
        getstatusoutput(f"wget '{thumb}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb = "no"

    # Parse start count
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

                # Handle special domains
                if "visionias" in url:
                    try:
                        async with ClientSession() as session:
                            headers = {
                                'User-Agent': random.choice(USER_AGENTS),
                                'Referer': 'http://www.visionias.in/',
                            }
                            async with session.get(url, headers=headers) as resp:
                                text = await resp.text()
                                url = re.search(r"(https://.?playlist.m3u8.?)\"", text).group(1)
                    except Exception as e:
                        await m.reply_text(f"⚠️ VisionIAS Error: {str(e)}")
                        continue

                elif 'videos.classplusapp' in url or 'classplus.co' in url:
                    try:
                        response = requests.get(
                            f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}',
                            headers={
                                'x-access-token': 'eyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MzgzNjkyMTIsIm9yZ0lkIjoyNjA1LCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTcwODI3NzQyODkiLCJuYW1lIjoiQWNlIiwiZW1haWwiOm51bGwsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjpudWxsLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpYXQiOjE2NDMyODE4NzcsImV4cCI6MTY0Mzg4NjY3N30.hM33P2ai6ivdzxPPfm01LAd4JWv-vnrSxGXqvCirCSpUfhhofpeqyeHPxtstXwe0',
                                'User-Agent': random.choice(USER_AGENTS)
                            }
                        )
                        url = response.json()['url']
                    except Exception as e:
                        await m.reply_text(f"⚠️ ClassPlus Error: {str(e)}")
                        continue

                elif '/master.mpd' in url:
                    try:
                        vid_id = url.split("/")[-2]
                        url = f"https://d26g5bnklkwsh4.cloudfront.net/{vid_id}/master.m3u8"
                    except:
                        pass

                # Clean name
                raw_name = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace("https", "").replace("http", "").strip()
                name1 = clean_filename(raw_name)
                display_name = f'{str(count).zfill(3)}) {name1[:60]}'
                file_safe_name = f'{str(count).zfill(3)})_{name1[:50]}'

                # Captions
                cc = f'*[ 🎥 ] Vid_ID:* {str(count).zfill(3)}.* {name1}{MR}.mkv\n✉️ 𝐁𝐚𝐭𝐜𝐡 » *{raw_text0}**'
                cc1 = f'*[ 📁 ] Pdf_ID:* {str(count).zfill(3)}. {name1}{MR}.pdf \n✉️ 𝐁𝐚𝐭𝐜𝐡 » *{raw_text0}*'

                # Handle Google Drive
                if "drive" in url:
                    try:
                        ka = await helper.download(url, file_safe_name)
                        if os.path.exists(ka):
                            await bot.send_document(chat_id=m.chat.id, document=ka, caption=cc1)
                            success_count += 1
                            os.remove(ka)
                        else:
                            failed_downloads.append((display_name, "Drive download failed"))
                    except Exception as e:
                        failed_downloads.append((display_name, f"Drive: {str(e)}"))
                    count += 1
                    continue
                
                # Handle PDF
                elif ".pdf" in url.lower() or url.lower().endswith('.pdf'):
                    prog = await m.reply_text(f"📄 Downloading PDF: {display_name}")
                    
                    pdf_path = f"{file_safe_name}.pdf"
                    success = False
                    error_msg = ""
                    
                    # Method 1: Direct download
                    try:
                        success, error_msg = await download_pdf_direct(url, pdf_path)
                    except Exception as e:
                        error_msg = f"Direct: {str(e)}"
                    
                    # Method 2: yt-dlp fallback
                    if not success or not os.path.exists(pdf_path):
                        try:
                            if os.path.exists(pdf_path):
                                os.remove(pdf_path)
                            success, result = await download_with_ytdlp(url, file_safe_name, m)
                            if success and os.path.exists(result):
                                pdf_path = result
                                success = True
                        except Exception as e:
                            error_msg += f" | ytdlp: {str(e)}"
                    
                    # Send if successful
                    if success and os.path.exists(pdf_path):
                        try:
                            file_size = os.path.getsize(pdf_path)
                            if file_size == 0:
                                raise Exception("Downloaded file is empty")
                            
                            await prog.edit(f"📤 Uploading: {display_name} ({file_size//1024}KB)")
                            
                            await bot.send_document(
                                chat_id=m.chat.id, 
                                document=pdf_path, 
                                caption=cc1
                            )
                            success_count += 1
                            
                            # Cleanup
                            try:
                                os.remove(pdf_path)
                            except:
                                pass
                                
                        except FloodWait as e:
                            await m.reply_text(f"⏳ FloodWait: {e.x} seconds")
                            await asyncio.sleep(e.x)
                            # Retry send
                            await bot.send_document(
                                chat_id=m.chat.id, 
                                document=pdf_path, 
                                caption=cc1
                            )
                        except Exception as e:
                            failed_downloads.append((display_name, f"Send: {str(e)}"))
                    else:
                        failed_downloads.append((display_name, error_msg or "Unknown error"))
                        await prog.edit(f"❌ Failed: {display_name}\nError: {error_msg}")
                    
                    try:
                        await prog.delete()
                    except:
                        pass
                    
                    count += 1
                    await asyncio.sleep(1)
                    continue
                
                # Handle Video
                else:
                    if "youtu" in url:
                        ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
                    else:
                        ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"

                    Show = f"❊⟱ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 ⟱❊ »\n\n📝 𝐍𝐚𝐦𝐞 » {display_name}\n⌨ 𝐐𝐮𝐥𝐢𝐭𝐲 » {raw_text2}\n\n*🔗 𝐔𝐑𝐋 »* {url}"
                    prog = await m.reply_text(Show)
                    
                    try:
                        res_file = await helper.download_video(url, f"yt-dlp -f '{ytf}' '{url}' -o '{file_safe_name}.%(ext)s'", file_safe_name)
                        
                        if res_file and os.path.exists(res_file):
                            await prog.delete()
                            await helper.send_vid(bot, m, cc, res_file, thumb, display_name, prog)
                            success_count += 1
                            
                            # Cleanup
                            try:
                                os.remove(res_file)
                            except:
                                pass
                        else:
                            failed_downloads.append((display_name, "Video download failed"))
                            
                    except Exception as e:
                        failed_downloads.append((display_name, f"Video: {str(e)}"))
                        await prog.edit(f"❌ Video Error: {str(e)}")
                    
                    count += 1
                    await asyncio.sleep(1)

            except Exception as e:
                failed_downloads.append((links[i][0] if i < len(links) else "Unknown", str(e)))
                await m.reply_text(f"⚠️ Loop Error: {str(e)}")
                count += 1
                continue

    except Exception as e:
        await m.reply_text(f"Main Error: {str(e)}")
    
    # Final report
    report = f"✅ 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐃𝐨𝐧𝐞\n\n📊 𝐒𝐭𝐚𝐭𝐬:\n✓ Success: {success_count}\n✗ Failed: {len(failed_downloads)}"
    
    if failed_downloads:
        report += "\n\n❌ 𝐅𝐚𝐢𝐥𝐞𝐝 𝐈𝐭𝐞𝐦𝐬:\n"
        for name, error in failed_downloads[:10]:  # Show first 10
            report += f"• {name[:30]}...: {error[:50]}\n"
        if len(failed_downloads) > 10:
            report += f"...and {len(failed_downloads)-10} more"
    
    await m.reply_text(report)
    
    # Cleanup directory
    try:
        os.chdir("..")
        import shutil
        shutil.rmtree(download_dir, ignore_errors=True)
    except:
        pass

async def main():
    if WEBHOOK:
        app = await web_server()
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()
        print(f"Web server started on port {PORT}")

if __name__== "__main__":
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
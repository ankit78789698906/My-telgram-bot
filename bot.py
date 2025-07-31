import os
import aiohttp
import aiofiles
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message

# 👉 अपनी जानकारी यहाँ डालें
API_ID = 25281153
API_HASH = "9fbfd30f6baf70e38e22aecbf50ee17c"
BOT_TOKEN = "8058445658:AAG2ZZHWmIJPvHDNBByWjIAvWR4zr6Wjlg8"

bot = Client("HindiDownloaderBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def sanitize_filename(name):
    import re
    return re.sub(r'[<>:"/\\|?*]', '', name).strip()

async def download_video(url, name, resolution):
    filename = f"{sanitize_filename(name)}.mp4"
    cmd = f"yt-dlp -f 'b[height<={resolution}]' -o '{filename}' '{url}'"
    subprocess.run(cmd, shell=True)
    return filename if os.path.exists(filename) else None

async def download_file(url, name):
    filename = f"{sanitize_filename(name)}.pdf"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(filename, mode='wb')
                await f.write(await resp.read())
                await f.close()
    return filename if os.path.exists(filename) else None

@bot.on_message(filters.command("start"))
async def start_handler(bot, message):
    await message.reply_text("नमस्ते! कृपया .txt फाइल भेजें जिसमें नाम और लिंक हो।")

@bot.on_message(filters.document)
async def handle_txt_file(bot, message: Message):
    if not message.document.file_name.endswith(".txt"):
        await message.reply_text("कृपया सिर्फ .txt फाइल भेजें।")
        return

    file_path = await message.download()
    await message.reply_text("🔄 फाइल पढ़ी जा रही है...")

    await message.reply_text("🎞 कृपया वीडियो क्वालिटी चुनें (उदाहरण: 144, 240, 360, 480, 720, 1080)")
    quality_msg = await bot.listen(message.chat.id)
    resolution = quality_msg.text.strip()

    await message.reply_text("🖋 अब एक कैप्शन भेजें जो हर फाइल के साथ जाएगा")
    caption_msg = await bot.listen(message.chat.id)
    caption = caption_msg.text.strip()

    await message.reply_text("🌄 थंबनेल लिंक भेजें या 'no' लिखें")
    thumb_msg = await bot.listen(message.chat.id)
    thumb_link = thumb_msg.text.strip()
    thumb_file = None

    if thumb_link.lower() != "no" and thumb_link.startswith("http"):
        thumb_file = "thumb.jpg"
        subprocess.run(f"wget '{thumb_link}' -O '{thumb_file}'", shell=True)

    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
        async for line in f:
            if line.strip():
                parts = line.strip().rsplit(" ", 1)
                if len(parts) == 2 and parts[1].startswith("http"):
                    name, url = parts
                    try:
                        if ".pdf" in url or ".doc" in url:
                            saved_file = await download_file(url, name)
                        else:
                            saved_file = await download_video(url, name, resolution)

                        if saved_file:
                            await bot.send_document(
                                chat_id=message.chat.id,
                                document=saved_file,
                                caption=f"{name}\n{caption}",
                                thumb=thumb_file if thumb_file else None
                            )
                            os.remove(saved_file)
                        else:
                            await message.reply_text(f"❌ {name} डाउनलोड नहीं हुआ")
                    except Exception as e:
                        await message.reply_text(f"⚠️ {name}: {e}")

    if thumb_file and os.path.exists(thumb_file):
        os.remove(thumb_file)

    await message.reply_text("✅ सभी फाइलों का प्रोसेस पूरा हुआ।")

bot.run()

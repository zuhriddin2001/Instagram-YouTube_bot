import os
import telebot
import yt_dlp
import time
import socket
import requests
from telebot import types
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

TOKEN = '7679328919:AAEdvxHjCC5VqzYo0p6zR55y-cBMXRnT7V8'
bot = telebot.TeleBot(TOKEN)

# Vaqt chegaralari sozlamalari
socket.setdefaulttimeout(30)  # Soket vaqt chegarasi 30 soniyaga o'rnatildi

# HTTP so'rovlar uchun sessiya yaratish va qayta urinishlar
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

# Yuklanmalar uchun papka
DOWNLOAD_DIR = "../downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Bot logosi
BOT_LOGO = "https://example.com/logo.jpg"  # Botingiz uchun logo URL manzili


def is_valid_url(url):
    # Agar xabar bir necha qatorlardan iborat bo'lsa, faqat URLni topib olamiz
    if "\n" in url:
        lines = url.split("\n")
        for line in lines:
            if "youtube.com" in line or "youtu.be" in line or "instagram.com" in line or "tiktok.com" in line:
                return line.strip()  # URLni qaytaramiz

    # Oddiy URL tekshiruvi
    if "youtube.com" in url or "youtu.be" in url or "instagram.com" in url or "tiktok.com" in url:
        return url.strip()

    return False


@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Xush kelibsiz xabari
    welcome_text = (
        f"Assalomu alaykum, {message.from_user.first_name}! 👋\n\n"
        "Video yuklovchi botga xush kelibsiz! 🎬\n"
        "Men YouTube, Instagram va TikTok videolarini yuklab olishga yordam beraman.\n\n"
        "Quyidagi tugmalardan birini tanlang yoki to'g'ridan-to'g'ri video havolasini yuboring:"
    )

    # Inline tugmalar yaratish
    markup = types.InlineKeyboardMarkup(row_width=2)
    youtube_btn = types.InlineKeyboardButton("YouTube 🎥", callback_data="youtube")
    instagram_btn = types.InlineKeyboardButton("Instagram 📸", callback_data="instagram")
    tiktok_btn = types.InlineKeyboardButton("TikTok 🎵", callback_data="tiktok")
    help_btn = types.InlineKeyboardButton("Yordam ℹ️", callback_data="help")

    markup.add(youtube_btn, instagram_btn)
    markup.add(tiktok_btn)
    markup.add(help_btn)

    # Logo bilan birga xabarni yuborish
    try:
        bot.send_photo(
            message.chat.id,
            photo=BOT_LOGO,
            caption=welcome_text,
            reply_markup=markup
        )
    except Exception:
        # Agar logo yuborilmasa, oddiy xabar yuborish
        bot.send_message(
            message.chat.id,
            welcome_text,
            reply_markup=markup
        )


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "youtube":
        bot.send_message(call.message.chat.id, "YouTube video havolasini yuboring:")
    elif call.data == "instagram":
        bot.send_message(call.message.chat.id, "Instagram video havolasini yuboring:")
    elif call.data == "tiktok":
        bot.send_message(call.message.chat.id, "TikTok video havolasini yuboring:")
    elif call.data == "help":
        help_text = (
            "🔍 Qo'llanma:\n\n"
            "1. Video yuklab olish uchun video havolasini yuboring\n"
            "2. Yuklab olish boshlanganidan so'ng kuting\n"
            "3. Video yuklangandan so'ng, uni olasiz\n\n"
            "🔄 /start - botni qayta ishga tushirish\n"
            "ℹ️ /help - yordam olish"
        )
        bot.send_message(call.message.chat.id, help_text)

    # Tugma bosilgandan so'ng animatsiyani to'xtatish
    bot.answer_callback_query(call.id)


@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "🔍 Qo'llanma:\n\n"
        "1. Video yuklab olish uchun video havolasini yuboring\n"
        "2. Yuklab olish boshlanganidan so'ng kuting\n"
        "3. Video yuklangandan so'ng, uni olasiz\n\n"
        "⚠️ Eslatma: Juda katta hajmdagi videolarni yuklab olish uzoq vaqt talab qilishi mumkin."
    )
    bot.send_message(message.chat.id, help_text)


@bot.message_handler(func=lambda message: is_valid_url(message.text) is not False)
def download_video(message):
    # Agar xabar ko'p qatorli bo'lsa, faqat URL qismini olish
    url = is_valid_url(message.text)
    chat_id = message.chat.id

    # Yuklab olish jarayoni haqida xabar yuborish
    status_message = bot.send_message(chat_id, "⏳ Video aniqlanmoqda...")

    try:
        # Qaysi platformadan ekanligini aniqlash
        platform = "Noma'lum"
        if "youtube.com" in url or "youtu.be" in url:
            platform = "YouTube"
        elif "instagram.com" in url:
            platform = "Instagram"
        elif "tiktok.com" in url:
            platform = "TikTok"

        # Status xabarni yangilash
        bot.edit_message_text(
            f"⬇️ {platform} dan video yuklab olinmoqda...",
            chat_id=chat_id,
            message_id=status_message.message_id
        )

        # Yuklab olish parametrlari
        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_DIR}/%(title).100s.%(ext)s',
            'format': 'best',
            'quiet': True,
            'noplaylist': True,
            'cookiefile': 'cookies.txt',
            'default_search': 'ytsearch',  # YouTube qidirish funksiyasini yoqish
            'ignoreerrors': True,  # Ba'zi xatoliklarni e'tiborsiz qoldirish
            'socket_timeout': 30,  # Soket vaqt chegarasi
            'retries': 10,  # Qayta urinishlar soni
            'fragment_retries': 10,  # Fragment qayta urinishlari
            'skip_download_archive': True,  # Arxivni o'tkazib yuborish
            'external_downloader_args': ['-timeout', '30'],  # Tashqi yuklovchi uchun parametrlar
        }

        # Video ma'lumotlarini olish va xatolarni qayta ishlash
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Debug uchun URL haqida ma'lumot
                print(f"Yuklanmoqda: {url}")

                # Video ma'lumotlarini olish
                info = ydl.extract_info(url, download=False)

                if not info:
                    raise Exception("Video ma'lumotlarini olishda xatolik")

                # Xabarni yangilash
                bot.edit_message_text(
                    f"⬇️ {platform} dan \"{info.get('title', 'Video')}\" yuklanmoqda...",
                    chat_id=chat_id,
                    message_id=status_message.message_id
                )

                # Videoni yuklab olish - qayta urinish mexanizmi bilan
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        ydl.download([url])
                        file_path = ydl.prepare_filename(info)
                        if os.path.exists(file_path):
                            break  # Muvaffaqiyatli yuklab olindi
                    except Exception as download_error:
                        print(f"Urinish {attempt + 1}/{max_attempts} xatolik: {download_error}")
                        if attempt == max_attempts - 1:  # Oxirgi urinish
                            raise  # Xatolikni qayta ko'tarish
                        bot.edit_message_text(
                            f"⚠️ Yuklab olishda xatolik. Qayta urinilmoqda ({attempt + 2}/{max_attempts})...",
                            chat_id=chat_id,
                            message_id=status_message.message_id
                        )
                        time.sleep(2)  # Qayta urinishdan oldin kutish

        except Exception as e:
            print(f"Yuklab olishda xatolik: {str(e)}")

            # Xabar berish - muammoni tushunarli qilib tushuntirish
            error_message = str(e)
            if "Connection aborted" in error_message or "timed out" in error_message:
                error_text = "⚠️ Internet aloqasi sekin yoki beqaror. Iltimos, keyinroq qayta urinib ko'ring."
            elif "not a valid URL" in error_message:
                error_text = "❌ Yaroqsiz havola. Iltimos, to'g'ri YouTube, Instagram yoki TikTok havolasini yuboring."
            elif "This video is not available" in error_message:
                error_text = "⚠️ Bu video hozirda mavjud emas yoki cheklangan."
            else:
                error_text = f"❌ Videoni yuklab olishda xatolik yuz berdi. Iltimos, boshqa havola bilan urinib ko'ring."

            bot.edit_message_text(
                error_text,
                chat_id=chat_id,
                message_id=status_message.message_id
            )

            # Xatolikdan so'ng chiqib ketish
            return

        # Fayl mavjudligini tekshirish - agar mavjud bo'lmasa boshqa usulda urinib ko'rish
        if not os.path.exists(file_path):
            try:
                # Alternative parameter bilan qayta urinish
                alternative_opts = ydl_opts.copy()
                alternative_opts['format'] = 'best[height<=720]'  # Sifatni kamaytirish

                bot.edit_message_text(
                    "🔄 Asosiy usul bilan yuklab olib bo'lmadi. Alternativ usul bilan urinib ko'rilmoqda...",
                    chat_id=chat_id,
                    message_id=status_message.message_id
                )

                with yt_dlp.YoutubeDL(alternative_opts) as alt_ydl:
                    alt_info = alt_ydl.extract_info(url, download=True)
                    file_path = alt_ydl.prepare_filename(alt_info)
                    info = alt_info  # Ma'lumotni yangilash
            except Exception as alt_error:
                print(f"Alternativ usul bilan yuklab olishda xatolik: {alt_error}")
                bot.edit_message_text(
                    "❌ Videoni yuklab olishning iloji bo'lmadi. Boshqa havola bilan urinib ko'ring.",
                    chat_id=chat_id,
                    message_id=status_message.message_id
                )
                return

        # Faylni tekshirish
        if not os.path.exists(file_path):
            raise Exception("Fayl topilmadi")

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        # Xabarni yangilash
        bot.edit_message_text(
            f"✅ Video yuklandi! Telegramga yuborilmoqda... ({file_size_mb:.1f} MB)",
            chat_id=chat_id,
            message_id=status_message.message_id
        )

        # Video faylni Telegramga yuborish
        with open(file_path, 'rb') as video_file:
            # Fayl hajmi 50MB dan katta bo'lsa
            if file_size_mb > 50:
                bot.edit_message_text(
                    f"⚠️ Video hajmi juda katta ({file_size_mb:.1f} MB). "
                    f"Telegram 50MB dan katta fayllarni yuborishga ruxsat bermaydi.",
                    chat_id=chat_id,
                    message_id=status_message.message_id
                )
            else:
                # Video sarlavhasi
                caption = f"📹 {info.get('title', 'Video')}\n\n👉 @your_bot_username orqali yuklandi"

                # Videoni yuborish
                bot.send_video(
                    chat_id,
                    video_file,
                    caption=caption,
                    supports_streaming=True
                )

                # Xabarni o'chirish
                bot.delete_message(chat_id, status_message.message_id)

        # Yuklab olingan faylni o'chirish
        os.remove(file_path)

    except Exception as e:
        error_message = f"❌ Xatolik yuz berdi: {str(e)}"
        print(error_message)
        bot.edit_message_text(
            "❌ Videoni yuklab olishda xatolik yuz berdi. Iltimos, boshqa havola bilan urinib ko'ring.",
            chat_id=chat_id,
            message_id=status_message.message_id
        )


@bot.message_handler(func=lambda message: True)
def unknown(message):
    # Qo'shimcha inline tugmalar bilan javob qaytarish
    markup = types.InlineKeyboardMarkup(row_width=2)
    youtube_btn = types.InlineKeyboardButton("YouTube 🎥", callback_data="youtube")
    instagram_btn = types.InlineKeyboardButton("Instagram 📸", callback_data="instagram")
    tiktok_btn = types.InlineKeyboardButton("TikTok 🎵", callback_data="tiktok")

    markup.add(youtube_btn, instagram_btn)
    markup.add(tiktok_btn)

    bot.reply_to(
        message,
        "🔗 Iltimos, to'g'ri video havolasini yuboring yoki quyidagi tugmalarni bosing:",
        reply_markup=markup
    )


if __name__ == "__main__":
    print("🚀 Bot ishga tushdi...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"⚠️ Bot to'xtadi: {e}")
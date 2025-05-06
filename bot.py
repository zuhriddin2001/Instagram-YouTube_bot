import logging
import os
import json
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Sozlamalar
# TELEGRAM_BOT_TOKEN ni muhit o'zgaruvchisi sifatida o'rnating (masalan, `set TELEGRAM_BOT_TOKEN=your_token` cmd da)
TOKEN = os.getenv("7640573887:AAFsw3yS2z7Ugp0Im3F-mpnRAENbuCn4kxY")
# YOUR_ADMIN_CHAT_ID ni o'z Telegram ID bilan almashtiring (@userinfobot orqali oling)
ADMIN_CHAT_ID = os.getenv("7518756285")
FEEDBACK_FILE = "feedback.json"

# Tokenni tekshirish
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN muhit o'zgaruvchisi o'rnatilmagan. Iltimos, botni ishga tushirishdan oldin uni o'rnating.")

# Logging sozlamalari
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Suhbat holatlari
REGION, RESTAURANT, MENU, FEEDBACK, SEARCH, LANGUAGE = range(6)

# Qo'llab-quvvatlanadigan tillar
LANGUAGES = {
    "uz": {"name": "🇺🇿 O'zbek", "code": "uz"},
    "ru": {"name": "🇷🇺 Русский", "code": "ru"},
    "en": {"name": "🇬🇧 English", "code": "en"},
}

# Qashqadaryo tumanlari
qashqadaryo_regions = {
    "qarshi": "Qarshi shahri",
    "shahrisabz": "Shahrisabz",
    "guzor": "G'uzor",
    "kitob": "Kitob",
    "koson": "Koson",
    "kasbi": "Kasbi",
    "mirishkor": "Mirishkor",
    "muborak": "Muborak",
    "nishon": "Nishon",
    "chiroqchi": "Chiroqchi",
    "shakhrisabz_tumani": "Shahrisabz tumani",
    "yakkabog": "Yakkabog'",
    "qamashi": "Qamashi",
    "qarshi_tumani": "Qarshi tumani",
    "dehqonobod": "Dehqonobod",
}

# Oshxona ma'lumotlari
oshxona_data = {
    "qarshi": {
        "Lazzat": {
            "location": "Qarshi shahar, Mustaqillik ko'chasi, 45-uy",
            "latitude": 38.8606,
            "longitude": 65.7975,
            "menu": {
                "Osh": "30000 so'm",
                "Lagmon": "25000 so'm",
                "Shashlik": "12000 so'm dona",
                "Somsa": "10000 so'm dona",
                "Sho'rva": "22000 so'm",
            },
            "rating": "⭐⭐⭐⭐",
            "phone": "+998 91 456 78 90",
        },
        "Bek": {
            "location": "Qarshi shahar, Navoiy ko'chasi, 123-uy",
            "latitude": 38.8650,
            "longitude": 65.7900,
            "menu": {
                "Osh": "32000 so'm",
                "Mastava": "24000 so'm",
                "Manti": "8000 so'm dona",
                "Chuchvara": "20000 so'm",
                "Sho'rva": "23000 so'm",
            },
            "rating": "⭐⭐⭐⭐⭐",
            "phone": "+998 90 123 45 67",
        },
        "Oqshom": {
            "location": "Qarshi shahar, Nasaf ko'chasi, 78-uy",
            "latitude": 38.8700,
            "longitude": 65.7850,
            "menu": {
                "Osh": "28000 so'm",
                "Norin": "35000 so'm",
                "Shashlik": "11000 so'm dona",
                "Dimlama": "35000 so'm",
                "Mastava": "22000 so'm",
            },
            "rating": "⭐⭐⭐⭐",
            "phone": "+998 93 789 12 34",
        },
    },
    "shahrisabz": {
        "Amir Temur": {
            "location": "Shahrisabz shahar, Ipak yo'li ko'chasi, 56-uy",
            "latitude": 39.0578,
            "longitude": 66.8346,
            "menu": {
                "Osh": "28000 so'm",
                "Shashlik": "10000 so'm",
                "Norin": "30000 so'm",
                "Somsa": "9000 so'm",
                "Sho'rva": "20000 so'm",
            },
            "rating": "⭐⭐⭐⭐",
            "phone": "+998 94 567 89 01",
        },
        "Shirinsoy": {
            "location": "Shahrisabz shahar, Amir Temur ko'chasi, 111-uy",
            "latitude": 39.0600,
            "longitude": 66.8300,
            "menu": {
                "Osh": "30000 so'm",
                "Shashlik": "10000 so'm dona",
                "Somsa": "9000 so'm dona",
                "Chuchvara": "25000 so'm",
                "Qozon kabob": "40000 so'm",
            },
            "rating": "⭐⭐⭐⭐⭐",
            "phone": "+998 97 234 56 78",
        },
    },
    "guzor": {
        "Choyhona": {
            "location": "G'uzor tumani, Mustaqillik ko'chasi, 12-uy",
            "latitude": 38.6208,
            "longitude": 66.2450,
            "menu": {
                "Osh": "25000 so'm",
                "Shashlik": "9000 so'm dona",
                "Somsa": "8000 so'm dona",
                "Lag'mon": "24000 so'm",
                "Sho'rva": "20000 so'm",
            },
            "rating": "⭐⭐⭐⭐",
            "phone": "+998 99 876 54 32",
        },
    },
    "kitob": {
        "Bog'ishamol": {
            "location": "Kitob tumani, Alisher Navoiy ko'chasi, 45-uy",
            "latitude": 39.1200,
            "longitude": 66.8800,
            "menu": {
                "Osh": "27000 so'm",
                "Shashlik": "9000 so'm dona",
                "Somsa": "8000 so'm dona",
                "Chuchvara": "23000 so'm",
                "Qozon kabob": "38000 so'm",
            },
            "rating": "⭐⭐⭐⭐",
            "phone": "+998 93 222 33 44",
        },
    },
    "koson": {
        "Xorazm": {
            "location": "Koson tumani, Buyuk ipak yo'li ko'chasi, 77-uy",
            "latitude": 39.0400,
            "longitude": 65.5800,
            "menu": {
                "Osh": "28000 so'm",
                "Lagmon": "25000 so'm",
                "Shashlik": "10000 so'm dona",
                "Mastava": "22000 so'm",
                "Manti": "7000 so'm dona",
            },
            "rating": "⭐⭐⭐⭐",
            "phone": "+998 91 444 55 66",
        },
    },
    "kasbi": {
        "Shahzoda": {
            "location": "Kasbi tumani markazi, Navoiy ko'chasi, 34-uy",
            "latitude": 38.9600,
            "longitude": 65.4700,
            "menu": {
                "Osh": "26000 so'm",
                "Shashlik": "9000 so'm dona",
                "Lag'mon": "23000 so'm",
                "Sho'rva": "19000 so'm",
                "Manti": "7000 so'm dona",
            },
            "rating": "⭐⭐⭐⭐",
            "phone": "+998 94 111 22 33",
        },
    },
    "mirishkor": {
        "Chinor": {
            "location": "Mirishkor tumani, Yangi hayot ko'chasi, 23-uy",
            "latitude": 38.8500,
            "longitude": 65.1500,
            "menu": {
                "Osh": "25000 so'm",
                "Shashlik": "8000 so'm dona",
                "Somsa": "7000 so'm dona",
                "Chuchvara": "22000 so'm",
                "Mastava": "20000 so'm",
            },
            "rating": "⭐⭐⭐⭐",
            "phone": "+998 99 333 44 55",
        },
    },
    "muborak": {
        "Shalola": {
            "location": "Muborak tumani, Mustaqillik ko'chasi, 56-uy",
            "latitude": 39.2000,
            "longitude": 65.1500,
            "menu": {
                "Osh": "26000 so'm",
                "Shashlik": "9000 so'm dona",
                "Somsa": "8000 so'm dona",
                "Lag'mon": "24000 so'm",
                "Manti": "7000 so'm dona",
            },
            "rating": "⭐⭐⭐⭐",
            "phone": "+998 91 555 66 77",
        },
    },
    "nishon": {
        "Bahor": {
            "location": "Nishon tumani, Yangi hayot ko'chasi, 45-uy",
            "latitude": 38.6900,
            "longitude": 65.3700,
            "menu": {
                "Osh": "25000 so'm",
                "Shashlik": "8000 so'm dona",
                "Somsa": "7000 so'm dona",
                "Chuchvara": "22000 so'm",
                "Mastava": "20000 so'm",
            },
            "rating": "⭐⭐⭐⭐",
            "phone": "+998 93 666 77 88",
        },
    },
    "chiroqchi": {
        "Oqshom": {
            "location": "Chiroqchi tumani, Amir Temur ko'chasi, 89-uy",
            "latitude": 39.0000,
            "longitude": 66.5700,
            "menu": {
                "Osh": "26000 so'm",
                "Shashlik": "9000 so'm dona",
                "Somsa": "8000 so'm dona",
                "Lag'mon": "23000 so'm",
                "Manti": "7000 so'm dona",
            },
            "rating": "⭐⭐⭐⭐",
            "phone": "+998 94 777 88 99",
        },
    },
    "shakhrisabz_tumani": {
        "Nafis": {
            "location": "Shahrisabz tumani, Mustaqillik ko'chasi, 67-uy",
            "latitude": 39.0500,
            "longitude": 66.8200,
            "menu": {
                "Osh": "27000 so'm",
                "Shashlik": "9000 so'm dona",
                "Somsa": "8000 so'm dona",
                "Chuchvara": "23000 so'm",
                "Qozon kabob": "38000 so'm",
            },
            "rating": "⭐⭐⭐⭐",
            "phone": "+998 91 888 99 00",
        },
    },
    "yakkabog": {
        "Marjon": {
            "location": "Yakkabog' tumani, Navoiy ko'chasi, 34-uy",
            "latitude": 38.9700,
            "longitude": 66.6800,
            "menu": {
                "Osh": "26000 so'm",
                "Shashlik": "9000 so'm dona",
                "Somsa": "8000 so'm dona",
                "Lag'mon": "24000 so'm",
                "Manti": "7000 so'm dona",
            },
            "rating": "⭐⭐⭐⭐",
            "phone": "+998 93 999 00 11",
        },
    },
    "qamashi": {
        "Lazzat": {
            "location": "Qamashi tumani, Mustaqillik ko'chasi, 23-uy",
            "latitude": 38.8200,
            "longitude": 66.4600,
            "menu": {
                "Osh": "27000 so'm",
                "Shashlik": "9000 so'm dona",
                "Somsa": "8000 so'm dona",
                "Chuchvara": "23000 so'm",
                "Qozon kabob": "37000 so'm",
            },
            "rating": "⭐⭐⭐⭐",
            "phone": "+998 99 000 11 22",
        },
    },
    "qarshi_tumani": {
        "Saroy": {
            "location": "Qarshi tumani, Yangi hayot ko'chasi, 56-uy",
            "latitude": 38.8600,
            "longitude": 65.7800,
            "menu": {
                "Osh": "28000 so'm",
                "Shashlik": "10000 so'm dona",
                "Somsa": "9000 so'm dona",
                "Lag'mon": "25000 so'm",
                "Manti": "8000 so'm dona",
            },
            "rating": "⭐⭐⭐⭐",
            "phone": "+998 91 111 22 33",
        },
    },
    "dehqonobod": {
        "Chashma": {
            "location": "Dehqonobod tumani, Amir Temur ko'chasi, 78-uy",
            "latitude": 38.3500,
            "longitude": 66.3200,
            "menu": {
                "Osh": "26000 so'm",
                "Shashlik": "9000 so'm dona",
                "Somsa": "8000 so'm dona",
                "Lag'mon": "23000 so'm",
                "Manti": "7000 so'm dona",
            },
            "rating": "⭐⭐⭐⭐",
            "phone": "+998 93 222 33 44",
        },
    },
}

# Lokallashtirish lug'ati
MESSAGES = {
    "uz": {
        "welcome": "Assalomu alaykum, {name}! 🍽️\nQashqadaryo viloyati oshxonalari botiga xush kelibsiz!\n",
        "select_region": "Tuman tanlang:",
        "select_restaurant": "📍 {region} hududidagi oshxonalar:",
        "no_data_region": "Kechirasiz, {region} bo'yicha ma'lumot hozircha mavjud emas.",
        "invalid_selection": "Noto'g'ri tanlov. Iltimos, qaytadan tanlang.",
        "restaurant_info": "*{name}* oshxonasi:\n\n📍 *Manzil:* {location}\n📞 *Telefon:* {phone}\n⭐ *Reyting:* {rating}\n\n🍽️ *MENYU:*\n{menu}",
        "full_menu": "*{name}* oshxonasi menyusi:\n\n{menu}\n\n💬 Narxlar o'zgarishi mumkin.",
        "live_location": "*{name}* oshxonasi live lokatsiyasi:\n\n📍 {location}",
        "google_maps": "*{name}* oshxonasi manzili:\n\n📍 {location}\n\n[Google Maps’da ochish]({url})",
        "error": "Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
        "help": "🍽️ *Qashqadaryo Oshxonalari Bot*\n\nQo'llanma:\n1. /start - Botni ishga tushirish\n2. /help - Yordam\n3. /about - Bot haqida\n4. /language - Tilni o'zgartirish\nAvval tuman, so'ngra oshxonani tanlang.",
        "about": "🍽️ *Qashqadaryo Oshxonalari Bot*\n\nQashqadaryo viloyatidagi oshxonalar haqida ma'lumot.\nImkoniyatlar:\n• Oshxonalar topish\n• Manzil va telefon\n• Menyu va narxlar\n\nXatolik bo'lsa, admin bilan bog'laning.",
        "unknown_command": "Noma'lum buyruq. /help orqali qo'llanmani ko'ring.",
        "feedback_prompt": "Iltimos, fikr-mulohazangizni yuboring (masalan, oshxona haqida sharh):",
        "feedback_thanks": "Fikr-mulohazangiz uchun rahmat!",
        "search_prompt": "Oshxona yoki taom nomini kiriting:",
        "search_results": "Qidiruv natijalari:\n\n{results}",
        "no_search_results": "Hech narsa topilmadi. Iltimos, qaytadan urinib ko'ring.",
        "select_language": "Tilni tanlang:",
        "language_updated": "Til o'zgartirildi: {lang}",
        "main_menu": "Asosiy menyu:",
    },
    "ru": {
        "welcome": "Здравствуйте, {name}! 🍽️\nДобро пожаловать в бот ресторанов Кашкадарьинской области!\n",
        "select_region": "Выберите район:",
        "select_restaurant": "📍 Рестораны в районе {region}:",
        "no_data_region": "Извините, по району {region} пока нет данных.",
        "invalid_selection": "Неверный выбор. Пожалуйста, выберите снова.",
        "restaurant_info": "*{name}* ресторан:\n\n📍 *Адрес:* {location}\n📞 *Телефон:* {phone}\n⭐ *Рейтинг:* {rating}\n\n🍽️ *МЕНЮ:*\n{menu}",
        "full_menu": "*{name}* меню ресторана:\n\n{menu}\n\n💬 Цены могут измениться.",
        "live_location": "*{name}* живая локация ресторана:\n\n📍 {location}",
        "google_maps": "*{name}* адрес ресторана:\n\n📍 {location}\n\n[Открыть в Google Maps]({url})",
        "error": "Произошла ошибка. Пожалуйста, попробуйте снова.",
        "help": "🍽️ *Бот Ресторанов Кашкадарьи*\n\nИнструкция:\n1. /start - Запустить бот\n2. /help - Помощь\n3. /about - О боте\n4. /language - Сменить язык\nВыберите район, затем ресторан.",
        "about": "🍽️ *Бот Ресторанов Кашкадарьи*\n\nИнформация о ресторанах Кашкадарьинской области.\nВозможности:\n• Поиск ресторанов\n• Адреса и телефоны\n• Меню и цены\n\nПри ошибках свяжитесь с админом.",
        "unknown_command": "Неизвестная команда. Используйте /help для инструкций.",
        "feedback_prompt": "Пожалуйста, отправьте ваш отзыв (например, комментарий о ресторане):",
        "feedback_thanks": "Спасибо за ваш отзыв!",
        "search_prompt": "Введите название ресторана или блюда:",
        "search_results": "Результаты поиска:\n\n{results}",
        "no_search_results": "Ничего не найдено. Попробуйте снова.",
        "select_language": "Выберите язык:",
        "language_updated": "Язык изменен: {lang}",
        "main_menu": "Главное меню:",
    },
    "en": {
        "welcome": "Hello, {name}! 🍽️\nWelcome to the Qashqadaryo Restaurants Bot!\n",
        "select_region": "Select a region:",
        "select_restaurant": "📍 Restaurants in {region}:",
        "no_data_region": "Sorry, no data available for {region} yet.",
        "invalid_selection": "Invalid selection. Please try again.",
        "restaurant_info": "*{name}* restaurant:\n\n📍 *Address:* {location}\n📞 *Phone:* {phone}\n⭐ *Rating:* {rating}\n\n🍽️ *MENU:*\n{menu}",
        "full_menu": "*{name}* restaurant menu:\n\n{menu}\n\n💬 Prices may vary.",
        "live_location": "*{name}* restaurant live location:\n\n📍 {location}",
        "google_maps": "*{name}* restaurant address:\n\n📍 {location}\n\n[Open in Google Maps]({url})",
        "error": "An error occurred. Please try again.",
        "help": "🍽️ *Qashqadaryo Restaurants Bot*\n\nGuide:\n1. /start - Start the bot\n2. /help - Help\n3. /about - About the bot\n4. /language - Change language\nSelect a region, then a restaurant.",
        "about": "🍽️ *Qashqadaryo Restaurants Bot*\n\nInfo about restaurants in Qashqadaryo.\nFeatures:\n• Find restaurants\n• Addresses and phones\n• Menus and prices\n\nContact admin for issues.",
        "unknown_command": "Unknown command. Use /help for guidance.",
        "feedback_prompt": "Please send your feedback (e.g., a restaurant review):",
        "feedback_thanks": "Thank you for your feedback!",
        "search_prompt": "Enter a restaurant or dish name:",
        "search_results": "Search results:\n\n{results}",
        "no_search_results": "No results found. Please try again.",
        "select_language": "Select a language:",
        "language_updated": "Language changed: {lang}",
        "main_menu": "Main menu:",
    },
}

def get_message(lang: str, key: str, **kwargs) -> str:
    """Lokallashtirilgan xabar olish."""
    return MESSAGES.get(lang, MESSAGES["uz"]).get(key, "").format(**kwargs)

def generate_region_buttons(lang: str = "uz") -> InlineKeyboardMarkup:
    """Tuman tanlash uchun inline klaviaturasini yaratish."""
    keyboard = []
    row = []
    for i, (region_id, region_name) in enumerate(qashqadaryo_regions.items()):
        row.append(InlineKeyboardButton(region_name, callback_data=f"region_{region_id}"))
        if (i + 1) % 2 == 0 or i == len(qashqadaryo_regions) - 1:
            keyboard.append(row)
            row = []
    return InlineKeyboardMarkup(keyboard)

def generate_main_menu(lang: str = "uz") -> ReplyKeyboardMarkup:
    """Asosiy menyuni yaratish uchun reply klaviaturasini yaratish."""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(get_message(lang, "select_region")), KeyboardButton("🔍 Qidiruv")],
            [KeyboardButton("📝 Fikr bildirish"), KeyboardButton("🌐 Tilni o'zgartirish")],
            [KeyboardButton("❓ Yordam"), KeyboardButton("ℹ️ Bot haqida")],
        ],
        resize_keyboard=True,
    )

def save_feedback(user_id: int, username: str, feedback: str, restaurant: str = None):
    """Foydalanuvchi fikr-mulohazasini JSON faylga saqlash."""
    try:
        data = []
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.append({
            "user_id": user_id,
            "username": username or "unknown",
            "feedback": feedback,
            "restaurant": restaurant,
            "timestamp": str(asyncio.get_event_loop().time()),
        })
        with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Fikr-mulohaza saqlashda xatolik: {e}")

async def notify_admin(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Admin ga xabar yuborish."""
    try:
        if ADMIN_CHAT_ID != "YOUR_ADMIN_CHAT_ID":
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)
    except Exception as e:
        logger.error(f"Admin ga xabar yuborishda xatolik: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """/start buyrug'ini ishlatish va asosiy menyuni ko'rsatish."""
    user = update.effective_user
    context.user_data["lang"] = context.user_data.get("lang", "uz")
    lang = context.user_data["lang"]
    reply_text = get_message(lang, "welcome", name=user.first_name) + get_message(lang, "main_menu")
    try:
        await update.message.reply_text(reply_text, reply_markup=generate_main_menu(lang))
        return REGION
    except Exception as e:
        logger.error(f"start da xatolik: {e}")
        await update.message.reply_text(get_message(lang, "error"))
        return ConversationHandler.END

async def region_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tuman tanlashni boshqarish."""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "uz")

    try:
        region_id = query.data.split("_")[1]
        if region_id not in qashqadaryo_regions:
            await query.edit_message_text(
                text=get_message(lang, "invalid_selection"),
                reply_markup=generate_region_buttons(lang),
            )
            return REGION

        context.user_data["region"] = region_id
        region_name = qashqadaryo_regions[region_id]

        if region_id in oshxona_data and oshxona_data[region_id]:
            reply_text = get_message(lang, "select_restaurant", region=region_name)
            keyboard = [
                [InlineKeyboardButton(name, callback_data=f"restaurant_{name}")]
                for name in oshxona_data[region_id].keys()
            ]
            keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data="back_to_regions")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(text=reply_text, reply_markup=reply_markup)
            return RESTAURANT
        else:
            await query.edit_message_text(
                text=get_message(lang, "no_data_region", region=region_name),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⬅️ Ortga", callback_data="back_to_regions")]]
                ),
            )
            return REGION
    except Exception as e:
        logger.error(f"region_callback da xatolik: {e}")
        await query.edit_message_text(
            text=get_message(lang, "error"),
            reply_markup=generate_region_buttons(lang),
        )
        await notify_admin(context, f"User {update.effective_user.id} uchun region_callback da xatolik: {e}")
        return REGION

async def restaurant_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Oshxona tanlashni boshqarish."""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "uz")

    try:
        restaurant_name = query.data.split("_")[1]
        region_id = context.user_data.get("region")
        if not region_id or region_id not in oshxona_data or restaurant_name not in oshxona_data[region_id]:
            await query.edit_message_text(
                text=get_message(lang, "invalid_selection"),
                reply_markup=generate_region_buttons(lang),
            )
            return REGION

        context.user_data["restaurant"] = restaurant_name
        restaurant_data = oshxona_data[region_id][restaurant_name]
        menu_text = "\n".join(f"- {dish}: {price}" for dish, price in restaurant_data["menu"].items())
        reply_text = get_message(
            lang,
            "restaurant_info",
            name=restaurant_name,
            location=restaurant_data["location"],
            phone=restaurant_data["phone"],
            rating=restaurant_data["rating"],
            menu=menu_text,
        )

        keyboard = [
            [InlineKeyboardButton("📋 To'liq menyu", callback_data=f"menu_{restaurant_name}")],
            [InlineKeyboardButton("📍 Live lokatsiya", callback_data=f"live_location_{restaurant_name}")],
            [InlineKeyboardButton("🗺 Google Maps", callback_data=f"google_maps_{restaurant_name}")],
            [InlineKeyboardButton("📝 Fikr bildirish", callback_data=f"feedback_{restaurant_name}")],
            [InlineKeyboardButton("⬅️ Oshxonalarga qaytish", callback_data="back_to_restaurants")],
            [InlineKeyboardButton("🏠 Bosh sahifaga", callback_data="back_to_regions")],
        ]

        await query.edit_message_text(
            text=reply_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
        return MENU
    except Exception as e:
        logger.error(f"restaurant_callback da xatolik: {e}")
        await query.edit_message_text(
            text=get_message(lang, "error"),
            reply_markup=generate_region_buttons(lang),
        )
        await notify_admin(context, f"User {update.effective_user.id} uchun restaurant_callback da xatolik: {e}")
        return REGION

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Menyu, lokatsiya, xarita va fikr-mulohaza harakatlarini boshqarish."""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "uz")

    try:
        action, restaurant_name = query.data.split("_", 1)
        region_id = context.user_data.get("region")
        if not region_id or region_id not in oshxona_data or restaurant_name not in oshxona_data[region_id]:
            await query.edit_message_text(
                text=get_message(lang, "invalid_selection"),
                reply_markup=generate_region_buttons(lang),
            )
            return REGION

        restaurant_data = oshxona_data[region_id][restaurant_name]
        keyboard = [
            [InlineKeyboardButton("⬅️ Oshxonaga qaytish", callback_data=f"restaurant_{restaurant_name}")],
            [InlineKeyboardButton("🏠 Bosh sahifaga", callback_data="back_to_regions")],
        ]

        if action == "menu":
            menu_text = "\n".join(f"• *{dish}*: {price}" for dish, price in restaurant_data["menu"].items())
            reply_text = get_message(lang, "full_menu", name=restaurant_name, menu=menu_text)
        elif action == "live_location":
            await query.message.reply_location(
                latitude=restaurant_data["latitude"],
                longitude=restaurant_data["longitude"],
                live_period=3600,
            )
            reply_text = get_message(lang, "live_location", name=restaurant_name, location=restaurant_data["location"])
        elif action == "google_maps":
            maps_url = f"https://www.google.com/maps?q={restaurant_data['latitude']},{restaurant_data['longitude']}"
            reply_text = get_message(lang, "google_maps", name=restaurant_name, location=restaurant_data["location"], url=maps_url)
        elif action == "feedback":
            context.user_data["feedback_restaurant"] = restaurant_name
            reply_text = get_message(lang, "feedback_prompt")
            keyboard = [[InlineKeyboardButton("Bekor qilish", callback_data=f"restaurant_{restaurant_name}")]]
            await query.message.reply_text(reply_text, reply_markup=InlineKeyboardMarkup(keyboard))
            return FEEDBACK
        else:
            reply_text = get_message(lang, "invalid_selection")

        await query.edit_message_text(
            text=reply_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
        return MENU
    except Exception as e:
        logger.error(f"menu_callback da xatolik: {e}")
        await query.edit_message_text(
            text=get_message(lang, "error"),
            reply_markup=generate_region_buttons(lang),
        )
        await notify_admin(context, f"User {update.effective_user.id} uchun menu_callback da xatolik: {e}")
        return REGION

async def feedback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Foydalanuvchi fikr-mulohazasini qabul qilish."""
    lang = context.user_data.get("lang", "uz")
    user = update.effective_user
    feedback = update.message.text
    restaurant = context.user_data.get("feedback_restaurant")

    try:
        save_feedback(user.id, user.username, feedback, restaurant)
        await update.message.reply_text(
            get_message(lang, "feedback_thanks"), reply_markup=generate_main_menu(lang)
        )
        await notify_admin(
            context,
            f"Yangi fikr-mulohaza {user.username or user.id} dan:\nOshxona: {restaurant or 'N/A'}\nFikr: {feedback}",
        )
        return REGION
    except Exception as e:
        logger.error(f"feedback_handler da xatolik: {e}")
        await update.message.reply_text(get_message(lang, "error"), reply_markup=generate_main_menu(lang))
        await notify_admin(context, f"User {user.id} uchun feedback_handler da xatolik: {e}")
        return REGION

async def search_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Oshxona yoki taom qidirishni boshqarish."""
    lang = context.user_data.get("lang", "uz")
    query = update.message.text.lower()

    try:
        results = []
        for region_id, restaurants in oshxona_data.items():
            region_name = qashqadaryo_regions[region_id]
            for name, data in restaurants.items():
                if query in name.lower():
                    results.append(f"📍 {name} ({region_name})\n- Manzil: {data['location']}\n- Telefon: {data['phone']}")
                else:
                    for dish in data["menu"].keys():
                        if query in dish.lower():
                            results.append(f"🍽️ {dish} at {name} ({region_name})\n- Narx: {data['menu'][dish]}")
        if results:
            reply_text = get_message(lang, "search_results", results="\n\n".join(results[:5]))
        else:
            reply_text = get_message(lang, "no_search_results")
        await update.message.reply_text(reply_text, reply_markup=generate_main_menu(lang))
        return REGION
    except Exception as e:
        logger.error(f"search_handler da xatolik: {e}")
        await update.message.reply_text(get_message(lang, "error"), reply_markup=generate_main_menu(lang))
        await notify_admin(context, f"User {update.effective_user.id} uchun search_handler da xatolik: {e}")
        return REGION

async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Til tanlashni boshqarish."""
    lang = context.user_data.get("lang", "uz")
    keyboard = [[InlineKeyboardButton(lang_data["name"], callback_data=f"lang_{lang_code}")]
                for lang_code, lang_data in LANGUAGES.items()]
    try:
        await update.message.reply_text(
            get_message(lang, "select_language"),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return LANGUAGE
    except Exception as e:
        logger.error(f"language_handler da xatolik: {e}")
        await update.message.reply_text(get_message(lang, "error"), reply_markup=generate_main_menu(lang))
        return REGION

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tilni o'zgartirishni boshqarish."""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "uz")

    try:
        new_lang = query.data.split("_")[1]
        if new_lang in LANGUAGES:
            context.user_data["lang"] = new_lang
            await query.edit_message_text(
                text=get_message(new_lang, "language_updated", lang=LANGUAGES[new_lang]["name"]),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("OK", callback_data="back_to_regions")]]),
            )
        else:
            await query.edit_message_text(
                text=get_message(lang, "invalid_selection"),
                reply_markup=generate_region_buttons(lang),
            )
        return REGION
    except Exception as e:
        logger.error(f"language_callback da xatolik: {e}")
        await query.edit_message_text(
            text=get_message(lang, "error"),
            reply_markup=generate_region_buttons(lang),
        )
        await notify_admin(context, f"User {update.effective_user.id} uchun language_callback da xatolik: {e}")
        return REGION

async def back_to_regions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tuman tanlashga qaytish."""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "uz")
    try:
        await query.edit_message_text(
            text=get_message(lang, "select_region"),
            reply_markup=generate_region_buttons(lang),
        )
        return REGION
    except Exception as e:
        logger.error(f"back_to_regions da xatolik: {e}")
        await query.edit_message_text(
            text=get_message(lang, "error"),
            reply_markup=generate_region_buttons(lang),
        )
        await notify_admin(context, f"User {update.effective_user.id} uchun back_to_regions da xatolik: {e}")
        return REGION

async def back_to_restaurants(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Oshxona tanlashga qaytish."""
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "uz")

    try:
        region_id = context.user_data.get("region")
        if not region_id or region_id not in qashqadaryo_regions:
            await query.edit_message_text(
                text=get_message(lang, "invalid_selection"),
                reply_markup=generate_region_buttons(lang),
            )
            return REGION

        region_name = qashqadaryo_regions[region_id]
        reply_text = get_message(lang, "select_restaurant", region=region_name)
        keyboard = [
            [InlineKeyboardButton(name, callback_data=f"restaurant_{name}")]
            for name in oshxona_data[region_id].keys()
        ]
        keyboard.append([InlineKeyboardButton("⬅️ Ortga", callback_data="back_to_regions")])
        await query.edit_message_text(
            text=reply_text, reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return RESTAURANT
    except Exception as e:
        logger.error(f"back_to_restaurants da xatolik: {e}")
        await query.edit_message_text(
            text=get_message(lang, "error"),
            reply_markup=generate_region_buttons(lang),
        )
        await notify_admin(context, f"User {update.effective_user.id} uchun back_to_restaurants da xatolik: {e}")
        return REGION

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Yordam ma'lumotini ko'rsatish."""
    lang = context.user_data.get("lang", "uz")
    try:
        await update.message.reply_text(
            get_message(lang, "help"), parse_mode="Markdown", reply_markup=generate_main_menu(lang)
        )
    except Exception as e:
        logger.error(f"help_command da xatolik: {e}")
        await update.message.reply_text(get_message(lang, "error"), reply_markup=generate_main_menu(lang))
        await notify_admin(context, f"User {update.effective_user.id} uchun help_command da xatolik: {e}")

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bot haqida ma'lumotni ko'rsatish."""
    lang = context.user_data.get("lang", "uz")
    try:
        await update.message.reply_text(
            get_message(lang, "about"), parse_mode="Markdown", reply_markup=generate_main_menu(lang)
        )
    except Exception as e:
        logger.error(f"about_command da xatolik: {e}")
        await update.message.reply_text(get_message(lang, "error"), reply_markup=generate_main_menu(lang))
        await notify_admin(context, f"User {update.effective_user.id} uchun about_command da xatolik: {e}")

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Noma'lum buyruqlarni boshqarish."""
    lang = context.user_data.get("lang", "uz")
    try:
        await update.message.reply_text(
            get_message(lang, "unknown_command"), reply_markup=generate_main_menu(lang)
        )
    except Exception as e:
        logger.error(f"unknown_command da xatolik: {e}")
        await update.message.reply_text(get_message(lang, "error"), reply_markup=generate_main_menu(lang))
        await notify_admin(context, f"User {update.effective_user.id} uchun unknown_command da xatolik: {e}")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Matn kiritishni boshqarish uchun asosiy menyuni tanlash."""
    lang = context.user_data.get("lang", "uz")
    text = update.message.text
    try:
        if text == get_message(lang, "select_region"):
            await update.message.reply_text(
                get_message(lang, "select_region"), reply_markup=generate_region_buttons(lang)
            )
            return REGION
        elif text == "🔍 Qidiruv":
            await update.message.reply_text(
                get_message(lang, "search_prompt"), reply_markup=generate_main_menu(lang)
            )
            return SEARCH
        elif text == "📝 Fikr bildirish":
            context.user_data["feedback_restaurant"] = None
            await update.message.reply_text(
                get_message(lang, "feedback_prompt"), reply_markup=generate_main_menu(lang)
            )
            return FEEDBACK
        elif text == "🌐 Tilni o'zgartirish":
            await language_handler(update, context)
            return LANGUAGE
        elif text == "❓ Yordam":
            await help_command(update, context)
            return REGION
        elif text == "ℹ️ Bot haqida":
            await about_command(update, context)
            return REGION
        else:
            await update.message.reply_text(
                get_message(lang, "unknown_command"), reply_markup=generate_main_menu(lang)
            )
            return REGION
    except Exception as e:
        logger.error(f"text_handler da xatolik: {e}")
        await update.message.reply_text(get_message(lang, "error"), reply_markup=generate_main_menu(lang))
        await notify_admin(context, f"User {update.effective_user.id} uchun text_handler da xatolik: {e}")
        return REGION

def main() -> None:
    """Botni ishga tushirish va xavfsiz yopish."""
    try:
        application = (
            Application.builder()
            .token(TOKEN)
            .rate_limiter(True)
            .build()
        )

        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", start),
                MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler),
            ],
            states={
                REGION: [
                    CallbackQueryHandler(region_callback, pattern=r"^region_"),
                    CallbackQueryHandler(back_to_regions, pattern=r"^back_to_regions$"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler),
                ],
                RESTAURANT: [
                    CallbackQueryHandler(restaurant_callback, pattern=r"^restaurant_"),
                    CallbackQueryHandler(back_to_regions, pattern=r"^back_to_regions$"),
                ],
                MENU: [
                    CallbackQueryHandler(menu_callback, pattern=r"^menu_|^live_location_|^google_maps_|^feedback_"),
                    CallbackQueryHandler(restaurant_callback, pattern=r"^restaurant_"),
                    CallbackQueryHandler(back_to_restaurants, pattern=r"^back_to_restaurants$"),
                    CallbackQueryHandler(back_to_regions, pattern=r"^back_to_regions$"),
                ],
                FEEDBACK: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_handler),
                    CallbackQueryHandler(restaurant_callback, pattern=r"^restaurant_"),
                ],
                SEARCH: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, search_handler),
                ],
                LANGUAGE: [
                    CallbackQueryHandler(language_callback, pattern=r"^lang_"),
                    CallbackQueryHandler(back_to_regions, pattern=r"^back_to_regions$"),
                ],
            },
            fallbacks=[
                CommandHandler("start", start),
                CommandHandler("help", help_command),
                CommandHandler("about", about_command),
                MessageHandler(filters.COMMAND, unknown_command),
            ],
            per_message=True,
        )

        application.add_handler(conv_handler)
        logger.info("Bot ishga tushmoqda...")
        application.run_polling()
    except Exception as e:
        logger.error(f"main da xatolik: {e}")
        if str(e).startswith("TELEGRAM_BOT_TOKEN"):
            logger.error("Iltimos, TELEGRAM_BOT_TOKEN muhit o'zgaruvchisini to'g'ri o'rnating.")
        raise
    finally:
        logger.info("Bot yopilmoqda...")

if __name__ == "__main__":
    main()
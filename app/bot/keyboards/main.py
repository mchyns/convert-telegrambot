from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Main menu inline keyboard."""
    buttons = [
        [
            InlineKeyboardButton(
                text="📖 Cara Menggunakan", callback_data="help_usage"
            ),
            InlineKeyboardButton(
                text="📄 Format Didukung", callback_data="help_formats"
            ),
        ],
        [
            InlineKeyboardButton(text="📊 Status Saya", callback_data="menu_status"),
            InlineKeyboardButton(text="ℹ️ Tentang Bot", callback_data="menu_about"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Simple back button keyboard."""
    buttons = [
        [InlineKeyboardButton(text="« Kembali ke Menu", callback_data="menu_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

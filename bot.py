from database import Database
from ai_handler import ask_ai, draw_image

# Altına da şu fonksiyonu eklemeyi unutma (Main.py bunu çağırıyor):
def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("sor", sor_cmd))
    app.add_handler(CommandHandler("draw", draw_cmd))
    app.add_handler(CommandHandler("setup", setup_cmd))
    app.add_handler(CommandHandler("settings", settings_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND | filters.ANIMATION | filters.VIDEO | filters.PHOTO, message_handler))

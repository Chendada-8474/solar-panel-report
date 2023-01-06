import pandas as pd
import geopandas as gpd
from telegram.ext import (
    Filters,
    ExtBot,
    Updater,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.components import BotReply
from utils.sql_commander import (
    get_admin_ids,
    get_ponds_nearby_as_geopandas,
    _coord_trans,
    connection_info,
)

ADMIN = get_admin_ids()
TELEGRAM_TOKEN = connection_info["telegram"]["token"]
bot = ExtBot(TELEGRAM_TOKEN)
bot_reply = BotReply()
geodf_memory = {}

LISTEN_LOCATION, POND_SELECT = range(2)


def report(update, context):
    user_id = str(update.message.chat.id)
    if user_id not in ADMIN:
        bot.send_message(user_id, bot_reply.permission_deny())
        return ConversationHandler.END
    bot.send_message(user_id, bot_reply.ask_location())
    return LISTEN_LOCATION


def listen_location(update, context):
    user_id = update.message.chat.id
    x, y = update.message.location.longitude, update.message.location.latitude
    ponds = get_ponds_nearby_as_geopandas(x, y)

    if not len(ponds):
        bot.send_message(user_id, bot_reply.no_pond_selected())
        return ConversationHandler.END

    geodf_memory[user_id] = ponds
    x, y = _coord_trans(x, y)
    bot.send_photo(user_id, photo=bot_reply.selected_ponds_img(ponds, (x, y)))
    bot.send_message(user_id, bot_reply.ask_pond_index)
    return POND_SELECT


def pond_select(update, context):
    user_id = update.message.chat.id
    mes = update.message.text

    if not str(mes).isdigit() and int(mes) >= len(geodf_memory[user_id]):
        bot.send_message(user_id, bot_reply.no_pond_selected())
        return

    return


def main():
    updater = Updater(TELEGRAM_TOKEN)
    updater.dispatcher.add_handler(
        ConversationHandler(
            [CommandHandler("report", report)],
            {
                LISTEN_LOCATION: [MessageHandler(Filters.location, listen_location)],
                POND_SELECT: [MessageHandler(Filters.text), pond_select],
            },
        )
    )

    updater.start_polling(timeout=600)
    updater.idle()


if __name__ == "__main__":
    main()

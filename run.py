from telegram.ext import (
    Filters,
    ExtBot,
    Updater,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
)
from utils.components import BotReply, Bottons
from utils.sql_commander import (
    get_user_ids,
    get_solar_panel_types,
    get_ponds_nearby_as_geopandas,
    update_panel_type,
    _coord_trans,
    connection_info,
)

ADMINS = get_user_ids(admin=True)
USERS_IDS = get_user_ids()
TELEGRAM_TOKEN = connection_info["telegram"]["token"]
bot = ExtBot(TELEGRAM_TOKEN)
bot_reply = BotReply()
bot_button = Bottons()
geodf_memory = {}

LISTEN_LOCATION, LISTEN_POND, LISTEN_PANEL_TYPE, SELECT_CONTINUE = range(4)
LISTEN_CEHCK_LOCATION = 0


def report(update, context):
    user_id = str(update.message.chat.id)

    if user_id not in USERS_IDS:
        bot.send_message(user_id, bot_reply.permission_deny())
        return ConversationHandler.END

    bot.send_message(user_id, bot_reply.ask(question="location"))
    return LISTEN_LOCATION


def listen_location(update, context):
    user_id = str(update.message.chat.id)
    x, y = update.message.location.longitude, update.message.location.latitude
    ponds = get_ponds_nearby_as_geopandas(x, y)

    if not len(ponds):
        bot.send_message(user_id, bot_reply.no_pond_selected())
        return ConversationHandler.END

    x, y = _coord_trans(x, y)
    geodf_memory[user_id] = {"ponds": ponds, "location": (x, y)}
    bot.send_photo(user_id, photo=bot_reply.selected_ponds_img(ponds, (x, y)))
    bot.send_message(
        user_id,
        "%s\n%s" % (bot_reply.ask(question="pond_index"), bot_reply.current_location()),
    )
    return LISTEN_POND


def listen_pond(update, context):
    user_id = str(update.message.chat.id)
    pond_id = str(update.message.text)

    if not pond_id.isdigit() and int(pond_id) >= len(geodf_memory[user_id]):
        bot.send_message(user_id, bot_reply.no_pond_selected())
        return

    geodf_memory[user_id]["current_pond"] = int(pond_id)
    bot.send_message(
        user_id,
        bot_reply.ask(question="panel_type"),
        reply_markup=bot_button.panel_types_markup,
    )
    return LISTEN_PANEL_TYPE


def listen_panel_type(update, context):
    user_id = str(update.callback_query.message.chat.id)
    callback = update.callback_query.data
    pond_id = geodf_memory[user_id]["current_pond"]
    geodf_memory[user_id]["ponds"].at[pond_id, "solar_panel_type"] = callback

    ponds = geodf_memory[user_id]["ponds"]
    location = geodf_memory[user_id]["location"]
    bot.send_photo(user_id, photo=bot_reply.selected_ponds_img(ponds, location))

    bot.send_message(
        user_id,
        bot_reply.ask(question="end_select"),
        reply_markup=bot_button.continue_report_markup,
    )
    return SELECT_CONTINUE


def select_continue(update, context):
    user_id = str(update.callback_query.message.chat.id)
    callback = update.callback_query.data

    if callback == "confirm":
        print(geodf_memory[user_id]["ponds"])
        # update_panel_type(geodf_memory[user_id]["ponds"])
        bot.send_message(user_id, bot_reply.update_done())
        return ConversationHandler.END

    elif callback == "continue":
        bot.send_message(user_id, bot_reply.ask(question="pond_index"))
        return LISTEN_POND

    elif callback == "cancel":
        bot.send_message(user_id, bot_reply.report_cancel())
        return ConversationHandler.END


def check(update, context):
    user_id = str(update.message.chat.id)

    if user_id not in USERS_IDS:
        bot.send_message(user_id, bot_reply.permission_deny())
        return ConversationHandler.END

    bot.send_message(user_id, bot_reply.ask(question="location"))
    return LISTEN_CEHCK_LOCATION


def listen_check_location(update, context):
    user_id = str(update.message.chat.id)
    x, y = update.message.location.longitude, update.message.location.latitude

    ponds = get_ponds_nearby_as_geopandas(x, y)

    if not len(ponds):
        bot.send_message(user_id, bot_reply.no_pond_checked())
        return ConversationHandler.END

    x, y = _coord_trans(x, y)
    geodf_memory[user_id] = {"ponds": ponds, "location": (x, y)}
    bot.send_photo(user_id, photo=bot_reply.selected_ponds_img(ponds, (x, y)))
    return ConversationHandler.END


def contact(update, context):
    user_id = str(update.message.chat.id)
    bot.send_message(user_id, bot_reply.shuyen.title)
    bot.send_contact(
        user_id,
        phone_number=bot_reply.shuyen.phone_number,
        first_name=bot_reply.shuyen.first_name,
    )
    bot.send_message(user_id, bot_reply.hunter.title)
    bot.send_contact(
        user_id,
        phone_number=bot_reply.hunter.phone_number,
        first_name=bot_reply.hunter.first_name,
    )
    bot.send_message(user_id, bot_reply.chendada.title)
    bot.send_contact(
        user_id,
        phone_number=bot_reply.chendada.phone_number,
        first_name=bot_reply.chendada.first_name,
    )


def manual(update, context):
    user_id = str(update.message.chat.id)
    bot.send_message(user_id, bot_reply.manual_url())


def main():
    updater = Updater(TELEGRAM_TOKEN)

    updater.dispatcher.add_handler(CommandHandler("manual", manual))
    updater.dispatcher.add_handler(CommandHandler("contact", contact))
    updater.dispatcher.add_handler(
        ConversationHandler(
            [CommandHandler("check", check)],
            {
                LISTEN_CEHCK_LOCATION: [
                    MessageHandler(Filters.location, listen_check_location)
                ]
            },
            [ConversationHandler.END],
        )
    )

    updater.dispatcher.add_handler(
        ConversationHandler(
            [CommandHandler("report", report)],
            {
                LISTEN_LOCATION: [MessageHandler(Filters.location, listen_location)],
                LISTEN_POND: [MessageHandler(Filters.text, listen_pond)],
                LISTEN_PANEL_TYPE: [CallbackQueryHandler(listen_panel_type)],
                SELECT_CONTINUE: [CallbackQueryHandler(select_continue)],
            },
            [ConversationHandler.END],
        )
    )

    updater.start_polling(timeout=600)
    updater.idle()


if __name__ == "__main__":
    main()

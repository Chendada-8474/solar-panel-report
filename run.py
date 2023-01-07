from telegram.ext import (
    Filters,
    ExtBot,
    Updater,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
)
from telegram import ReplyKeyboardRemove
from utils.components import BotReply, Bottons
from utils.sql_commander import (
    get_admins,
    get_users_by_auth,
    get_ponds_nearby_as_geopandas,
    update_panel_type,
    insert_log,
    insert_user,
    _coord_trans,
    get_unauth_info,
    authorize_user,
    connection_info,
)

ADMINS = get_admins()
USERS_IDS = get_users_by_auth(authorized=True)
TELEGRAM_TOKEN = connection_info["telegram"]["token"]
bot = ExtBot(TELEGRAM_TOKEN)
bot_reply = BotReply()
bot_button = Bottons()
geodf_memory = {}
apply_memory = {}

LISTEN_LOCATION, LISTEN_POND, LISTEN_PANEL_TYPE, SELECT_CONTINUE = range(4)
LISTEN_CEHCK_LOCATION = 0
LISTEN_ORG, LISTEN_SIGNUP_CONFIRM = range(2)
APPROVE = 0


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
    geodf_memory[user_id] = {"ponds": ponds, "location": (x, y), "updates": {}}
    bot.send_photo(user_id, photo=bot_reply.selected_ponds_img(ponds, (x, y)))
    bot.send_message(
        user_id,
        "%s\n%s" % (bot_reply.ask(question="pond_index"), bot_reply.current_location()),
    )
    return LISTEN_POND


def listen_pond(update, context):
    user_id = str(update.message.chat.id)
    pond_index = str(update.message.text)

    if not pond_index.isdigit() and int(pond_index) >= len(geodf_memory[user_id]):
        bot.send_message(user_id, bot_reply.no_pond_selected())
        return

    geodf_memory[user_id]["current_pond"] = int(pond_index)
    bot.send_message(
        user_id,
        bot_reply.ask(question="panel_type"),
        reply_markup=bot_button.panel_types_markup,
    )
    return LISTEN_PANEL_TYPE


def listen_panel_type(update, context):
    user_id = str(update.callback_query.message.chat.id)
    callback = update.callback_query.data
    pond_index = geodf_memory[user_id]["current_pond"]
    fishpond_id = geodf_memory[user_id]["ponds"].iloc[pond_index]["fishpond_id"]
    geodf_memory[user_id]["updates"][fishpond_id] = callback
    geodf_memory[user_id]["ponds"].at[pond_index, "solar_panel_type"] = callback

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
        update_panel_type(geodf_memory[user_id]["updates"])
        insert_log(geodf_memory[user_id]["updates"], user_id)
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


def signup(update, context):
    user_id = str(update.message.chat.id)
    first_name = update.message.chat.first_name
    last_name = update.message.chat.last_name
    unauth_user_ids = get_users_by_auth(authorized=False)

    if not first_name and not last_name:
        bot.send_message(user_id, bot_reply.set_name_first())
        return ConversationHandler.END

    if user_id in ADMINS:
        bot.send_message(user_id, bot_reply.auth_already(status="admin"))
        return ConversationHandler.END

    if user_id in USERS_IDS:
        bot.send_message(user_id, bot_reply.auth_already(status="user"))
        return ConversationHandler.END

    if user_id in unauth_user_ids:
        bot.send_message(user_id, bot_reply.auth_already(status="applied"))
        return ConversationHandler.END

    bot.send_message(
        user_id,
        bot_reply.ask(question="orgnization"),
        reply_markup=bot_button.org_markup,
    )
    return LISTEN_ORG


def listen_org(update, context):
    user_id = str(update.callback_query.message.chat.id)
    callback = update.callback_query.data

    apply_memory[user_id] = callback
    bot.send_message(user_id, bot_reply.selected_org(org=callback))
    bot.send_message(
        user_id, bot_reply.ask(question="signup"), reply_markup=bot_button.signup_markup
    )
    return LISTEN_SIGNUP_CONFIRM


def listen_signup_confirm(update, context):
    user_id = str(update.callback_query.message.chat.id)
    callback = update.callback_query.data
    first_name = update.callback_query.message.chat.first_name
    last_name = update.callback_query.message.chat.last_name

    if callback == "signup":
        insert_user(
            user_id,
            org=apply_memory[user_id],
            first_name=first_name,
            last_name=last_name,
        )
        bot.send_message(user_id, bot_reply.signup_sent())

        for admin in ADMINS:
            bot.send_message(
                admin, bot_reply.someone_signup(last_name, apply_memory[user_id])
            )

    elif callback == "cancel":
        bot.send_message(user_id, bot_reply.signup_cancel())

    apply_memory.pop(user_id)
    return ConversationHandler.END


def authorize(update, context):
    user_id = str(update.message.chat.id)
    if user_id not in ADMINS:
        bot.send_message(user_id, bot_reply.permission_deny())
        return ConversationHandler.END

    unauth_user_ids = get_users_by_auth(authorized=False)

    if not unauth_user_ids:
        bot.send_message(user_id, bot_reply.no_applier())
        return ConversationHandler.END

    unauth_users = get_unauth_info()
    bot.send_message(
        user_id,
        bot_reply.ask(question="applier"),
        reply_markup=bot_button.unauth_appliers(unauth_users),
    )
    return APPROVE


def approve(update, context):
    user_id = str(update.message.chat.id)
    approve_reply = str(update.message.text)
    applier_id = approve_reply.split(" ")[-1]
    bot.send_message(
        user_id,
        bot_reply.seleted_applier(applier_id),
        reply_markup=ReplyKeyboardRemove(),
    )

    unauth_user_ids = get_users_by_auth(authorized=False)

    if not applier_id.isdigit() or applier_id not in unauth_user_ids:
        bot.send_message(user_id, bot_reply.wrong_id())
        return ConversationHandler.END

    authorize_user(applier_id)
    bot.send_message(user_id, bot_reply.approved_applier())
    bot.send_message(applier_id, bot_reply.to_applier_passed())

    return ConversationHandler.END


def manual(update, context):
    user_id = str(update.message.chat.id)
    bot.send_message(user_id, bot_reply.manual_url())


def panel_type(update, context):
    user_id = str(update.message.chat.id)
    bot.send_message(user_id, bot_reply.panel_type())


def main():
    updater = Updater(TELEGRAM_TOKEN)

    updater.dispatcher.add_handler(CommandHandler("type", panel_type))
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

    updater.dispatcher.add_handler(
        ConversationHandler(
            [CommandHandler("signup", signup)],
            {
                LISTEN_ORG: [CallbackQueryHandler(listen_org)],
                LISTEN_SIGNUP_CONFIRM: [CallbackQueryHandler(listen_signup_confirm)],
            },
            [ConversationHandler.END],
        )
    )

    updater.dispatcher.add_handler(
        ConversationHandler(
            [CommandHandler("authorize", authorize)],
            {APPROVE: [MessageHandler(Filters.text, approve)]},
            [ConversationHandler.END],
        )
    )

    updater.start_polling(timeout=600)
    updater.idle()


if __name__ == "__main__":
    main()

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
from telegram.error import TelegramError
from utils.components import BotReply, Bottons
from utils.sql_commander import (
    get_admins,
    get_super_admin,
    get_users_by_auth,
    get_user_name,
    get_ponds_nearby_as_geopandas,
    update_panel_type,
    insert_log,
    insert_user,
    _coord_trans,
    get_unauth_info,
    authorize_user,
    connection_info,
)
from utils.tools import (
    GeoMemory,
    send_message_skip_no_found_chat,
    split_pond_indexes,
)

ADMINS = 0
SUPER_ADMIN = get_super_admin()
TELEGRAM_TOKEN = connection_info["telegram"]["token"]
bot = ExtBot(TELEGRAM_TOKEN)
authed_useres = get_users_by_auth(authorized=True)
bot_reply = BotReply()
bot_button = Bottons()
geodf_memory = GeoMemory()
apply_memory = {}
announcement = {}

LISTEN_LOCATION, LISTEN_POND, LISTEN_PANEL_TYPE, SELECT_CONTINUE = range(4)
LISTEN_CEHCK_LOCATION = 0
LISTEN_ORG, LISTEN_SIGNUP_CONFIRM = range(2)
APPROVE = 0
LISTEN_ANNOUNCE_CONTENT, CONFIRM_ANNOUNCE = range(2)


def report(update, context):
    user_id = str(update.message.chat.id)

    if user_id not in authed_useres:
        bot.send_message(user_id, bot_reply.say(say_what="permission_deny"))
        return ConversationHandler.END

    bot.send_message(user_id, bot_reply.ask(question="location"))
    return LISTEN_LOCATION


def listen_location(update, context):
    user_id = str(update.message.chat.id)
    x, y = update.message.location.longitude, update.message.location.latitude
    ponds = get_ponds_nearby_as_geopandas(x, y)

    if not len(ponds):
        bot.send_message(user_id, bot_reply.say(say_what="no_pond_selected"))
        return ConversationHandler.END

    x, y = _coord_trans(x, y)

    geodf_memory.init_user(user_id)
    geodf_memory.init_updates(user_id)
    geodf_memory.add(user_id, ponds, key="ponds")
    geodf_memory.add(user_id, (x, y), key="location")
    bot.send_message(
        user_id,
        "%s\n%s"
        % (
            bot_reply.ask(question="pond_index"),
            bot_reply.say(say_what="current_location"),
        ),
    )
    bot.send_photo(user_id, photo=bot_reply.selected_ponds_img(ponds, (x, y)))
    return LISTEN_POND


def listen_pond(update, context):
    user_id = str(update.message.chat.id)
    pond_indexes = split_pond_indexes(str(update.message.text))
    num_ponds = len(geodf_memory.get(user_id, "ponds"))

    if not pond_indexes or any(i >= num_ponds for i in pond_indexes):
        bot.send_message(user_id, bot_reply.say(say_what="weird_pond_index"))
        return

    geodf_memory.add(user_id, pond_indexes, key="modified_ponds")

    bot.send_message(
        user_id,
        bot_reply.ask(question="panel_type"),
        reply_markup=bot_button.panel_types_markup,
    )
    return LISTEN_PANEL_TYPE


def listen_panel_type(update, context):
    user_id = str(update.callback_query.message.chat.id)
    callback = update.callback_query.data
    pond_indexes = geodf_memory.get(user_id, key="modified_ponds")

    geodf_memory.add_updates(user_id, pond_indexes, callback)
    geodf_memory.update_mem_panel_type(user_id, pond_indexes, callback)

    ponds = geodf_memory.get(user_id, key="ponds")
    location = geodf_memory.get(user_id, key="location")
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
        updates = geodf_memory.get_updates(user_id)
        update_panel_type(updates)
        insert_log(updates, user_id)
        bot.send_message(user_id, bot_reply.say(say_what="update_done"))
        return ConversationHandler.END

    elif callback == "continue":
        bot.send_message(user_id, bot_reply.ask(question="pond_index"))
        return LISTEN_POND

    elif callback == "cancel":
        bot.send_message(user_id, bot_reply.say(say_what="report_cancel"))
        return ConversationHandler.END


def check(update, context):
    user_id = str(update.message.chat.id)

    if user_id not in authed_useres:
        bot.send_message(user_id, bot_reply.say(say_what="permission_deny"))
        return ConversationHandler.END

    bot.send_message(user_id, bot_reply.ask(question="location"))
    return LISTEN_CEHCK_LOCATION


def listen_check_location(update, context):
    user_id = str(update.message.chat.id)
    x, y = update.message.location.longitude, update.message.location.latitude

    ponds = get_ponds_nearby_as_geopandas(x, y)

    if not len(ponds):
        bot.send_message(user_id, bot_reply.say(say_what="no_pond_checked"))
        return ConversationHandler.END

    x, y = _coord_trans(x, y)
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

    if not first_name or not last_name:
        bot.send_message(user_id, bot_reply.say(say_what="set_name_first"))
        return ConversationHandler.END

    if user_id in ADMINS:
        bot.send_message(user_id, bot_reply.auth_already(status="admin"))
        return ConversationHandler.END

    if user_id in authed_useres:
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
        bot.send_message(user_id, bot_reply.say(say_what="signup_sent"))

        for admin in ADMINS:
            bot.send_message(
                admin, bot_reply.someone_signup(first_name, apply_memory[user_id])
            )

    elif callback == "cancel":
        bot.send_message(user_id, bot_reply.say(say_what="signup_cancel"))

    apply_memory.pop(user_id)
    return ConversationHandler.END


def authorize(update, context):
    user_id = str(update.message.chat.id)
    if user_id not in ADMINS:
        bot.send_message(user_id, bot_reply.say(say_what="permission_deny"))
        return ConversationHandler.END

    unauth_user_ids = get_users_by_auth(authorized=False)

    if not unauth_user_ids:
        bot.send_message(user_id, bot_reply.say(say_what="no_applier"))
        return ConversationHandler.END

    unauth_users = get_unauth_info()
    bot.send_message(
        user_id,
        bot_reply.say(say_what="auth_cancel"),
        reply_markup=ReplyKeyboardRemove(),
    )
    bot.send_message(
        user_id,
        bot_reply.ask(question="applier"),
        reply_markup=bot_button.unauth_appliers(unauth_users),
    )
    return APPROVE


def approve(update, context):
    global authed_useres
    user_id = str(update.message.chat.id)
    approve_reply = str(update.message.text)

    if approve_reply.lower() == "cancel":
        bot.send_message(
            user_id,
            bot_reply.say(say_what="cancel"),
            reply_markup=ReplyKeyboardRemove(),
        )
        return ConversationHandler.END

    applier_id = approve_reply.split(" ")[-1]
    bot.send_message(
        user_id,
        bot_reply.seleted_applier(applier_id),
        reply_markup=ReplyKeyboardRemove(),
    )

    unauth_user_ids = get_users_by_auth(authorized=False)

    if not applier_id.isdigit() or applier_id not in unauth_user_ids:
        bot.send_message(user_id, bot_reply.say(say_what="wrong_id"))
        return ConversationHandler.END

    authorize_user(applier_id)
    bot.send_message(user_id, bot_reply.say(say_what="approved_applier"))
    bot.send_message(applier_id, bot_reply.say(say_what="to_applier_passed"))
    authed_useres.add(applier_id)
    # authed_useres = get_users_by_auth(authorized=True)

    return ConversationHandler.END


def announce(update, context):
    user_id = str(update.message.chat.id)

    if user_id not in ADMINS:
        bot.send_message(user_id, bot_reply.say(say_what="permission_deny"))
        return ConversationHandler.END

    bot.send_message(user_id, bot_reply.ask(question="announce_content"))
    return LISTEN_ANNOUNCE_CONTENT


def listen_announce_contect(update, context):
    global announcement
    user_id = str(update.message.chat.id)
    announcement = str(update.message.text)

    bot.send_message(
        user_id,
        bot_reply.ask(question="send_announce"),
        reply_markup=bot_button.announce_markup,
    )
    return CONFIRM_ANNOUNCE


def confirm_announce(update, context):
    user_id = str(update.callback_query.message.chat.id)
    callback = update.callback_query.data
    announcer_name = get_user_name(user_id)

    if callback == "send":
        bot.send_message(user_id, bot_reply.say(say_what="announce_sent"))
        send_message_skip_no_found_chat(authed_useres, announcer_name, announcement)
    elif callback == "cancel":
        bot.send_message(user_id, bot_reply.say(say_what="announce_cancel"))

    return ConversationHandler.END


def manual(update, context):
    user_id = str(update.message.chat.id)
    bot.send_message(user_id, bot_reply.say(say_what="manual_url"))


def panel_type(update, context):
    user_id = str(update.message.chat.id)
    bot.send_message(user_id, bot_reply.say(say_what="panel_type"))


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

    updater.dispatcher.add_handler(
        ConversationHandler(
            [CommandHandler("announce", announce)],
            {
                LISTEN_ANNOUNCE_CONTENT: [
                    MessageHandler(Filters.text, listen_announce_contect)
                ],
                CONFIRM_ANNOUNCE: [CallbackQueryHandler(confirm_announce)],
            },
            [ConversationHandler.END],
        )
    )

    updater.start_polling(timeout=600)
    updater.idle()


if __name__ == "__main__":
    main()

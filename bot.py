from datetime import datetime

import telebot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.custom_filters import StateFilter, ChatFilter
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage, StateRedisStorage
from telebot.util import extract_arguments, extract_command, antiflood

import config
from logger import bot_logger
import database
from database import Role

storage = StateRedisStorage(host=config.redis_host, port=config.redis_port,
                            password=config.redis_password) if not config.test else StateMemoryStorage()

bot = telebot.TeleBot(token=config.token)


class MyStates(StatesGroup):
    bot = State()

    reg_buttons = State()
    team_name = State()
    host_password = State()
    host_name = State()
    admin_password = State()
    admin_name = State()

    team = State()
    host = State()
    admin = State()

    kp_one_time = State()
    kp_name = State()

    stop = State()


@bot.message_handler(commands=["start"], state=[None])
def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("Да", callback_data="reg_yes"),
                 InlineKeyboardButton("Нет", callback_data="reg_no"))
    bot.set_state(message.chat.id, MyStates.reg_buttons)
    bot.send_message(message.chat.id, "Привет! Хотите зарегистрировать команду?", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith("reg_"), state=MyStates.reg_buttons)
def reg_buttons_handler(call: CallbackQuery):
    bot.delete_state(call.from_user.id)
    bot.answer_callback_query(call.id)
    if call.data == "reg_yes":
        reg_handler(call.message)
    elif call.data == "reg_no":
        bot.send_message(call.message.chat.id, "Жаль, если захотите, то можете зарегистрироваться командой /reg")


@bot.message_handler(commands=["help"])
def help_handler(message: Message):
    state = bot.get_state(message.chat.id)
    msg = (
        "Список команд:\n\n"
        "/start - начать работу с ботом\n"
        "/reg - зарегистрировать команду\n"
        "/reg_host - зарегистрировать КПшника\n"
        "/reg_admin - зарегистрировать админа\n"
        "/list_free - список свободных КПшек\n"
        "/list_all - список всех КПшек\n"
        "/help - список команд\n"
    )
    if state == MyStates.team.name:
        msg += (
            "/balance - баланс команды\n"
            "/transfer <amount> to <recipient> - перевести деньги другой команде\n"
            "/queue_to <point_id> - занять очередь на КПшку\n"
            "/place - место в очереди\n"
            "/remove_queue - отменить свою очередь\n"
            "/stop - закончить участие\n"
        )
    if state == MyStates.host.name:
        msg += (
            "/add_host_to <point_id> - стать КПшником на выбранной точке\n"
            "/remove_host - перестать быть КПшником на выбранной точке\n"
            "/start_team - начать работу с командой\n"
            "/payment <amount> - оплата товара в магазине (деньги снимутся со счёта текущей команды)\n"
            "/payment_nal <amount> - оплата товара в магазине наличкой (деньги снимутся со счёта текущей команды)\n"
            "/pay <amount> - выплата за прохождение КПшки (деньги начислятся на счёт текущей команды)\n"
            "/pay_nal <amount> - выплата за прохождение КПшки наличкой (деньги начислятся на счёт текущей команды)\n"
            "/stop_team - закончить работу с командой\n"
            "/kp_pause - приостановить работу КПшки\n"
            "/kp_resume - возобновить работу КПшки\n"
        )
    if state == MyStates.admin.name:
        msg += (
            "/reg_kp - зарегистрировать КПшку\n"
            "/total_money - общее количество денег\n"
        )
    if state in [MyStates.host.name, MyStates.admin.name]:
        msg += (
            "/reg_team <team_name> - зарегистрировать команду\n"
            "/queue_team <team_id> to <point_id> - занять очередь на КПшку для выбранной команды\n"
            "remove_team_queue <team_id> - отменить очередь для выбранной команды\n"
            "/transfer_from_team <team_id> <amount> to <recipient> - перевести деньги другой команде\n"
            "/kp_balance <point_id> - баланс КПшки (наличка)\n"
        )
    bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=["reg"], state=[None])
def reg_handler(message: Message):
    bot.set_state(message.chat.id, MyStates.team_name)
    bot.send_message(message.chat.id, "Введите название команды")


@bot.message_handler(state=MyStates.team_name)
def team_name_handler(message: Message):
    bot.delete_state(message.chat.id)
    try:
        team_id = database.add.user(Role.player, message.text.lower(), message.chat.id)
        if team_id:
            bot.set_state(message.chat.id, MyStates.team)
            bot_logger.info(f"New team: {message.text.lower()} (tg_id: {message.chat.id}, team_id: {team_id})")
            bot.send_message(message.chat.id, f"Ваш номер счёта: {team_id}")
        else:
            bot.set_state(message.chat.id, MyStates.team_name)
            bot.send_message(message.chat.id, "Такая команда уже существует, попробуйте другое название")
    except ConnectionError as e:
        bot.set_state(message.chat.id, MyStates.team_name)
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        for admin_id in config.admin_ids:
            antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["balance"], state=MyStates.team)
def balance_handler(message: Message):
    try:
        balance = database.get.user_balance(message.chat.id)
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        for admin_id in config.admin_ids:
            antiflood(bot.send_message, admin_id, e.args[0])
    else:
        if balance is not None:
            bot.send_message(message.chat.id, f"Ваш баланс - {balance}")
        else:
            bot.send_message(message.chat.id, "Не удалось получить данные о балансе")


@bot.message_handler(commands=["transfer"], state=MyStates.team)
def transfer_handler(message: Message):
    args = extract_arguments(message.text).split(" to ")
    if len(args) != 2 or not args[0].isdigit() or not args[1].isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        amount = int(args[0])
        recipient = int(args[1])
        try:
            user = database.get.user(user_id=recipient)
            if user is not None and database.update.transfer(recipient, amount, from_user_tg_id=message.chat.id):
                bot_logger.info(f"Transfer: {amount} from tg_id: {message.chat.id} to team_id: {recipient}")
                bot.send_message(message.chat.id, f"Перевод выполнен! "
                                                  f"Переведено {amount} команде {user.name} ({user.id})")
            else:
                bot.send_message(message.chat.id, "Не получилось, проверьте правильность введенных данных")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            for admin_id in config.admin_ids:
                antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["queue_to"], state=MyStates.team)
def queue_to_handler(message: Message):
    args = extract_arguments(message.text)
    if len(args) == 0 or not args.isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        point_id = int(args)
        try:
            point = database.get.point(point_id=point_id)
            if point is not None and database.add.queue(point_id, datetime.now(), tg_id=message.chat.id):
                bot_logger.info(f"Queue: tg_id: {message.chat.id} to point_id: {point_id}")
                bot.send_message(message.chat.id, f"Теперь вы в очереди на КПшку {point.name}!")
            else:
                bot.send_message(message.chat.id, "Не получилось, проверьте нет ли у вас активной очереди")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            for admin_id in config.admin_ids:
                antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["place"], state=MyStates.team)
def place_handler(message: Message):
    try:
        place = database.get.user_queue_place(message.chat.id)
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        for admin_id in config.admin_ids:
            antiflood(bot.send_message, admin_id, e.args[0])
    else:
        if place is None:
            bot.send_message(message.chat.id, "У вас нет активной очереди")
        else:
            bot.send_message(message.chat.id, f"Ваше место в очереди - {place}")


@bot.message_handler(commands=["remove_queue"], state=MyStates.team)
def remove_queue_handler(message: Message):
    with bot.retrieve_data(message.chat.id) as data:
        active = data.get("active", False)
    if active:
        bot.send_message(message.chat.id, "Вы не можете отменить очередь, пока находитесь на КПшке")
    else:
        try:
            if database.remove.queue(tg_id=message.chat.id):
                bot_logger.info(f"Remove queue: tg_id: {message.chat.id}")
                bot.send_message(message.chat.id, "Очередь отменена!")
            else:
                bot.send_message(message.chat.id, "Не получилось, проверьте есть ли у вас очередь")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            for admin_id in config.admin_ids:
                antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["list_free"], state=[MyStates.team, MyStates.host, MyStates.admin])
def list_free_handler(message: Message):
    try:
        points = database.get.free_points(message.chat.id)
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        for admin_id in config.admin_ids:
            antiflood(bot.send_message, admin_id, e.args[0])
    else:
        if len(points) > 0:
            msg = "\n".join(f"{point[0]} - {point[1]}" for point in points)
            bot.send_message(message.chat.id, f"Свободные КПшки:\n{msg}")
        else:
            bot.send_message(message.chat.id, "Свободных КПшек нет")


@bot.message_handler(commands=["list_all"], state=[MyStates.team, MyStates.host, MyStates.admin])
def list_all_handler(message: Message):
    try:
        points = database.get.all_points()
        if len(points) > 0:
            msg = "\n".join(f"{point[0]} - {point[1]}" for point in points)
            bot.send_message(message.chat.id, f"Все КПшки:\n{msg}")
        else:
            bot.send_message(message.chat.id, "КПшек нет")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        for admin_id in config.admin_ids:
            antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["stop"], state=MyStates.team)
def stop_handler(message: Message):
    bot.set_state(message.chat.id, MyStates.stop)
    bot_logger.info(f"Stop: tg_id: {message.chat.id}")
    bot.send_message(message.chat.id, "Спасибо за участие!")
    try:
        database.remove.queue(tg_id=message.chat.id)
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        for admin_id in config.admin_ids:
            antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["reg_host"], state=[None])
def reg_host_handler(message: Message):
    with bot.retrieve_data(bot.user.id) as data:
        failed_hosts = data.get("failed_hosts", [])
    if message.from_user.id in failed_hosts:
        bot.send_message(message.chat.id, "Вы уже пытались зарегистрироваться хостом, обратитесь к администратору")
    else:
        bot.set_state(message.chat.id, MyStates.host_password)
        bot.add_data(message.chat.id, retries=2)
        bot.send_message(message.chat.id, "Введите пароль для хостов, у вас три попытки")


@bot.message_handler(state=MyStates.host_password)
def host_password_handler(message: Message):
    with bot.retrieve_data(message.chat.id) as data:
        retries = data.get("retries", 2)
    bot.delete_state(message.chat.id)
    with bot.retrieve_data(bot.user.id) as data:
        host_password = data.get("host_password")
    if message.text == host_password:
        bot.set_state(message.chat.id, MyStates.host_name)
        bot.send_message(message.chat.id, "Введи своё имя")
    else:
        if retries == 0:
            with bot.retrieve_data(bot.user.id) as data:
                failed_hosts = data.get("failed_hosts", [])
            failed_hosts.append(message.from_user.id)
            bot.add_data(bot.user.id, failed_hosts=failed_hosts)
            bot.send_message(message.chat.id, "Неверный  пароль, попытки кончились, обратитесь к администратору для "
                                              "сброса количества попыток и получения пароля")
        else:
            bot.set_state(message.chat.id, MyStates.host_password)
            bot.add_data(message.chat.id, retries=retries - 1)
            bot.send_message(message.chat.id, f"Неверный пароль, осталось попыток: {retries}")


@bot.message_handler(state=MyStates.host_name)
def host_name_handler(message: Message):
    bot.delete_state(message.chat.id)
    try:
        if database.add.user(Role.host, message.text, message.chat.id):
            bot.set_state(message.chat.id, MyStates.host)
            bot_logger.info(f"Host: tg_id: {message.chat.id}, name: {message.text}")
            bot.send_message(message.chat.id, "Вы успешно зарегистрированы как КПшник")
        else:
            bot.set_state(message.chat.id, MyStates.host_name)
            bot.send_message(message.chat.id, "КПшник с таким именем уже есть, попробуйте другое имя")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        for admin_id in config.admin_ids:
            antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["add_host_to"], state=MyStates.host)
def add_host_to_handler(message: Message):
    args = extract_arguments(message.text)
    if len(args) == 0 or not args.isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            point_id = int(args)
            point = database.get.point(point_id=point_id)
            if point is not None and database.update.host(message.chat.id, point_id=point_id):
                bot_logger.info(f"Host: tg_id: {message.chat.id}, point_id: {point_id}")
                bot.send_message(message.chat.id, f"Теперь вы КПшник на КПшке {point.name} ({point_id})")
            else:
                bot.send_message(message.chat.id, "Проверьте правильность введённых данных")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            for admin_id in config.admin_ids:
                antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["remove_host"], state=MyStates.host)
def remove_host_handler(message: Message):
    with bot.retrieve_data(message.chat.id) as data:
        current_team_id = data.get("current_team_id")
    if current_team_id is not None:
        bot.send_message(message.chat.id, "Вы не можете покинуть КПшку, пока на ней есть команда")
    else:
        try:
            if database.update.host(message.chat.id, remove=True):
                bot_logger.info(f"Host: tg_id: {message.chat.id}, removed from point")
                bot.send_message(message.chat.id, f"Теперь вы можете стать КПшником на другой КПшке")
            else:
                bot.send_message(message.chat.id, "Проверьте правильность введённых данных")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            for admin_id in config.admin_ids:
                antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["reg_team"], state=[MyStates.host, MyStates.admin])
def reg_team_handler(message: Message):
    team_name = extract_arguments(message.text)
    if len(team_name) == 0:
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            team_id = database.add.user(Role.player, team_name.lower())
            if team_id:
                bot_logger.info(f"New team by admins: name: {team_name}, team_id: {team_id}")
                bot.send_message(message.chat.id, f"Ваш номер счёта: {team_id}")
            else:
                bot.send_message(message.chat.id, "Такая команда уже существует, попробуйте другое название")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            for admin_id in config.admin_ids:
                antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["queue_team"], state=[MyStates.host, MyStates.admin])
def queue_team_handler(message: Message):
    args = extract_arguments(message.text).split(" to ")
    if len(args) != 2 or not args[0].isdigit() or not args[1].isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            user_id = int(args[0])
            point_id = int(args[1])
            user = database.get.user(user_id=user_id)
            point = database.get.point(point_id=point_id)
            if user is not None and point is not None and database.add.queue(point_id, datetime.now(), user_id=user_id):
                bot_logger.info(f"Queue by admins: team_id: {user_id}, point_id: {point_id}")
                bot.send_message(message.chat.id, f"Команда {user.name} ({user.id}) успешно поставлена в очередь "
                                                  f"на КПшку {point.name} ({point.id})")
            else:
                bot.send_message(message.chat.id, "Проверьте правильность введённых данных и нет ли у команды очереди")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            for admin_id in config.admin_ids:
                antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["remove_team_queue"], state=[MyStates.host, MyStates.admin])
def remove_team_queue_handler(message: Message):
    args = extract_arguments(message.text)
    if len(args) == 0 or not args.isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            user_id = int(args)
            user = database.get.user(user_id=user_id)
            if user is not None and database.remove.queue(user_id=user_id):
                bot_logger.info(f"Remove queue by admins: team_id: {user_id}")
                bot.send_message(message.chat.id, f"Команда {user.name} ({user.id}) успешно удалена из очереди")
            else:
                bot.send_message(message.chat.id, "Проверьте правильность введённых данных")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            for admin_id in config.admin_ids:
                antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["transfer_from_team"], state=[MyStates.host, MyStates.admin])
def transfer_from_team_handler(message: Message):
    args = extract_arguments(message.text).split(" to ")
    args1 = args[0].split()
    if len(args1) != 2 or not args1[0].isdigit() or not args1[1].isdigit() or len(args) != 2 or not args[1].isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            from_user_id = int(args1[0])
            amount = int(args1[1])
            recipient = int(args[1])
            from_user = database.get.user(user_id=from_user_id)
            to_user = database.get.user(user_id=recipient)
            if database.update.transfer(recipient, amount, from_user_id=from_user_id):
                bot_logger.info(f"Transfer by admins: from_team_id: {from_user_id}, amount: {amount}, to: {recipient}")
                bot.send_message(message.chat.id, f"Перевод выполнен успешно! "
                                                  f"Переведено {amount} от команды {from_user.name} ({from_user.id}) "
                                                  f"команде {to_user.name} ({to_user.id})")
            else:
                bot.send_message(message.chat.id, "Проверьте правильность введённых данных")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            for admin_id in config.admin_ids:
                antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["start_team"], state=MyStates.host)
def start_team_handler(message: Message):
    try:
        user = database.get.point_next_team(message.chat.id)
        if user is not None:
            bot.add_data(message.chat.id, current_team_id=user.id, current_team_tg_id=user.tg_id)
            if user.tg_id is not None:
                bot.add_data(user.tg_id, active=True)
            bot_logger.info(f"Start team: team_id: {user.id}, host_tg_id: {message.chat.id}")
            bot.send_message(message.chat.id, f"Работа с командой {user.name} ({user.id}) успешно начата")
        else:
            bot.send_message(message.chat.id, "На вашу КПшку нет команд в очереди")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        for admin_id in config.admin_ids:
            antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["payment", "payment_nal"], state=MyStates.host)
def payment_handler(message: Message):
    with bot.retrieve_data(message.chat.id) as data:
        current_team_id = data.get("current_team_id")
    if current_team_id is None:
        bot.send_message(message.chat.id, "Нет активной команды")
    else:
        args = extract_arguments(message.text)
        if len(args) == 0 or not args.isdigit():
            bot.send_message(message.chat.id, "Неверный формат")
        else:
            try:
                amount = int(args)
                user = database.get.user(user_id=current_team_id)
                if user is not None and database.update.payment(message.chat.id, current_team_id, amount,
                                                                cash=extract_command(message.text) == "payment_nal"):
                    bot_logger.info(
                        f"Payment: host_tg_id: {message.chat.id}, team_id: {current_team_id}, amount: {amount}")
                    bot.send_message(message.chat.id, f"Оплата произведена успешно, "
                                                      f"списано {amount} со счёта команды {user.name} ({user.id})")
                else:
                    bot.send_message(message.chat.id, "Проверьте правильность введённых данных")
            except ConnectionError as e:
                bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
                for admin_id in config.admin_ids:
                    antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["pay", "pay_nal"], state=MyStates.host)
def pay_handler(message: Message):
    with bot.retrieve_data(message.chat.id) as data:
        current_team_id = data.get("current_team_id")
    if current_team_id is None:
        bot.send_message(message.chat.id, "Нет активной команды")
    else:
        args = extract_arguments(message.text)
        if len(args) == 0 or not args.isdigit():
            bot.send_message(message.chat.id, "Неверный формат")
        else:
            try:
                amount = int(args)
                user = database.get.user(user_id=current_team_id)
                if user is not None and database.update.pay(message.chat.id, current_team_id, amount,
                                                            cash=extract_command(message.text) == "pay_nal"):
                    bot_logger.info(f"Pay: host_tg_id: {message.chat.id}, team_id: {current_team_id}, amount: {amount}")
                    bot.send_message(message.chat.id, f"Выплата произведена успешно, "
                                                      f"зачислено {amount} на счёт команды {user.name} ({user.id})")
                else:
                    bot.send_message(message.chat.id, "Проверьте правильность введённых данных")
            except ConnectionError as e:
                bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
                for admin_id in config.admin_ids:
                    antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["stop_team"], state=MyStates.host)
def stop_team_handler(message: Message):
    with bot.retrieve_data(message.chat.id) as data:
        current_team_id = data.get("current_team_id")
        current_team_tg_id = data.get("current_team_tg_id")
    if current_team_id is None:
        bot.send_message(message.chat.id, "Нет активной команды")
    if current_team_tg_id is not None:
        bot.add_data(current_team_tg_id, active=False)
    else:
        try:
            if database.remove.queue(user_id=current_team_id):
                bot.add_data(message.chat.id, current_team_id=None, current_team_tg_id=None)
                bot_logger.info(f"Stop team: team_id: {current_team_id}, host_tg_id: {message.chat.id}")
                bot.send_message(message.chat.id, "Работа с командой успешно завершена")
            else:
                bot.send_message(message.chat.id, "Не удалось удалить очередь активной команды")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            for admin_id in config.admin_ids:
                antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["kp_pause"], state=MyStates.host)
def pause_kp_handler(message: Message):
    try:
        if database.update.pause(message.chat.id):
            bot_logger.info(f"Pause kp: host_tg_id: {message.chat.id}")
            bot.send_message(message.chat.id, "КП успешно приостановлена")
        else:
            bot.send_message(message.chat.id, "КП не активна")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        for admin_id in config.admin_ids:
            antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["kp_resume"], state=MyStates.host)
def resume_kp_handler(message: Message):
    try:
        if database.update.resume(message.chat.id):
            bot_logger.info(f"Resume kp: host_tg_id: {message.chat.id}")
            bot.send_message(message.chat.id, "КП успешно возобновлена")
        else:
            bot.send_message(message.chat.id, "КП не приостановлена")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        for admin_id in config.admin_ids:
            antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["kp_balance"], state=[MyStates.host, MyStates.admin])
def kp_balance_handler(message: Message):
    args = extract_arguments(message.text)
    if len(args) == 0 or not args.isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            point_id = int(args)
            balance = database.get.point_balance(point_id)
            if balance is not None:
                bot.send_message(message.chat.id, f"Баланс КП: {balance}")
            else:
                bot.send_message(message.chat.id, "Не удалось получить баланс КП")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            for admin_id in config.admin_ids:
                antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["reg_admin"], state=[None])
def reg_admin_handler(message: Message):
    with bot.retrieve_data(bot.user.id) as data:
        failed_admins = data.get("failed_admins", [])
    if message.from_user.id in failed_admins:
        bot.send_message(message.chat.id, "Вы уже пытались зарегистрироваться админом")
    else:
        bot.set_state(message.chat.id, MyStates.admin_password)
        bot.add_data(message.chat.id, retries=2)
        bot.send_message(message.chat.id, "Введите пароль для админов, у вас три попытки")


@bot.message_handler(state=MyStates.admin_password)
def admin_password_handler(message: Message):
    with bot.retrieve_data(message.chat.id) as data:
        retries = data.get("retries", 2)
    bot.delete_state(message.chat.id)
    with bot.retrieve_data(bot.user.id) as data:
        admin_password = data.get("admin_password")
    if message.text == admin_password:
        bot.set_state(message.chat.id, MyStates.admin_name)
        bot.send_message(message.chat.id, "Введи своё имя")
    else:
        if retries == 0:
            with bot.retrieve_data(bot.user.id) as data:
                failed_admins = data.get("failed_admins", [])
            failed_admins.append(message.from_user.id)
            bot.add_data(bot.user.id, failed_admins=failed_admins)
            bot.send_message(message.chat.id, "Неверный  пароль, попытки кончились")
        else:
            bot.set_state(message.chat.id, MyStates.admin_password)
            bot.add_data(message.chat.id, retries=retries - 1)
            bot.send_message(message.chat.id, f"Неверный пароль, осталось попыток: {retries}")


@bot.message_handler(state=MyStates.admin_name)
def admin_name_handler(message: Message):
    bot.delete_state(message.chat.id)
    try:
        if database.add.user(Role.admin, message.text, message.chat.id):
            bot.set_state(message.chat.id, MyStates.admin)
            bot_logger.info(f"New admin: tg_id: {message.chat.id}")
            bot.send_message(message.chat.id, "Вы успешно зарегистрированы как админ")
        else:
            bot.set_state(message.chat.id, MyStates.admin_name)
            bot.send_message(message.chat.id, "Админ с таким именем уже есть, попробуйте другое имя")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        for admin_id in config.admin_ids:
            antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["reg_kp"], state=MyStates.admin)
def reg_kp_handler(message: Message):
    bot.set_state(message.chat.id, MyStates.kp_one_time)
    bot.send_message(message.chat.id, "Команда может пройти КП один раз? (да/нет)")


@bot.message_handler(func=lambda msg: msg.text in ["да", "нет"], state=MyStates.kp_one_time)
def kp_one_time_handler(message: Message):
    bot.set_state(message.chat.id, MyStates.kp_name)
    bot.add_data(message.chat.id, kp_one_time=message.text == "да")
    bot.send_message(message.chat.id, "Введите название КП")


@bot.message_handler(state=MyStates.kp_name)
def kp_name_handler(message: Message):
    with bot.retrieve_data(message.chat.id) as data:
        kp_one_time = data.get("kp_one_time")
    try:
        point_id = database.add.point(message.text, kp_one_time)
        if point_id:
            bot.set_state(message.chat.id, MyStates.admin)
            bot_logger.info(f"New point: name: {message.text}, one_time: {kp_one_time}, point_id: {point_id}")
            bot.send_message(message.chat.id, f"КП успешно зарегистрирована, point_id: {point_id}")
        else:
            bot.send_message(message.chat.id, "КП с таким названием уже есть, попробуйте другое название")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        for admin_id in config.admin_ids:
            antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["total_money"], state=MyStates.admin)
def total_money_handler(message: Message):
    try:
        points_total, teams_total = database.get.total_money()
        bot.send_message(message.chat.id, f"Налички на КПшках и в магазине: {points_total}\n"
                                          f"Денег на счету у команд: {teams_total}\n"
                                          f"Всего: {points_total + teams_total}")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        for admin_id in config.admin_ids:
            antiflood(bot.send_message, admin_id, e.args[0])


@bot.message_handler(commands=["host_password"], chat_id=config.admin_ids)
def host_password_handler(message: Message):
    password = extract_arguments(message.text).strip()
    bot.add_data(bot.user.id, host_password=password)
    bot_logger.info(f"Пароль для хостов успешно установлен, \"{password}\"")
    bot.send_message(message.chat.id, f"Пароль для хостов успешно установлен, \"{password}\"")


@bot.message_handler(commands=["admin_password"], chat_id=config.admin_ids)
def admin_password_handler(message: Message):
    password = extract_arguments(message.text).strip()
    bot.add_data(bot.user.id, admin_password=password)
    bot_logger.info(f"Пароль для админов успешно установлен, \"{password}\"")
    bot.send_message(message.chat.id, f"Пароль для админов успешно установлен, \"{password}\"")


database.create_all()

bot.add_custom_filter(ChatFilter())
bot.add_custom_filter(StateFilter(bot))
bot.set_state(bot.user.id, MyStates.bot)
bot.infinity_polling()

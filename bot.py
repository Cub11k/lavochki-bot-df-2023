import telebot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.custom_filters import StateFilter, ChatFilter
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateRedisStorage
from telebot.util import extract_arguments, extract_command, antiflood, smart_split

from sqlalchemy.exc import SQLAlchemyError

import config
from logger import bot_logger
import database
from database import Role

storage = StateRedisStorage(host=config.redis_host, port=config.redis_port, password=config.redis_password)
bot = telebot.TeleBot(token=config.token, state_storage=storage)


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


def notify_admins(message: Message, exception: SQLAlchemyError):
    bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
    for admin_id in config.admin_ids:
        antiflood(bot.send_message, admin_id, exception.args[0])


@bot.message_handler(commands=["start"], state=[None])
def start_handler(message: Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("Да", callback_data="reg_yes"),
                 InlineKeyboardButton("Нет", callback_data="reg_no"))
    bot.set_state(message.chat.id, MyStates.reg_buttons)
    bot.send_message(message.chat.id, "Привет! Хотите зарегистрироваться как участник / команда?",
                     reply_markup=keyboard)


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
        "Список команд для всех:\n\n"
        "/start - начать работу с ботом\n"
        "/cancel - отменить текущее действие (регистрацию)\n"
        "/reg - зарегистрировать команду\n"
        "/reg_host - зарегистрировать КПшника\n"
        "/reg_admin - зарегистрировать админа\n"
        "/help - список команд\n\n"
    )
    if state == MyStates.team.name:
        msg += (
            "Список команд для участников:\n\n"
            "/balance - баланс команды\n"
            "/transfer <amount> to <recipient> - перевести деньги другой команде\n"
            "/queue_to <kp_id> - занять очередь на КПшку\n"
            "/place - место в очереди\n"
            "/remove_queue - отменить свою очередь\n"
            "/stop - закончить участие\n\n"
        )
    if state in [MyStates.team.name, MyStates.host.name, MyStates.admin.name]:
        msg += (
            "Список команд для участников, КПшников и админов:\n\n"
            "/my_id - узнать свой id\n"
            "/list_free - список свободных КПшек\n"
            "/list_all - список всех КПшек\n\n"
        )
    if state == MyStates.host.name:
        msg += (
            "Список команд для КПшников:\n\n"
            "/add_host_to <kp_id> - стать КПшником на выбранной точке\n"
            "/remove_host - перестать быть КПшником на выбранной точке\n"
            "/start_team - начать работу с командой\n"
            "/payment <amount> - оплата товара в магазине (деньги снимутся со счёта текущей команды)\n"
            "/payment_nal <amount> - оплата товара в магазине наличкой (деньги снимутся со счёта текущей команды)\n"
            "/pay <amount> - выплата за прохождение КПшки (деньги начислятся на счёт текущей команды)\n"
            "/pay_nal <amount> - выплата за прохождение КПшки наличкой (деньги начислятся на счёт текущей команды)\n"
            "/stop_team - закончить работу с командой\n"
            "/skip_team - пропустить команду (подвинуть на одно место в очереди назад)\n"
            "/kp_pause - приостановить работу КПшки\n"
            "/kp_resume - возобновить работу КПшки\n\n"
        )
    if state in [MyStates.host.name, MyStates.admin.name]:
        msg += (
            "Список команд для КПшников и админов:\n\n"
            "/reg_team <team_name> - зарегистрировать команду\n"
            "/balance_team <team_id> - узнать баланс команды\n"
            "/place_team <team_id> - узнать место команды в очереди\n"
            "/id_team <team_name> - узнать id команды\n"
            "/queue_team <team_id> to <kp_id> - занять очередь на КПшку для выбранной команды\n"
            "/remove_queue_team <team_id> - отменить очередь для выбранной команды\n"
            "/transfer_from_team <team_id> <amount> to <recipient> - перевести деньги другой команде\n"
            "/kp_id <kp_name> - узнать id КПшки\n"
            "/kp_balance <kp_id> - баланс КПшки (наличка)\n"
            "/kp_queue <kp_id> - очередь на КПшку\n"
            "/total_money - общее количество денег\n\n"
        )
    if state == MyStates.admin.name:
        msg += (
            "Список команд для админов:\n\n"
            "/reg_kp - зарегистрировать КПшку\n"
            "/kp_balance_all - баланс всех КПшек по возрастанию (наличка)\n"
            "/add_cash <amount> to <kp_id> - добавить наличку на КПшку\n"
            "/all_teams - список всех команд\n"
            "/all_hosts - список всех КПшников\n"
            "/all_admins - список всех админов\n\n"
        )
    if message.chat.id in config.admin_ids:
        msg += (
            "Список команд для главных админов:\n\n"
            "/new_host_password <password> - установить пароль для КПшников\n"
            "/new_admin_password <password> - установить пароль для админов\n"
            "/remove_user <user_id> - удалить пользователя\n"
            "/remove_kp <kp_id> - удалить КПшку\n"
            "/remove_blacklist <team_id> <kp_id> - удалить команду из черного списка КПшки\n\n"
        )
    bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=["cancel"], state=[MyStates.team_name, MyStates.host_password, MyStates.host_name,
                                                 MyStates.admin_password, MyStates.admin_name,
                                                 MyStates.kp_one_time, MyStates.kp_name])
def cancel_handler(message: Message):
    bot.delete_state(message.chat.id)
    bot.send_message(message.chat.id, "Отменено")


@bot.message_handler(commands=["reg"], state=[None])
def reg_handler(message: Message):
    bot.set_state(message.chat.id, MyStates.team_name)
    bot.send_message(message.chat.id, "Введите название вашей команды / участника")


@bot.message_handler(state=MyStates.team_name)
def team_name_handler(message: Message):
    if extract_command(message.text) is not None:
        bot.send_message(message.chat.id, "Название команды не может начинаться с /")
    else:
        bot.delete_state(message.chat.id)
        try:
            team_id = database.add.user(Role.player, message.text.lower(), message.chat.id)
            if team_id:
                bot.set_state(message.chat.id, MyStates.team)
                bot_logger.info(f"New team: {message.text.lower()} (tg_id: {message.chat.id}, team_id: {team_id})")
                bot.send_message(message.chat.id, f"Ваш номер команды: {team_id}")
                bot.send_message(config.channel_id, f"Новая команда: {message.text.lower()} "
                                                    f"(tg_id: {message.chat.id}, team_id: {team_id})")
            else:
                bot.set_state(message.chat.id, MyStates.team_name)
                bot.send_message(message.chat.id, "Такая команда уже существует, попробуйте другое название")
        except SQLAlchemyError as e:
            bot.set_state(message.chat.id, MyStates.team_name)
            notify_admins(message, e)


@bot.message_handler(commands=["balance"], state=MyStates.team)
def balance_handler(message: Message):
    try:
        balance = database.get.user_balance(message.chat.id)
        if balance is not None:
            bot.send_message(message.chat.id, f"Ваш баланс - {balance}")
        else:
            bot.send_message(message.chat.id, "Не удалось получить данные о балансе")
    except SQLAlchemyError as e:
        notify_admins(message, e)


@bot.message_handler(commands=["transfer"], state=MyStates.team)
def transfer_handler(message: Message):
    args = extract_arguments(message.text).split(" to ")
    if len(args) != 2 or not args[0].isdigit() or not args[1].isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        amount = int(args[0])
        recipient = int(args[1])
        try:
            from_user = database.get.user(tg_id=message.chat.id)
            user = database.get.user(user_id=recipient)
            if user is not None and database.update.transfer(recipient, amount, from_user_tg_id=message.chat.id):
                bot_logger.info(f"Transfer: {amount} from tg_id: {message.chat.id} to team_id: {recipient}")
                bot.send_message(message.chat.id, f"Перевод выполнен! "
                                                  f"Переведено {amount} команде {user.name} ({user.id})")
                bot.send_message(config.channel_id, f"Команда {from_user.name} ({from_user.id}) перевела {amount} "
                                                    f"команде {user.name} ({user.id})")
            else:
                bot.send_message(message.chat.id, "Не удалось выполнить перевод")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["queue_to"], state=MyStates.team)
def queue_to_handler(message: Message):
    args = extract_arguments(message.text)
    if len(args) == 0 or not args.isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        point_id = int(args)
        try:
            user = database.get.user(tg_id=message.chat.id)
            point = database.get.point(point_id=point_id)
            is_free = database.get.point_is_free(point_id=point_id)
            if point is not None and database.add.queue(point_id, tg_id=message.chat.id):
                bot_logger.info(f"Queue: tg_id: {message.chat.id} to point_id: {point_id}")
                bot.send_message(message.chat.id, f"Теперь вы в очереди на КПшку {point.name}!")
                if is_free:
                    bot.send_message(point.host_tg_id, f"Команда {user.name} встала в очередь на вашу КПшку!")
                bot.send_message(config.channel_id, f"Команда {user.name} встала в очередь на КПшку {point.name}!")
            else:
                bot.send_message(message.chat.id, "Не удалось встать в очередь")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["place"], state=MyStates.team)
def place_handler(message: Message):
    try:
        place = database.get.user_queue_place(tg_id=message.chat.id)
        if place is None:
            bot.send_message(message.chat.id, "У вас нет активной очереди")
        else:
            bot.send_message(message.chat.id, f"Ваше место в очереди - {place}")
    except SQLAlchemyError as e:
        notify_admins(message, e)


@bot.message_handler(commands=["remove_queue"], state=MyStates.team)
def remove_queue_handler(message: Message):
    with bot.retrieve_data(message.chat.id) as data:
        active = data.get("active", False)
    if active:
        bot.send_message(message.chat.id, "Вы не можете отменить очередь, пока находитесь на КПшке")
    else:
        try:
            user = database.get.user(tg_id=message.chat.id)
            if database.remove.queue(tg_id=message.chat.id):
                bot_logger.info(f"Remove queue: tg_id: {message.chat.id}")
                bot.send_message(message.chat.id, "Очередь отменена!")
                bot.send_message(config.channel_id, f"Команда {user.name} ({user.id}) отменила очередь!")
            else:
                bot.send_message(message.chat.id, "Не удалось отменить очередь")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["stop"], state=MyStates.team)
def stop_handler(message: Message):
    bot_logger.info(f"Stop: tg_id: {message.chat.id}")
    bot.send_message(message.chat.id, "Спасибо за участие!")
    try:
        user = database.get.user(tg_id=message.chat.id)
        if user is not None:
            bot.send_message(config.channel_id, f"Команда {user.name} ({user.id}) закончила участие")
        database.remove.queue(tg_id=message.chat.id)
    except SQLAlchemyError as e:
        notify_admins(message, e)


@bot.message_handler(commands=["my_id"], state=[MyStates.team, MyStates.host, MyStates.admin])
def my_id_handler(message: Message):
    try:
        user = database.get.user(tg_id=message.chat.id)
        if user is not None:
            bot.send_message(message.chat.id, f"Ваш ID: {user.id}")
        else:
            bot.send_message(message.chat.id, "Не удалось получить ID")
    except SQLAlchemyError as e:
        notify_admins(message, e)


@bot.message_handler(commands=["list_free"], state=[MyStates.team, MyStates.host, MyStates.admin])
def list_free_handler(message: Message):
    try:
        points = database.get.free_points(message.chat.id)
        if len(points) > 0:
            list_msg = f"Свободные КПшки:\n"
            list_msg += "\n".join(f"{point[0]} - {point[1]}" for point in points)
            msgs = smart_split(list_msg)
            for msg in msgs:
                antiflood(bot.send_message, message.chat.id, msg)
        else:
            bot.send_message(message.chat.id, "Свободных КПшек нет")
    except SQLAlchemyError as e:
        notify_admins(message, e)


@bot.message_handler(commands=["list_all"], state=[MyStates.team, MyStates.host, MyStates.admin])
def list_all_handler(message: Message):
    try:
        points = database.get.all_points()
        if len(points) > 0:
            list_msg = "\n".join(f"{point[0]} ({point[1]})" for point in points)
            msgs = smart_split(list_msg)
            for msg in msgs:
                antiflood(bot.send_message, message.chat.id, msg)
        else:
            bot.send_message(message.chat.id, "КПшек нет")
    except SQLAlchemyError as e:
        notify_admins(message, e)


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
    if extract_command(message.text) is not None:
        bot.send_message(message.chat.id, "Имя не может начинаться с /")
    else:
        bot.delete_state(message.chat.id)
        try:
            if database.add.user(Role.host, message.text.lower(), message.chat.id):
                bot.set_state(message.chat.id, MyStates.host)
                bot_logger.info(f"Host: tg_id: {message.chat.id}, name: {message.text.lower()}")
                bot.send_message(message.chat.id, "Вы успешно зарегистрированы как КПшник")
                bot.send_message(config.channel_id,
                                 f"КПшник {message.text.lower()}, tg_id: {message.chat.id}, зарегистрировался")
            else:
                bot.set_state(message.chat.id, MyStates.host_name)
                bot.send_message(message.chat.id, "КПшник с таким именем уже есть, попробуйте другое имя")
        except SQLAlchemyError as e:
            bot.set_state(message.chat.id, MyStates.host_name)
            notify_admins(message, e)


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
                bot.send_message(config.channel_id, f"КПшник, tg_id: {message.chat.id}, "
                                                    f"перешёл на КПшку {point.name} ({point_id})")
            else:
                bot.send_message(message.chat.id, "Не удалось перейти на КПшку")
        except SQLAlchemyError as e:
            notify_admins(message, e)


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
                bot.send_message(config.channel_id, f"КПшник, tg_id: {message.chat.id}, покинул КПшку")
            else:
                bot.send_message(message.chat.id, "Не удалось покинуть КПшку")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["start_team"], state=MyStates.host)
def start_team_handler(message: Message):
    try:
        user = database.get.point_next_team(message.chat.id)
        point = database.get.point(host_tg_id=message.chat.id)
        if user is not None and point is not None:
            bot.add_data(message.chat.id, current_team_id=user.id, current_team_tg_id=user.tg_id)
            if user.tg_id is not None:
                bot.add_data(user.tg_id, active=True)
            bot_logger.info(f"Start team: team_id: {user.id}, point_id: {point.id}")
            bot.send_message(message.chat.id, f"Работа с командой {user.name} ({user.id}) успешно начата")
            bot.send_message(config.channel_id, f"Начата работа с командой {user.name} ({user.id}) "
                                                f"на КПшке {point.name} ({point.id})")
        else:
            bot.send_message(message.chat.id, "На вашу КПшку нет команд в очереди")
    except SQLAlchemyError as e:
        notify_admins(message, e)


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
                cash = extract_command(message.text) == "payment_nal"
                user = database.get.user(user_id=current_team_id)
                if user is not None and database.update.payment(message.chat.id, current_team_id, amount,
                                                                cash=cash):
                    bot_logger.info(
                        f"Payment: host_tg_id: {message.chat.id}, team_id: {current_team_id}, amount: {amount}")
                    bot.send_message(message.chat.id, f"Оплата произведена успешно, "
                                                      f"списано {amount} со счёта команды {user.name} ({user.id})")
                    bot.send_message(config.channel_id, f"Списано {amount} со счёта команды {user.name} ({user.id}), "
                                                        f"{'наличка' if cash else 'крипта'}")
                else:
                    bot.send_message(message.chat.id, "Не удалось выполнить оплату")
            except SQLAlchemyError as e:
                notify_admins(message, e)


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
                cash = extract_command(message.text) == "pay_nal"
                user = database.get.user(user_id=current_team_id)
                if user is not None and database.update.pay(message.chat.id, current_team_id, amount,
                                                            cash=cash):
                    bot_logger.info(f"Pay: host_tg_id: {message.chat.id}, team_id: {current_team_id}, amount: {amount}")
                    bot.send_message(message.chat.id, f"Выплата произведена успешно, "
                                                      f"зачислено {amount} на счёт команды {user.name} ({user.id})")
                    bot.send_message(config.channel_id, f"Зачислено {amount} на счёт команды {user.name} ({user.id}), "
                                                        f"{'наличка' if cash else 'крипта'}")
                else:
                    bot.send_message(message.chat.id, "Не удалось выполнить выплату")
            except SQLAlchemyError as e:
                notify_admins(message, e)


@bot.message_handler(commands=["stop_team"], state=MyStates.host)
def stop_team_handler(message: Message):
    with bot.retrieve_data(message.chat.id) as data:
        current_team_id = data.get("current_team_id")
        current_team_tg_id = data.get("current_team_tg_id")
    if current_team_id is None:
        bot.send_message(message.chat.id, "Нет активной команды")
    else:
        if current_team_tg_id is not None:
            bot.add_data(current_team_tg_id, active=False)
        try:
            user = database.get.user(user_id=current_team_id)
            if user is not None and database.remove.queue(user_id=current_team_id):
                bot.add_data(message.chat.id, current_team_id=None, current_team_tg_id=None)
                bot_logger.info(f"Stop team: team_id: {current_team_id}, host_tg_id: {message.chat.id}")
                bot.send_message(message.chat.id, "Работа с командой успешно завершена")
                bot.send_message(config.channel_id, f"Работа с командой {user.name} ({user.id}) завершена")
            else:
                bot.send_message(message.chat.id, "Не удалось завершить работу с командой")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["skip_team"], state=MyStates.host)
def skip_team_handler(message: Message):
    try:
        if database.update.skip_team(message.chat.id):
            bot_logger.info(f"Skip team: host_tg_id: {message.chat.id}")
            bot.send_message(message.chat.id, "Команда успешно пропущена")
            bot.send_message(config.channel_id, f"КПшник {message.chat.id} пропустил команду")
        else:
            bot.send_message(message.chat.id, "Не удалось пропустить команду")
    except SQLAlchemyError as e:
        notify_admins(message, e)


@bot.message_handler(commands=["kp_pause"], state=MyStates.host)
def kp_pause_handler(message: Message):
    try:
        point = database.get.point(host_tg_id=message.chat.id)
        if database.update.pause(message.chat.id):
            bot_logger.info(f"Pause kp: host_tg_id: {message.chat.id}")
            bot.send_message(message.chat.id, "КПшка успешно приостановлена")
            bot.send_message(config.channel_id, f"КПшка {point.name} ({point.id}) приостановлена")
        else:
            bot.send_message(message.chat.id, "КПшка не активна")
    except SQLAlchemyError as e:
        notify_admins(message, e)


@bot.message_handler(commands=["kp_resume"], state=MyStates.host)
def kp_resume_handler(message: Message):
    try:
        point = database.get.point(host_tg_id=message.chat.id)
        if database.update.resume(message.chat.id):
            bot_logger.info(f"Resume kp: host_tg_id: {message.chat.id}")
            bot.send_message(message.chat.id, "КПшка успешно возобновлена")
            bot.send_message(config.channel_id, f"КПшка {point.name} ({point.id}) возобновлена")
        else:
            bot.send_message(message.chat.id, "КПшка не приостановлена")
    except SQLAlchemyError as e:
        notify_admins(message, e)


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
                bot.send_message(message.chat.id, f"Ваш номер команды: {team_id}")
                bot.send_message(config.channel_id, f"Команда {team_name}, team_id: {team_id}, зарегистрирована")
            else:
                bot.send_message(message.chat.id, "Такая команда уже существует, попробуйте другое название")
        except SQLAlchemyError as e:
            notify_admins(message, e)


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
            is_free = database.get.point_is_free(point_id=point_id)
            if user is not None and point is not None and database.add.queue(point_id, user_id=user_id):
                bot_logger.info(f"Queue by admins: team_id: {user_id}, point_id: {point_id}")
                bot.send_message(message.chat.id, f"Команда {user.name} ({user.id}) успешно поставлена в очередь "
                                                  f"на КПшку {point.name} ({point.id})")
                if is_free:
                    bot.send_message(point.host_tg_id, f"Команда {user.name} поставлена в очередь на вашу КПшку!")
                bot.send_message(config.channel_id, f"Команда {user.name} ({user.id}) поставлена в очередь "
                                                    f"на КПшку {point.name} ({point.id})")
            else:
                bot.send_message(message.chat.id, "Не удалось поставить команду в очередь")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["remove_queue_team"], state=[MyStates.host, MyStates.admin])
def remove_queue_team_handler(message: Message):
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
                bot.send_message(config.channel_id, f"Команда {user.name} ({user.id}) удалена из очереди")
            else:
                bot.send_message(message.chat.id, "Не удалось удалить команду из очереди")
        except SQLAlchemyError as e:
            notify_admins(message, e)


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
                bot.send_message(config.channel_id, f"Переведено {amount} от команды {from_user.name} ({from_user.id}) "
                                                    f"команде {to_user.name} ({to_user.id})")
            else:
                bot.send_message(message.chat.id, "Не удалось выполнить перевод")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["balance_team"], state=[MyStates.host, MyStates.admin])
def balance_team_handler(message: Message):
    args = extract_arguments(message.text)
    if len(args) == 0 or not args.isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            user_id = int(args)
            user = database.get.user(user_id=user_id)
            if user is not None:
                bot.send_message(message.chat.id, f"Баланс команды {user.name} ({user.id}): {user.balance}")
            else:
                bot.send_message(message.chat.id, "Не удалось получить баланс команды")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["place_team"], state=[MyStates.host, MyStates.admin])
def balance_team_handler(message: Message):
    args = extract_arguments(message.text)
    if len(args) == 0 or not args.isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            user_id = int(args)
            user = database.get.user(user_id=user_id)
            if user is not None:
                place = database.get.user_queue_place(user_id=user_id)
                if place is not None:
                    bot.send_message(message.chat.id, f"Место команды {user.name} ({user.id}) в очереди: {place}")
                else:
                    bot.send_message(message.chat.id, f"Команда {user.name} ({user.id}) не в очереди")
            else:
                bot.send_message(message.chat.id, "Не удалось получить место команды")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["id_team"], state=[MyStates.host, MyStates.admin])
def id_team_handler(message: Message):
    args = extract_arguments(message.text).lower()
    if len(args) == 0:
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            user = database.get.user(name=args)
            if user is not None:
                bot.send_message(message.chat.id, f"ID команды {user.name}: {user.id}")
            else:
                bot.send_message(message.chat.id, "Не удалось получить ID команды")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["kp_id"], state=[MyStates.host, MyStates.admin])
def kp_id_handler(message: Message):
    args = extract_arguments(message.text).lower()
    if len(args) == 0:
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            point = database.get.point(name=args)
            if point is not None:
                bot.send_message(message.chat.id, f"ID КПшки {point.name}: {point.id}")
            else:
                bot.send_message(message.chat.id, "Не удалось получить ID КПшки")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["kp_balance"], state=[MyStates.host, MyStates.admin])
def kp_balance_handler(message: Message):
    args = extract_arguments(message.text)
    if len(args) == 0 or not args.isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            point_id = int(args)
            point = database.get.point(point_id=point_id)
            if point is not None:
                bot.send_message(message.chat.id, f"Баланс КПшки {point.name}: {point.balance}")
            else:
                bot.send_message(message.chat.id, "Не удалось получить баланс КПшки")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["kp_queue"], state=[MyStates.host, MyStates.admin])
def kp_queue_handler(message: Message):
    args = extract_arguments(message.text)
    if len(args) == 0 or not args.isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            point_id = int(args)
            point = database.get.point(point_id=point_id)
            if point is not None:
                queues = database.get.point_queues(point_id)
                if len(queues) > 0:
                    list_msg = f"Очередь на КПшку {point.name}:\n"
                    list_msg += "\n".join([f'{user[0]} ({user[1]})' for user in queues])
                    msgs = smart_split(list_msg)
                    for msg in msgs:
                        antiflood(bot.send_message, message.chat.id, msg)
                else:
                    bot.send_message(message.chat.id, f"Очередь на КПшку {point.name} пуста")
            else:
                bot.send_message(message.chat.id, "Не удалось получить очередь на КПшку")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["total_money"], state=[MyStates.host, MyStates.admin])
def total_money_handler(message: Message):
    try:
        points_total, teams_total = database.get.total_money()
        bot.send_message(message.chat.id, f"Налички на КПшках и в магазине: {points_total}\n"
                                          f"Денег на счету у команд: {teams_total}\n"
                                          f"Всего: {points_total + teams_total}")
    except SQLAlchemyError as e:
        notify_admins(message, e)


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
    if extract_command(message.text) is not None:
        bot.send_message(message.chat.id, "Имя не может начинаться с /")
    else:
        bot.delete_state(message.chat.id)
        try:
            admin_id = database.add.user(Role.admin, message.text.lower(), message.chat.id, 10000000)
            if admin_id:
                bot.set_state(message.chat.id, MyStates.admin)
                bot_logger.info(f"New admin: {message.text.lower()}, tg_id: {message.chat.id}, user_id: {admin_id}")
                bot.send_message(message.chat.id, f"Вы успешно зарегистрированы как админ, ваш id: {admin_id}")
                bot.send_message(config.channel_id, f"Новый админ: {message.text.lower()} (tg_id: {message.chat.id})")
            else:
                bot.set_state(message.chat.id, MyStates.admin_name)
                bot.send_message(message.chat.id, "Админ с таким именем уже есть, попробуйте другое имя")
        except SQLAlchemyError as e:
            bot.set_state(message.chat.id, MyStates.admin_name)
            notify_admins(message, e)


@bot.message_handler(commands=["kp_balance_all"], state=MyStates.admin)
def kp_balance_all_handler(message: Message):
    try:
        points = database.get.all_points()
        if len(points) > 0:
            list_msg = "\n".join([f"{point[0]} ({point[1]}): {point[2]}" for point in points])
            msgs = smart_split(list_msg)
            for msg in msgs:
                antiflood(bot.send_message, message.chat.id, msg)
        else:
            bot.send_message(message.chat.id, "Нет КПшек")
    except SQLAlchemyError as e:
        notify_admins(message, e)


@bot.message_handler(commands=["add_cash"], state=MyStates.admin)
def add_cash_handler(message: Message):
    args = extract_arguments(message.text).split(" to ")
    if len(args) != 2 or not args[0].isdigit() or not args[1].isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            amount = int(args[0])
            point_id = int(args[1])
            point = database.get.point(point_id=point_id)
            if database.update.add_cash(amount, point_id):
                bot.send_message(message.chat.id, "Успешно")
                bot_logger.info(f"Admin {message.from_user.id} added {amount} to {point_id}")
                bot.send_message(config.channel_id, f"Админ {message.from_user.id} добавил {amount} кэша "
                                                    f"на {point.name} ({point.id})")
            else:
                bot.send_message(message.chat.id, "Не удалось добавить кэш")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["all_teams", "all_hosts", "all_admins"], state=MyStates.admin)
def all_users_handler(message: Message):
    command = extract_command(message.text)
    role = Role.admin if command == "all_admins" else Role.host if command == "all_hosts" else Role.player
    try:
        users = database.get.all_users(role)
        if len(users) > 0:
            list_msg = f"Список пользователей, всего {len(users)}:\n"
            list_msg += "\n".join([f"{user.name} ({user.id}), баланс: {user.balance}" for user in users])
            msgs = smart_split(list_msg)
            for msg in msgs:
                antiflood(bot.send_message, message.chat.id, msg)
        else:
            bot.send_message(message.chat.id, "Пользователей нет")
    except SQLAlchemyError as e:
        notify_admins(message, e)


@bot.message_handler(commands=["reg_kp"], state=MyStates.admin)
def reg_kp_handler(message: Message):
    bot.set_state(message.chat.id, MyStates.kp_one_time)
    bot.send_message(message.chat.id, "Команда может пройти КПшку только один раз? (да/нет)")


@bot.message_handler(func=lambda msg: msg.text in ["да", "нет"], state=MyStates.kp_one_time)
def kp_one_time_handler(message: Message):
    bot.set_state(message.chat.id, MyStates.kp_name)
    bot.add_data(message.chat.id, kp_one_time=message.text == "да")
    bot.send_message(message.chat.id, "Введите название КПшки")


@bot.message_handler(state=MyStates.kp_name)
def kp_name_handler(message: Message):
    if extract_command(message.text) is not None:
        bot.send_message(message.chat.id, "Название КПшки не может быть начинаться с /")
    else:
        with bot.retrieve_data(message.chat.id) as data:
            kp_one_time = data.get("kp_one_time")
        bot.delete_state(message.chat.id)
        name = message.text.lower()
        try:
            point_id = database.add.point(name, kp_one_time)
            if point_id:
                bot.set_state(message.chat.id, MyStates.admin)
                bot_logger.info(f"New point: name: {name}, one_time: {kp_one_time}, point_id: {point_id}")
                bot.send_message(message.chat.id, f"КПшка успешно зарегистрирована, point_id: {point_id}")
                bot.send_message(config.channel_id, f"Новая КП: {name} (point_id: {point_id})")
            else:
                bot.set_state(message.chat.id, MyStates.kp_name)
                bot.send_message(message.chat.id, "КПшка с таким названием уже есть, попробуйте другое название")
        except SQLAlchemyError as e:
            bot.set_state(message.chat.id, MyStates.kp_name)
            notify_admins(message, e)


@bot.message_handler(commands=["new_host_password"], chat_id=config.admin_ids)
def new_host_password_handler(message: Message):
    password = extract_arguments(message.text).strip()
    bot.add_data(bot.user.id, host_password=password)
    bot_logger.info(f"Пароль для хостов успешно установлен, \"{password}\"")
    bot.send_message(message.chat.id, f"Пароль для хостов успешно установлен, \"{password}\"")


@bot.message_handler(commands=["new_admin_password"], chat_id=config.admin_ids)
def new_admin_password_handler(message: Message):
    password = extract_arguments(message.text).strip()
    bot.add_data(bot.user.id, admin_password=password)
    bot_logger.info(f"Пароль для админов успешно установлен, \"{password}\"")
    bot.send_message(message.chat.id, f"Пароль для админов успешно установлен, \"{password}\"")


@bot.message_handler(commands=["remove_user"], chat_id=config.admin_ids)
def remove_user_handler(message: Message):
    args = extract_arguments(message.text)
    if len(args) == 0 or not args.isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            user_id = int(args)
            if database.remove.all_user_blacklists(user_id) and database.remove.user(user_id):
                bot.send_message(message.chat.id, "Успешно")
                bot_logger.info(f"User {args} deleted")
                bot.send_message(config.channel_id, f"Админ {message.from_user.id} удалил пользователя {user_id}")
            else:
                bot.send_message(message.chat.id, "Не удалось удалить пользователя")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["remove_kp"], chat_id=config.admin_ids)
def remove_kp_handler(message: Message):
    args = extract_arguments(message.text)
    if len(args) == 0 or not args.isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            point_id = int(args)
            if database.remove.all_point_queues(point_id) and database.remove.all_point_blacklists(
                    point_id) and database.remove.point(point_id):
                bot.send_message(message.chat.id, "Успешно")
                bot_logger.info(f"Point {point_id} deleted")
                bot.send_message(config.channel_id, f"Админ {message.from_user.id} удалил КПшку {point_id}")
            else:
                bot.send_message(message.chat.id, "Не удалось удалить КПшку")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["remove_blacklist"], chat_id=config.admin_ids)
def remove_blacklist_handler(message: Message):
    args = extract_arguments(message.text).split()
    if len(args) != 2 or not args[0].isdigit() or not args[1].isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            user_id = int(args[0])
            point_id = int(args[1])
            if database.remove.blacklist(user_id, point_id):
                bot.send_message(message.chat.id, "Успешно")
                bot_logger.info(f"Blacklist ({user_id},{point_id}) deleted")
                bot.send_message(config.channel_id, f"Админ {message.from_user.id} удалил "
                                                    f"blacklist ({user_id},{point_id})")
            else:
                bot.send_message(message.chat.id, "Не удалось удалить blacklist")
        except SQLAlchemyError as e:
            notify_admins(message, e)


@bot.message_handler(commands=["create_all"], chat_id=config.admin_ids)
def create_all_handler(message: Message):
    database.create_all()
    bot.send_message(message.chat.id, "Успешно")


bot.add_custom_filter(ChatFilter())
bot.add_custom_filter(StateFilter(bot))

bot.set_state(bot.user.id, MyStates.bot)
bot.infinity_polling()

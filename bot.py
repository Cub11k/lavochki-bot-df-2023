from datetime import datetime

import telebot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from telebot.custom_filters import StateFilter
from telebot.handler_backends import State, StatesGroup
from telebot.util import extract_arguments, extract_command

import config
import database
from database import Role

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
    bot.send_message(message.chat.id, "<b>Команды бота:</b>\n", parse_mode='HTML')
    bot.send_message(message.chat.id, "\n /start - запуск бота;\n"
                                      "\n /reg - регистрация для участников;\n"
                                      "\n /balance - текущее количество вмкешей команды;\n"
                                      "\n /transfer <n> to <recipient_id> - перевести n вмкешей на счёт recipient_id;\n"
                                      "\n /queue_to <l> - занять очередь на кп l;\n"
                                      "\n /place - показывает место в очереди;\n"
                                      "\n /remove_queue - отменить свою очередь, если она была назначена на кп;\n"
                                      "\n /stop - остановка участия команды, при котором они больше не проходят кп;\n"
                                      "\n /list_free - команда показывает свободные кпшки\n")


@bot.message_handler(commands=["reg"], state=[None])
def reg_handler(message: Message):
    bot.set_state(message.chat.id, MyStates.team_name)
    bot.send_message(message.chat.id, "Введите название команды")


@bot.message_handler(state=MyStates.team_name)
def team_name_handler(message: Message):
    bot.delete_state(message.chat.id)
    try:
        if database.add.user(Role.player, message.text.lower(), message.chat.id):
            bot.set_state(message.chat.id, MyStates.team)
            bot.send_message(message.chat.id, "Ваш номер счёта: ")
        else:
            bot.set_state(message.chat.id, MyStates.team_name)
            bot.send_message(message.chat.id, "Такая команда уже существует, попробуйте другое название")
    except ConnectionError as e:
        bot.set_state(message.chat.id, MyStates.team_name)
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        bot.send_message(config.admin_id, e.args[0])


@bot.message_handler(commands=["balance"], state=MyStates.team)
def balance_handler(message: Message):
    try:
        balance = database.get.user_balance(message.chat.id)
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        bot.send_message(config.admin_id, e.args[0])
    else:
        if balance is not None:
            bot.send_message(message.chat.id, f"Ваш баланс - {balance}")
        else:
            bot.send_message(message.chat.id, "Не удалось получить данные о балансе")


@bot.message_handler(commands=["transfer"], state=MyStates.team)
def transfer_handler(message: Message):
    args = extract_arguments(message.text).split(" to ")
    if len(args) != 2 or not args[0].isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        amount = int(args[0])
        recipient = args[1]
        try:
            if database.update.transfer(recipient, amount, from_user_tg_id=message.chat.id):
                bot.send_message(message.chat.id, "Перевод выполнен!")
            else:
                bot.send_message(message.chat.id, "Не получилось, проверьте правильность введенных данных")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            bot.send_message(config.admin_id, e.args[0])


@bot.message_handler(commands=["queue_to"], state=MyStates.team)
def queue_to_handler(message: Message):
    args = extract_arguments(message.text).split(" ")
    if len(args) != 1 or not args[0].isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        point_id = int(args[0])
        try:
            if database.add.queue(point_id, datetime.now(), tg_id=message.chat.id):
                bot.send_message(message.chat.id, "Теперь вы в очереди!")
            else:
                bot.send_message(message.chat.id, "Не получилось, проверьте нет ли у вас активной очереди")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            bot.send_message(config.admin_id, e.args[0])


@bot.message_handler(commands=["place"], state=MyStates.team)
def place_handler(message: Message):
    try:
        place = database.get.user_queue_place(message.chat.id)
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        bot.send_message(config.admin_id, e.args[0])
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
                bot.send_message(message.chat.id, "Очередь отменена!")
            else:
                bot.send_message(message.chat.id, "Не получилось, проверьте есть ли у вас очередь")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            bot.send_message(config.admin_id, e.args[0])


@bot.message_handler(commands=["list_free"], state=MyStates.team)
def list_free_handler(message):
    try:
        points = database.get.free_points()
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        bot.send_message(config.admin_id, e.args[0])
    else:
        if len(points) > 0:
            msg = "\n".join(f"{point[0]} - {point[1]}" for point in points)
            bot.send_message(message.chat.id, f"Свободные КПшки:\n{msg}")
        else:
            bot.send_message(message.chat.id, "Свободных КПшек нет")


@bot.message_handler(commands=["stop"], state=MyStates.team)
def stop_handler(message: Message):
    bot.set_state(message.chat.id, MyStates.stop)
    bot.send_message(message.chat.id, "Спасибо за участие!")


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
            bot.send_message(message.chat.id, "Вы успешно зарегистрированы как КПшник")
        else:
            bot.set_state(message.chat.id, MyStates.host_name)
            bot.send_message(message.chat.id, "КПшник с таким именем уже есть, попробуйте другое имя")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        bot.send_message(config.admin_id, e.args[0])


@bot.message_handler(commands=["add_host_to"], state=MyStates.host)
def point_id_handler(message: Message):
    args = extract_arguments(message.text).split()
    if len(args) != 1 or not args[0].isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
        return
    try:
        point_id = int(args[0])
        if database.update.host(message.chat.id, point_id):
            bot.send_message(message.chat.id, f"Теперь вы КПшник на {point_id} КПшке")
        else:
            bot.send_message(message.chat.id, "Проверьте правильность введённых данных")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        bot.send_message(config.admin_id, e.args[0])


@bot.message_handler(commands=["reg_team"], state=[MyStates.host, MyStates.admin])
def reg_team_handler(message: Message):
    team_name = extract_arguments(message.text)
    if len(team_name) == 0:
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            if database.add.user(Role.player, message.text.lower()):
                bot.send_message(message.chat.id, "Ваш номер счёта: ")
            else:
                bot.send_message(message.chat.id, "Такая команда уже существует, попробуйте другое название")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            bot.send_message(config.admin_id, e.args[0])


@bot.message_handler(commands=["kp_queue_team"], state=MyStates.host)
def queue_team_handler(message: Message):
    args = extract_arguments(message.text).split(" to ")
    if len(args) != 2 or not args[0].isdigit() or not args[1].isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
        return
    try:
        user_id = int(args[0])
        point = database.get.point(host_tg_id=message.chat.id)
        if point is not None and database.add.queue(point.id, datetime.now(), user_id=user_id):
            bot.send_message(message.chat.id, "Команда успешно поставлена в очередь")
        else:
            bot.send_message(message.chat.id, "Проверьте правильность введённых данных")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        bot.send_message(config.admin_id, e.args[0])


@bot.message_handler(commands=["remove_team_queue"], state=[MyStates.host, MyStates.admin])
def remove_team_queue_handler(message: Message):
    args = extract_arguments(message.text).split()
    if len(args) != 1 or not args[0].isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
        return
    try:
        user_id = int(args[0])
        if database.remove.queue(user_id=user_id):
            bot.send_message(message.chat.id, "Команда успешно удалена из очереди")
        else:
            bot.send_message(message.chat.id, "Проверьте правильность введённых данных")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        bot.send_message(config.admin_id, e.args[0])


@bot.message_handler(commands=["transfer_from_team"], state=[MyStates.host, MyStates.admin])
def transfer_from_team_handler(message: Message):
    args = extract_arguments(message.text).split(" to ")
    args1 = args[0].split()
    if len(args1) != 2 or not args1[0].isdigit() or not args1[1].isdigit() or len(args) != 2 or not args[1].isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
        return
    try:
        from_user_id = int(args1[0])
        amount = int(args1[1])
        recipient = int(args[1])
        if database.update.transfer(recipient, amount, from_user_id=from_user_id):
            bot.send_message(message.chat.id, "Перевод выполнен успешно")
        else:
            bot.send_message(message.chat.id, "Проверьте правильность введённых данных")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        bot.send_message(config.admin_id, e.args[0])


@bot.message_handler(commands=["payment", "payment_nal"])
def payment_handler(message: Message):
    args = extract_arguments(message.text)
    if len(args) == 0 or not args.isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            amount = int(args[0])
            if database.update.payment(message.chat.id, amount,
                                       cash=extract_command(message.text) == "payment_nal"):
                bot.send_message(message.chat.id, "Оплата произведена успешно")
            else:
                bot.send_message(message.chat.id, "Проверьте правильность введённых данных")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            bot.send_message(config.admin_id, e.args[0])


@bot.message_handler(commands=["kp_pause"], state=MyStates.host)
def pause_kp_handler(message: Message):
    try:
        if database.update.pause(message.chat.id):
            bot.send_message(message.chat.id, "КП успешно приостановлена")
        else:
            bot.send_message(message.chat.id, "КП не активна")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        bot.send_message(config.admin_id, e.args[0])


@bot.message_handler(commands=["kp_resume"], state=MyStates.host)
def resume_kp_handler(message: Message):
    try:
        if database.update.resume(message.chat.id):
            bot.send_message(message.chat.id, "КП успешно возобновлена")
        else:
            bot.send_message(message.chat.id, "КП не приостановлена")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        bot.send_message(config.admin_id, e.args[0])


@bot.message_handler(commands=["start_team"], state=MyStates.host)
def start_team_handler(message: Message):
    try:
        user = database.get.point_next_team(message.chat.id)
        if user is not None:
            bot.add_data(message.chat.id, current_team_id=user.id, current_team_tg_id=user.tg_id)
            if user.tg_id is not None:
                bot.add_data(user.tg_id, active=True)
                bot.send_message(user.tg_id, "Ваша команда может пройти на КПшку")
            else:
                bot.send_message(message.chat.id, "У команды нет тг аккаунта")
            bot.send_message(message.chat.id, "Команда успешно вызвана")
        else:
            bot.send_message(message.chat.id, "Некого вызывать")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        bot.send_message(config.admin_id, e.args[0])


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
                bot.send_message(message.chat.id, "Работа с командой успешно завершена")
            else:
                bot.send_message(message.chat.id, "Не удалось удалить очередь активной команды")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            bot.send_message(config.admin_id, e.args[0])


@bot.message_handler(commands=["pay", "pay_nal"], state=MyStates.host)
def pay_handler(message: Message):
    with bot.retrieve_data(message.chat.id) as data:
        current_team_id = data.get("current_team_id")
    if current_team_id is None:
        bot.send_message(message.chat.id, "Нет активной команды")
    else:
        args = extract_arguments(message.text)
        if len(args) != 1 or not args.isdigit():
            bot.send_message(message.chat.id, "Неверный формат")
        else:
            try:
                amount = int(args[0])
                if database.update.pay(message.chat.id, current_team_id, amount,
                                       cash=extract_command(message.text) == "pay_nal"):
                    bot.send_message(message.chat.id, "Выплата произведена успешно")
                else:
                    bot.send_message(message.chat.id, "Проверьте правильность введённых данных")
            except ConnectionError as e:
                bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
                bot.send_message(config.admin_id, e.args[0])


@bot.message_handler(commands=["kp_balance"], state=[MyStates.host, MyStates.admin])
def kp_balance_handler(message: Message):
    args = extract_arguments(message.text).split()
    if len(args) != 1 or not args.isdigit():
        bot.send_message(message.chat.id, "Неверный формат")
    else:
        try:
            point_id = int(args[0])
            balance = database.get.point_balance(point_id)
            if balance is not None:
                bot.send_message(message.chat.id, f"Баланс КП: {balance}")
            else:
                bot.send_message(message.chat.id, "Не удалось получить баланс КП")
        except ConnectionError as e:
            bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
            bot.send_message(config.admin_id, e.args[0])


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
            bot.add_data(bot.user.id, failed_hosts=failed_admins)
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
            bot.send_message(message.chat.id, "Вы успешно зарегистрированы как админ")
        else:
            bot.set_state(message.chat.id, MyStates.admin_name)
            bot.send_message(message.chat.id, "Админ с таким именем уже есть, попробуйте другое имя")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        bot.send_message(config.admin_id, e.args[0])


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
        if database.add.point(message.text, kp_one_time):
            bot.set_state(message.chat.id, MyStates.admin)
            bot.send_message(message.chat.id, "КП успешно зарегистрирована")
        else:
            bot.send_message(message.chat.id, "КП с таким названием уже есть, попробуйте другое название")
    except ConnectionError as e:
        bot.send_message(message.chat.id, "Что-то пошло не так, пожалуйста, попробуйте позже")
        bot.send_message(config.admin_id, e.args[0])


bot.add_custom_filter(StateFilter(bot))
bot.set_state(bot.user.id, MyStates.bot)
bot.infinity_polling()

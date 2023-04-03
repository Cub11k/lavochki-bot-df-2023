import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.custom_filters import StateFilter
from telebot.handler_backends import State, StatesGroup
from telebot.util import extract_arguments

import database
from database import Role

bot = telebot.TeleBot(token="1823274524:AAGXq-uH7Cw9NHplDhsbyRwr2pCaTjWYVgM")


class MyStates(StatesGroup):
    team_name = State()  # MyStates:team_name
    point_id = State()


@bot.message_handler(commands=["start"])
def start_handler(message):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("Да", callback_data="reg_yes"),
                 InlineKeyboardButton("Нет", callback_data="reg_no"))
    bot.send_message(message.chat.id, "Привет! Хочешь зарегистрировать команду?", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith("reg_"))
def reg_buttons_handler(call):
    if call.data == "reg_yes":
        reg_handler(call.message)
    elif call.data == "reg_no":
        bot.send_message(call.message.chat.id, "Жаль, если захочешь, то можешь зарегистрироваться командой /reg")


@bot.message_handler(commands=["help"])
def help_handler(message):
    bot.send_message(message.chat.id, "<b>Команды бота:</b>\n", parse_mode='HTML')
    bot.send_message(message.chat.id, "\n /start - запуск бота и инструкций; \n"
                                      "\n /reg - запуск регистрации для участников; \n"
                                      "\n /balance - показывает, сколько команда заработала вмкешей на данный момент; \n"
                                      "\n /transfare <n> to <m> - перевести n вмкешей команде с id m; \n"
                                      "\n /que_to <l> - занять очередь на кп l; \n"
                                      "\n /place - показывает место в очереди; \n"
                                      "\n/remove_que - отменить свою очередь, если она была назначена на кп; \n"
                                      "\n /stop - остановка участия команды, при котором они больше не проходят кп; \n"
                                      "\n /list_free - команда показывает свободные кпшки\n")


@bot.message_handler(commands=["reg"])
def reg_handler(message):
    bot.send_message(message.chat.id, "Введите название команды")
    bot.set_state(message.from_user.id, MyStates.team_name)


@bot.message_handler(state=MyStates.team_name)
def team_name_handler(message):
    if database.add.user(Role.player, message.text.lower(), message.from_user.id):
        bot.send_message(message.chat.id, "Ваш id: ")
    else:
        bot.send_message(message.chat.id, "Такая команда уже существует, попробуйте другое название")


@bot.message_handler(commands=["reg_host"])
def reg_host_handler(message):
    bot.send_message(message.chat.id, "Введите номер КПшки")
    bot.set_state(message.from_user.id, MyStates.point_id)


@bot.message_handler(state=MyStates.point_id)
def point_id_handler(message):
    user = database.get.user(message.from_user.id)
    if user is not None and user.role == Role.host:
        pass
        # add host to the point


@bot.message_handler(commands=["balance"])
def balance_handler(message):
    bot.send_message(message.chat.id, '<b>Ваш баланс:</b>', parse_mode='HTML')
    user = database.get.user(message.from_user.id)
    if user is not None:
        bot.send_message(message.chat.id, user.balance)


@bot.message_handler(commands=["transfer"])
def transfer_handler(message):
    args = extract_arguments(message.text).split(" to ")
    if len(args) != 2 or not args[0].isdigit():
        bot.send_message(message.chat.id, "Неверный формат команды")
    else:
        amount = int(args[0])
        recipient = args[1]
        user = database.get.user(message.from_user.id)
        if user is not None and user.balance >= amount:
            if database.update.transfer(user.id, recipient, amount):
                bot.send_message(message.chat.id, "Перевод выполнен!")
            else:
                bot.send_message(message.chat.id, "Не получилось, проверьте правильность введенных данных")


@bot.message_handler(commands=["que_to"])
def que(message):
    message1 = bot.send_message(message.chat.id, "Введите номер КП")
    bot.register_next_step_handler(message1, end_que)
    number = message.text
    print(number)


def end_que(message):
    bot.send_message(message.chat.id, "Вы забронировали место!")


@bot.message_handler(commands=["place"])
def plc(message):
    bot.send_message(message.chat.id, "<b>Ваше место в очереди:</b>", parse_mode='HTML')
    bot.send_message(message.chat.id, "Место в очереди из БД")


@bot.message_handler(commands=["remove_que"])
def rem_q(message):
    bot.send_message(message.chat.id, "Очередь отменена")


@bot.message_handler(commands=["end"])  # почему-то /stop не работает
def end(message):
    bot.send_message(message.chat.id, "<b> Игра окончена</b>", parse_mode='HTML')
    bot.send_message(message.chat.id, "Спасибо за участие")


@bot.message_handler(commands=["list_free"])
def list(message):
    bot.send_message(message.chat.id, "<b>Сейчас свободна(ы):</b>", parse_mode='HTML')
    bot.send_message(message.chat.id, "Вывести свободные КП")


@bot.message_handler(commands=["start_kps"])
def start_kp(message):
    bot.send_message(message.chat.id, "Здравствуй, добрый человек!")
    bot.send_message(message.chat.id, "Да прибудет с тобой сила!")
    # интсрукция для КПШников
    bot.send_message(message.chat.id, "<b>Команды бота:</b>\n", parse_mode='HTML')
    bot.send_message(message.chat.id, "\n /start_kps - запуск бота и инструкций; \n"
                                      "\n /reg_kp - запуск регистрации для участников; \n"
                                      "\n /balance - показывает, сколько команда заработала вмкешей на данный момент; \n"
                                      "\n /transfare <n> to <m> - перевести n вмкешей команде с id m; \n"
                                      "\n /que_to <l> - занять очередь на кп l; \n"
                                      "\n /place - показывает место в очереди; \n"
                                      "\n/remove_que - отменить свою очередь, если она была назначена на кп; \n"
                                      "\n /stop - остановка участия команды, при котором они больше не проходят кп; \n"
                                      "\n /list_free - команда показывает свободные кпшки\n")


@bot.message_handler(commands=["reg_kp"])
def reg_kp(message):
    message1 = bot.send_message(message.chat.id, "Введите название КП")
    bot.register_next_step_handler(message1, end_reg)
    d = message.text
    print(d)


def end_reg(message):
    bot.send_message(message.chat.id, "КП успешно зарегистрирована")
    m = message.text
    print(m)


@bot.message_handler(commands=["reg_team"])
def reg_tm(message):
    bot.send_message(message.chat.id, "Команда успешно зарегистрирована")
    bot.send_message(message.chat.id, "Ваш номер:")


@bot.message_handler(commands=["que_team"])
def que_tm_id(message):
    message1 = bot.send_message(message.chat.id, "Введите id команды")
    bot.register_next_step_handler(message1, que_tm_num)
    message_to_save1 = message.text
    print(message_to_save1)


def que_tm_num(message):
    message2 = bot.send_message(message.chat.id, "Введите номер КП")
    bot.register_next_step_handler(message2, que_tm_end)
    message_to_save2 = message.text
    print(message_to_save2)


def que_tm_end(message):
    bot.send_message(message.chat.id, "Команда успешно поставлена в очередь")
    message_to_save3 = message.text
    print(message_to_save3)


@bot.message_handler(commands=["remove_team_que"])
def rem_que_tm_id(message):
    message1 = bot.send_message(message.chat.id, "Введите id команды")
    bot.register_next_step_handler(message1, rem_que_tm_id_2)
    message_to_save1 = message.text
    print(message_to_save1)


def rem_que_tm_id_2(message):
    bot.send_message(message.chat.id, "Команда успешно удалена из очереди")
    message_to_save2 = message.text
    print(message_to_save2)


@bot.message_handler(commands=["transfare_team_money"])
def ttm(message):
    message1 = bot.send_message(message.chat.id, "Введите ID команды 1")
    bot.register_next_step_handler(message1, ttm_2)
    message_to_save1 = message.text
    print(message_to_save1)


def ttm_2(message):
    message2 = bot.send_message(message.chat.id, "Введите ID команды 2")
    bot.register_next_step_handler(message2, ttm_3)
    message_to_save2 = message.txt
    print(message_to_save2)


def ttm_3(message):
    bot.send_message(message.chat.id, "Перевод успешно выполнен")
    message_to_save3 = message.text
    print(message_to_save3)


@bot.message_handler(commands=["payment"])
def payment(message):
    message1 = bot.send_message(message.chat.id, "Введите сумму:")
    bot.register_next_step_handler(message1, payment_2)
    message_to_save1 = message.txt
    print(message_to_save1)


def payment_2(message):
    bot.send_message(message.chat.id, "Оплата произведена")
    message_to_save2 = message.txt
    print(message_to_save2)


@bot.message_handler(commands=["payment_nal"])
def pay_nal(message):
    message1 = bot.send_message(message.chat.id, "Введите сумму:")
    bot.register_next_step_handler(message1, pay_nal_2)
    message_to_save1 = message.txt
    print(message_to_save1)


def pay_nal_2(message):
    bot.send_message(message.chat.id, "Оплата произведена")
    message_to_save2 = message.txt
    print(message_to_save2)


@bot.message_handler(commands=["reg_kp"])
def reg(message):
    message1 = bot.send_message(message.chat.id, 'Введите номер кп')
    bot.register_next_step_handler(message1, reg_2)
    message_to_save = message.txt
    print(message_to_save)


def reg_2(message):
    bot.send_message(message.chat.id, 'КП зарегистрирована')


################################################################################################################################
# Вот отсюда перестал работать. Не пойму почему. Писал те же самые команды. Бот обрабатывает команды, но не отвечает:(

@bot.message_handler(commands=['start_team'])
def start_tm(message):
    bot.send_message(message.chat.id, 'Команда вызвана')  # посмотреть


@bot.message_handler(commands=['stop_team'])
def stop_tm(message):
    bot.send_message(message.chat.id, 'Команда завершила прохождение КП')  # посмотреть


@bot.message_handler(commands=["pay"])
def pay(message):
    message1 = bot.send_message(message.chat.id, "Введите сумму")
    bot.register_next_step_handler(message1, pay_2)
    message_to_save1 = message.txt
    print(message_to_save1)


def pay_2(message):
    bot.send_message(message.chat.id, "Оплата произвдена")  # посмотреть почему-то команды перестали работать


@bot.message_handler(commands=["pay_nal"])
def pay_n(message):
    message1 = bot.send_message(message.chat.id, "Введите сумму")
    bot.register_next_step_handler(message1, pay_2)
    message_to_save1 = message.txt
    print(message_to_save1)


def pay_n_2(message):
    bot.send_message(message.chat.id, "Оплата произвдена")  # посмотреть почему-то команды перестали работать


@bot.message_handler(commands=["kp_que_team"])
def kp_que(message):
    message1 = bot.send_message(message.chat.id, "Введите ID команды")
    bot.register_next_step_handler(message1, kp_que_2)
    message_to_save1 = message.txt
    print(message_to_save1)


def kp_que_2(message):
    bot.send_message(message.chat.id, "Команда поставлена в очередь")


@bot.message_handler(commands=["kp_balance"])
def kp_bal(message):
    message1 = bot.send_message(message.chat.id, "Введите ID КП")
    bot.register_next_step_handler(message1, kp_bal_2)
    message_to_save1 = message.txt
    print(message_to_save1)


def kp_bal_2(message):
    message2 = bot.send_message(message.chat.id, "Баланс КП:")
    bot.register_next_step_handler(message2, kp_bal_3)
    message_to_save1 = message.txt
    print(message_to_save1)


def kp_bal_3(message):
    bot.send_message(message.chat.id, "Вывести баланс")


bot.add_custom_filter(StateFilter(bot))
bot.infinity_polling()

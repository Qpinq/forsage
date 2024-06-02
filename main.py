import telebot
from telebot import types
from database import *
import hashlib


token = 'token'
bot = telebot.TeleBot(token)
user_condition = {}


@bot.message_handler(commands=['start'])
def s(message):
    bot.send_message(message.chat.id, "Здравствуйте, я - бот-помощник Форси, как я могу к Вам обращаться?"
                                      "\n\nПродолжая работу со мной, "
                                      "Вы <b>соглашаетесь</b> на хранение Ваших персональных данных, а именно: "
                                      "<b>Ваши уникальные id, имя пользователя и имя, которое укажете ниже</b>",
                     parse_mode="HTML")
    user_condition[message.chat.id] = 'waiting_name'
    add_user(message)


@bot.message_handler(commands=['catalog'])
def t(message):
    menu_types(message.chat.id)


@bot.message_handler(commands=['staff'])
def staff(message):
    staff_(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        if call.data == 'menu_types':
            menu_types(call.message.chat.id)
            user_condition[call.message.chat.id] = 'waiting_type'
        elif call.data[:12] == 'waitingType_':
            products_type(call.message.chat.id, call.data[12:], 1)
        elif call.data[:5] == "type_":
            parts = call.data.split("_")
            id_type = parts[1]
            page = int(parts[2])
            products_type(call.message.chat.id, id_type, page)
        elif call.data[:6] == 'order_':
            product_ = info('name', 'id', call.data[6:], 'products')
            keyboard_inline = types.InlineKeyboardMarkup()
            yes = types.InlineKeyboardButton(text="Да", callback_data=f'yes_{call.data[6:]}_1_'
                                                                      f'{info('price', 'id', call.data[6:], 'products')}')
            more = types.InlineKeyboardButton(text="Больше", callback_data=f'more_{call.data[6:]}')
            keyboard_inline.add(yes, more)
            bot.send_message(call.message.chat.id, f'Вы уверены, что хотите купить <b>{product_}</b> в количестве'
                                                   f' <i>1 штука?</i>',
                             reply_markup=keyboard_inline, parse_mode="HTML")
        elif call.data[:5] == 'more_':
            user_condition[call.message.chat.id] = f'waiting_more_{call.data[5:]}'
            bot.send_message(call.message.chat.id, f'А сколько штук Вам нужно приобрести?')
        elif call.data[:4] == 'yes_':
            keyboard = generate_next_7_days(call.data[3:])
            bot.send_message(call.message.chat.id, 'В какой день Вам будет удобно забрать и оплатить '
                                                   'покупку в нашем магазине?\n\n<b>Адрес:</b> <i>г. '
                                                   'Ростов-на-Дону, просп. Михаила Нагибина, 45</i>\n<b>Режим работы:'
                                                   '</b> '
                                                   'пн-вс с 10.00 до 20:00', parse_mode="HTML", reply_markup=keyboard)
        elif call.data[:5] == 'date_':
            parts = call.data.split('_')
            keyboard = types.InlineKeyboardMarkup()
            info_cheque = cheque(call.message.chat.id, parts[1], parts[2], parts[3], parts[4])
            delete = types.InlineKeyboardButton(text="Отменить заказ", callback_data=f'del_{info_cheque[0]}')
            keyboard.add(delete)
            bot.send_message(call.message.chat.id, f'<i><b>Поздравляем с покупкой!</b></i>\n\n<b>Номер заказа:</b> '
                                                   f'{info_cheque[0]}\n<b>Название товара:</b> {info_cheque[1]}\n'
                                                   f'<b>Количество:</b> {info_cheque[2]} шт.\n\n<b>Стоимость:</b> '
                                                   f'{info_cheque[3]} руб.\n<b>Дата заказа:</b> {info_cheque[4]}\n'
                                                   f'<b>Дата выдачи:</b> {info_cheque[5]} с 10:00 до 20:00\n\n'
                                                   f'<b>Адрес:</b> <i>г. Ростов-на-Дону, просп. Михаила Нагибина, 45\n'
                                                   f'\nЧтобы забрать заказ озвучьте или покажите номер заказа '
                                                   f'сотруднику</i>',
                             parse_mode="HTML", reply_markup=keyboard)
        elif call.data[:4] == 'del_':
            delete_(call.data[4:])
            bot.send_message(call.message.chat.id, f'<i>Вы отменили заказ <b>{call.data[4:]}</b></i>',
                             parse_mode="HTML")
        elif call.data == 'back':
            staff_(call.message)
        elif call.data == 'today' or call.data == 'tomorrow' or call.data == 'all':
            info_ = info('name', 'id', call.message.chat.id, 'staff')
            if info_ is None:
                bot.send_message(call.message.chat.id, f'<i><b>Вы не зарегистрированы как сотрудник.</b></i> '
                                                       f'Введите пароль для доступа к функциям сотрудников',
                                 parse_mode="HTML")
                user_condition[call.message.chat.id] = 'waiting_pass'
            else:
                keyboard_inline = types.InlineKeyboardMarkup()
                back = types.InlineKeyboardButton(text='Назад', callback_data='staff')
                keyboard_inline.add(back)
                if call.data == 'today':
                    day(call.message, datetime.now())
                elif call.data == 'tomorrow':
                    date = datetime.now() + timedelta(days=1)
                    day(call.message, date)
                elif call.data == 'all':
                    day(call.message)
        elif call.data[:5] == 'take_':
            take(call.data[5:], call.message.chat.id)
            bot.send_message(call.message.chat.id, f'Заказ <b><i>{call.data[5:]}</i></b> был выдан сотрудником '
                                                   f'по имени <i>'
                                                   f'{info('name', 'id', call.message.chat.id, 'staff')}</i>, '
                                                   f'<b>{datetime.now().strftime('%d.%m.%Y')}</b>', parse_mode="HTML")
            bot.send_message(info('id_user', 'id', call.data[5:], 'cheque'), f'Заказ <b><i>{call.data[5:]}'
                                                                   f'</i></b> был выдан сотрудником по имени <i>'
                                                                   f'{info('name', 'id', call.message.chat.id, 'staff')}'
                                                                   f'</i>, <b>'
                                                                   f'{datetime.now().strftime('%d.%m.%Y')}</b>',
                             parse_mode="HTML")
    except Exception as e:
        print(f"Произошла ошибка при обработке сообщения: {e}")
        bot.send_message(call.message.chat.id, "Повторите запрос позже")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        if user_condition.get(message.chat.id) == "waiting_name":
            name(message)
            bot.send_message(message.chat.id, f'<i>Приятно познакомится, {message.text}</i>', parse_mode='HTML')
            menu_types(message.chat.id)
            user_condition[message.chat.id] = ''
        elif message.text.isdigit():
            if user_condition.get(message.chat.id)[:13] == "waiting_more_":
                quantity = info('quantity', 'id', user_condition.get(message.chat.id)[13:], 'products')
                if quantity >= int(message.text):
                    price = int(message.text)*int(info('price', 'id', user_condition.get(message.chat.id)[13:], 'products'))
                    keyboard_inline = types.InlineKeyboardMarkup()
                    yes = types.InlineKeyboardButton(text="Да", callback_data=f'yes_{user_condition.get(message.chat.id)[13:]}_{message.text}_{price}')
                    keyboard_inline.add(yes)
                    bot.send_message(message.chat.id, f'Хорошо, <i>{info('name', 'id', message.chat.id, 'users')}'
                                                      f'</i>\n\nВы уверены, что хотите приобрести <b>'
                                                      f'{info('name', 'id', user_condition.get(message.chat.id)[13:], 'products')}'
                                                      f'</b> в количестве {message.text} шт.?\n<b>Стоимость: '
                                                      f'{price}</b>',
                                     parse_mode="HTML", reply_markup=keyboard_inline)
                else:
                    price = int(quantity) * int(
                        info('price', 'id', user_condition.get(message.chat.id)[13:], 'products'))
                    keyboard_inline = types.InlineKeyboardMarkup()
                    yes = types.InlineKeyboardButton(text=f"Заказать {quantity} шт.",
                                                     callback_data=f'yes_{user_condition.get(message.chat.id)[13:]}'
                                                                   f'_{quantity}_{price}')
                    no = types.InlineKeyboardButton(text="Другое количество", callback_data=f'more_'
                                                                              f'{user_condition.get(message.chat.id)[13:]}')
                    keyboard_inline.add(yes, no)
                    bot.send_message(message.chat.id, f'<i>{info('name', 'id', message.chat.id, 'users')}'
                                                      f'</i>, к сожалению, на данный момент у нас только <b><u>{quantity} '
                                                      f'шт.</u></b> этого товара, '
                                                      f'\n\nВы готовы приобрести <b>'
                                                      f'{info('name', 'id', 
                                                              user_condition.get(message.chat.id)[13:], 'products')}'
                                                      f'</b> в количестве <u>{quantity} шт.</u>?\n<b>Стоимость: '
                                                      f'{price}</b>',
                                     parse_mode="HTML", reply_markup=keyboard_inline)
                    user_condition[message.chat.id] = ''
            else:
                product(message.chat.id, message.text)
        elif user_condition.get(message.chat.id) == "waiting_pass":
            pas = hashlib.sha256(message.text.encode('utf-8')).hexdigest()
            info_ = info('password', 'password', pas, 'passwords')
            if info_:
                add_staff(message.chat.id, message.from_user.username)
                bot.send_message(message.chat.id, f'<i>{info('name', 'id', message.chat.id, 'staff')}, '
                                                  f'Вы добавлены в базу данных сотрудников, '
                                                  f'чтобы увидеть функции, нужно нажать /staff</i>',
                                 parse_mode="HTML")
                user_condition[message.chat.id] = ''
    except Exception as e:
        print(f"Произошла ошибка при обработке сообщения: {e}")
        bot.send_message(message.chat.id, "Повторите запрос позже")


def staff_(message):
    info_ = info('name', 'id', message.chat.id, 'staff')
    if info_ is None:
        bot.send_message(message.chat.id, f'<i><b>Вы не зарегистрированы как сотрудник.</b></i> '
                                          f'Введите пароль для доступа к функциям сотрудников', parse_mode="HTML")
        user_condition[message.chat.id] = 'waiting_pass'
    else:
        keyboard_inline = types.InlineKeyboardMarkup()
        today = types.InlineKeyboardButton(text='Заказы на сегодня', callback_data='today')
        tomorrow = types.InlineKeyboardButton(text='Заказы на завтра', callback_data='tomorrow')
        all_ = types.InlineKeyboardButton(text='Все заказы', callback_data='all')
        keyboard_inline.add(today)
        keyboard_inline.add(tomorrow)
        keyboard_inline.add(all_)
        bot.send_message(message.chat.id, f'{info_}, для Вас доступны следующие функции:',
                         reply_markup=keyboard_inline, parse_mode="HTML")


bot.polling()

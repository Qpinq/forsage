import telebot
from telebot import types
import mysql.connector
from mysql.connector import errorcode
import random
import string
from datetime import datetime, timedelta


token = 'token'
bot = telebot.TeleBot(token)
user_condition = {}


def create_connection():
    try:
        conn = mysql.connector.connect(host='', user='', password='', database='')
        return conn
    except Exception as e:
        print(e)


def add_user(message):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute('INSERT IGNORE INTO users (id, first_name) VALUES (%s, %s)',
                  (message.chat.id, '@' + message.from_user.username))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Произошла ошибка в функции add_user: {e}")


def name(message):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute(f"UPDATE users SET name = %s WHERE id = %s",
                  (message.text, message.chat.id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Произошла ошибка в функции name: {e}")


def permission_off(user_id):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute(f"UPDATE users SET permission = %s WHERE id = %s",
                  ('0', user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Произошла ошибка в функции permission_off: {e}")


def menu_types(user_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT id, name FROM types_products")
    types_products = c.fetchall()
    conn.close()
    response_message = '\n\n<b>Наш каталог:</b>\n'
    keyboard_ = types.InlineKeyboardMarkup()
    row = []
    for type_name in types_products:
        button_ = types.InlineKeyboardButton(text=type_name[1], callback_data=f'waitingType_{type_name[0]}')
        row.append(button_)
        if len(row) == 2:
            keyboard_.row(*row)
            row = []
    if row:
        keyboard_.row(*row)
    try:
        bot.send_message(user_id, response_message, parse_mode='HTML', reply_markup=keyboard_)
    except telebot.apihelper.ApiException as e:
        if e.error_code == 403 or e.error_code == 400:
            permission_off(user_id)
        else:
            print("Ошибка при отправке сообщения:", e)


def products_type(user_id, type_id, page):
    try:
        begin = (page - 1) * 10
        count = 10
        conn = create_connection()
        c = conn.cursor()
        c.execute("SELECT name FROM types_products where id = %s", (type_id,))
        name_type = c.fetchone()[0]
        response_message = f'<b><i><u>{name_type}</u></i></b>:  '
        c.execute("SELECT count(*) FROM products where type_id = %s", (type_id,))
        further_ = f'type_{type_id}_{page+1}'
        last_page = c.fetchone()[0] // 10 + 1
        response_message += f'{page}/{last_page}'
        if page == last_page:
            further_ = f'type_{type_id}_1'
        c.execute("SELECT id, name, size FROM products where type_id = %s and quantity > 0 limit %s, %s",
                  (type_id, begin, count))
        types_products = c.fetchall()
        conn.close()
        response_message += f'\n\n'
        for type_name in types_products:
            response_message += f'<b>{type_name[0]}.</b> {type_name[1].strip()}, <i>размер: {type_name[2]}</i>\n'
        response_message += '\n<b>Чтобы узнать подробнее о товаре, напишите его номер</b>'
        if page == 1:
            back_ = 'menu_types'
        else:
            back_ = f'type_{type_id}_{page-1}'
        keyboard_inline = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton(text="Назад", callback_data=back_)
        further = types.InlineKeyboardButton(text="Далее", callback_data=further_)
        another_type = types.InlineKeyboardButton(text="Выбрать другую категорию", callback_data='menu_types')
        keyboard_inline.add(back, further)
        keyboard_inline.add(another_type)
        bot.send_message(user_id, response_message, reply_markup=keyboard_inline, parse_mode="HTML")
    except Exception as e:
        print(f"Произошла ошибка в функции products_type: {e}")


def product(user_id, product_id):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute("SELECT name, material, size, color, img, price, quantity FROM products where id = %s", (product_id,))
        product_info = c.fetchone()
        conn.close()
        name_ = product_info[0]
        keyboard_inline = types.InlineKeyboardMarkup()
        if int(product_info[6]) != 0:
            description = (f'<b>Материал:</b> {product_info[1]}\n<b>Размер:</b> {product_info[2]}\n<b>Цвет:</b>'
                           f' {product_info[3]}\n\n<b>Цена: {product_info[5]} руб.</b>')
            back = types.InlineKeyboardButton(text="Заказать", callback_data=f'order_{product_id}')
        else:
            description = (f'<u><b>На данный момент этого товара нет на складе!\n\n</b></u><b>Материал:</b> '
                           f'{product_info[1]}\n<b>Размер:</b> {product_info[2]}\n<b>Цвет:</b>'
                           f' {product_info[3]}\n\n<b>Цена: {product_info[5]} руб.</b>')
            back = types.InlineKeyboardButton(text="Перейти в каталог", callback_data='menu_types')
        keyboard_inline.add(back)
        response_message = f'<b><i>{product_id}. <u>{name_}</u></i></b>:\n\n{description}'
        if product_info[4] is not None:
            photo = open(f'img/id_{product_info[4]}.jpg', 'rb')
            bot.send_photo(user_id, photo)
        bot.send_message(user_id, response_message, reply_markup=keyboard_inline, parse_mode="HTML")
    except Exception as e:
        print(f"Произошла ошибка в функции product: {e}")


def info(col_info, col, val, table):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute(f"SELECT {col_info} FROM {table} where {col} = %s", (val,))
        result = c.fetchone()
        conn.close()
        if result is not None:
            return result[0]
        else:
            return None
    except Exception as e:
        print(f"Произошла ошибка в функции info: {e}")


def add_staff(staff_id, first_name):
    try:
        name_ = info('name', 'id', staff_id, 'users')
        conn = create_connection()
        c = conn.cursor()
        c.execute(f"insert into staff(id, first_name, name) values (%s, %s, %s)",
                  (staff_id, '@' + first_name, name_))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Произошла ошибка в функции add_staff: {e}")


def delete_(id_cheque):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute(f"DELETE FROM cheque WHERE id = %s", (id_cheque,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Произошла ошибка в функции delete: {e}")


def cheque(user_id_telegram, product_id, quantity, price, date_issue):
    conn = create_connection()
    c = conn.cursor()
    characters = string.ascii_letters + string.digits
    unique_id = ''.join(random.choices(characters, k=7))
    date_cheque = datetime.today().strftime('%Y-%m-%d')
    while True:
        try:
            c.execute("INSERT INTO cheque (id, user_id, product_id, quantity, price, date_cheque, date_issue) "
                      "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                      (unique_id, user_id_telegram, product_id, quantity, price, date_cheque, date_issue))
            c.execute("update products set request = request + %s, quantity = quantity - %s where id = %s",
                      (quantity, quantity, product_id))
            conn.commit()
            break
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_DUP_ENTRY:
                print(f"Идентификатор {unique_id} уже существует, генерирую новый...")
                conn.rollback()
                unique_id = ''.join(random.choices(characters, k=7))
            else:
                print(f"Произошла ошибка в функции cheque: {err}")
                conn.rollback()
                break
    conn.close()
    return unique_id, info('name', 'id', product_id, 'products'), quantity, price, date_cheque, date_issue


def day(message, date=None):
    try:
        conn = create_connection()
        c = conn.cursor()
        if date:
            c.execute('SELECT ch.id, u.first_name, u.name, pr.id, pr.name, pr.price, ch.quantity, ch.price, '
                      'ch.date_cheque FROM products pr INNER JOIN cheque ch on ch.product_id = pr.id '
                      'INNER JOIN users u on u.id = ch.user_id where ch.date_issue = %s and ch.staff_id is NULL',
                      (date.strftime('%Y-%m-%d'),))
            result = c.fetchall()
            conn.close()
            if result:
                bot.send_message(message.chat.id, f'<b>Заказы на <i>{get_weekday(date)}, '
                                                  f'{date.strftime('%d.%m.%Y')}</i>:</b>', parse_mode="HTML")
                for row in result:
                    keyboard_inline = types.InlineKeyboardMarkup()
                    back = types.InlineKeyboardButton(text="Забрали", callback_data=f'take_{row[0]}')
                    keyboard_inline.add(back)
                    bot.send_message(message.chat.id, f'<b>Номер заказа: </b>{row[0]}\n\n<b>Никнейм '
                                     f'покупателя: </b>{row[1]}\n<b>Имя покупателя: </b>{row[2]}\n\n'
                                     f'<b>id товара: </b>{row[3]}\n<b>Название товара: </b> {row[4]}\n<b>Цена: </b>'
                                     f'{row[5]}\n\n<b>Количество: </b> {row[6]} шт.\n<b>Стоимость:</b> {row[7]} руб.\n'
                                     f'<b>Дата заказа: </b> {row[8]}\n', parse_mode="HTML", reply_markup=keyboard_inline)
            else:
                bot.send_message(message.chat.id, f'<b>Заказов на <i>{get_weekday(date)}, '
                                                  f'{date.strftime('%d.%m.%Y')}</i>, нет</b>', parse_mode="HTML")
        else:
            c.execute('SELECT ch.id, u.first_name, u.name, pr.id, pr.name, pr.price, ch.quantity, ch.price, '
                      'ch.date_cheque FROM products pr INNER JOIN cheque ch on ch.product_id = pr.id '
                      'INNER JOIN users u on u.id = ch.user_id where ch.staff_id is NULL')
            result = c.fetchall()
            conn.close()
            if result:
                bot.send_message(message.chat.id, f'<b>Все заказы:</b>', parse_mode="HTML")
                for row in result:
                    keyboard_inline = types.InlineKeyboardMarkup()
                    back = types.InlineKeyboardButton(text="Забрали", callback_data=f'take_{row[0]}')
                    keyboard_inline.add(back)
                    bot.send_message(message.chat.id, f'<b>Номер заказа: </b>{row[0]}\n\n<b>Никнейм '
                                                      f'покупателя: </b>{row[1]}\n<b>Имя покупателя: </b>{row[2]}\n\n'
                                                      f'<b>id товара: </b>{row[3]}\n<b>Название товара: </b> {row[4]}'
                                                      f'\n<b>Цена: </b>{row[5]}\n\n<b>Количество: </b> {row[6]} шт.'
                                                      f'\n<b>Стоимость:</b> {row[7]} руб.\n'
                                                      f'<b>Дата заказа: </b> {row[8]}',
                                     parse_mode="HTML", reply_markup=keyboard_inline)
            else:
                bot.send_message(message.chat.id, f'<b>Заказов нет</b>', parse_mode="HTML")
    except Exception as e:
        print(f"Произошла ошибка в функции day: {e}")


def take(id_cheque, staff_id):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute(f"update cheque set staff_id = %s, date_issue = %s"
                  f"where id = %s", (staff_id, datetime.now().strftime('%Y-%m-%d'), id_cheque))
        c.execute("update products set request = request - %s where id = %s",
                  (info('quantity', 'id', id_cheque, 'cheque'),
                   info('product_id', 'id', id_cheque, 'cheque')))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Произошла ошибка в функции take: {e}")


def generate_next_7_days(call):
    today = datetime.now()
    keyboard_ = types.InlineKeyboardMarkup()
    for i in range(1, 8, 2):
        day = today + timedelta(days=i)
        formatted_date = day.strftime("%Y-%m-%d")
        text_date = day.strftime("%d.%m.%Y")
        day_2 = today + timedelta(days=i+1)
        formatted_date_2 = day_2.strftime("%Y-%m-%d")
        text_date_2 = day_2.strftime("%d.%m.%Y")
        button_ = types.InlineKeyboardButton(text=text_date, callback_data=f'date{call}_{formatted_date}')
        button_2 = types.InlineKeyboardButton(text=text_date_2, callback_data=f'date{call}_{formatted_date_2}')
        keyboard_.add(button_, button_2)
    return keyboard_


def get_weekday(date):
    try:
        weekdays = ['Понедельник', 'Вторник', 'Среду', 'Четверг', 'Пятницу', 'Субботу', 'Воскресенье']
        today_weekday = date.weekday()
        return weekdays[today_weekday]
    except Exception as e:
        print('Ошибка в функции get_weekday:', e)

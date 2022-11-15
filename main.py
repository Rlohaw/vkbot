import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import mysql.connector
from random import randint
from keys import main_token as tk
from bs4 import BeautifulSoup


class Anecdot:
    def __init__(self, host='localhost', user='root', password='75645', database='anekdots'):
        self.mydb = mysql.connector.connect(host=host, user=user, password=password, database=database)
        self.cursor = self.mydb.cursor()

    def get_anecdot(self, id):
        number = randint(1, 130263)
        while number in self.read_anecdots(id):
            number = randint(1, 130263)
        self.cursor.execute(f"select text from anek where id={number}")
        res = self.cursor.fetchall()[0][0]
        self.cursor.execute(f"insert into {str(id) + '_grades'}(number, grade) values ({number}, {-1})")
        self.mydb.commit()
        soup = BeautifulSoup(res, 'lxml')
        res = str(soup.text)
        return res

    def rate_anecdot(self, id, grade):
        dts = self.read_anecdots(id)
        nbm = dts[-1]
        self.cursor.execute(f"update {id}_grades set grade={grade} where number={nbm}")
        self.mydb.commit()

    def read_anecdots(self, id):
        self.cursor.execute(f"select number from {id}_grades")
        return tuple(map(lambda x: x[0], self.cursor))

    def create_user(self, id):
        self.cursor.execute('show tables')
        if str(id) + '_grades' not in list(map(lambda x: x[0], self.cursor)):
            self.cursor.execute(f"create table {id}_grades (number int, grade int)")


class Bot:
    def __init__(self, main_token):
        self.user_id = None
        self.vk_session = vk_api.VkApi(token=main_token)
        self.session_api = self.vk_session.get_api()
        self.long_pool = VkLongPoll(self.vk_session)

    def sender(self, id, text, keyboard=None):
        post = {'user_id': id,
                'message': text,
                'random_id': 0}
        if keyboard is not None:
            post['keyboard'] = keyboard.get_keyboard()
        self.vk_session.method('messages.send', post)

    def give_anc(self):
        keyboard = VkKeyboard()
        keyboard.add_button('Дай Анекдот!', VkKeyboardColor.POSITIVE)
        self.sender(self.user_id, 'Чего тебе, старче?', keyboard)

    def score_anc(self):
        score_keyboard = VkKeyboard()
        score_keyboard.add_button('1', VkKeyboardColor.NEGATIVE)
        score_keyboard.add_button('2', VkKeyboardColor.NEGATIVE)
        score_keyboard.add_button('3', VkKeyboardColor.SECONDARY)
        score_keyboard.add_button('4', VkKeyboardColor.POSITIVE)
        score_keyboard.add_button('5', VkKeyboardColor.POSITIVE)
        self.sender(self.user_id, 'Оцените онекдотъ:', score_keyboard)

    def event(self):
        for event in self.long_pool.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                text = event.text.lower()
                self.user_id = event.user_id
                Anecdot().create_user(self.user_id)
                if text == 'начать':
                    self.give_anc()

                elif text == 'дай анекдот!':
                    txt = Anecdot().get_anecdot(self.user_id)
                    self.sender(self.user_id, txt)
                    self.score_anc()

                elif text in '12345':
                    anc = Anecdot()
                    anc.rate_anecdot(self.user_id, text)
                    self.give_anc()

                elif text:
                    k = VkKeyboard()
                    k.add_button('Начать', VkKeyboardColor.PRIMARY)
                    self.sender(self.user_id, 'Нажми на кнопку', k)


while True:
    try:
        Bot(tk).event()
    except Exception as e:
        print(e)

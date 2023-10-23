import tkinter as tk
from tkinter import ttk
from tkinter import messagebox as mb
import os
import sqlite3 as sql
from datetime import datetime
import telebot as tb
from telebot import types
import threading as thread
import sys

# TelegramBot class - Класс приложения архива телеграм бота
# https://t.me/AudioCollector_Bot - для проверки данного токена


class EnglishArchiveBot(tb.TeleBot):
    def __init__(self, given_token=None, window_gui=None):
        tb.TeleBot.__init__(self, given_token)

        self.bot_active = True

        # Вместо given_token указывается свой уникальный токен

        self.given_token = given_token
        self.AppGui = window_gui

        self.startPosition = True
        self.SelectedThemePosition = False

        # Создание подключения к базе данных, чтобы получить названия всех уникальных тем

        sql_con = sql.connect(
            os.path.abspath(os.path.dirname(sys.argv[0])) + "\\Database\\" + "Vk_group_archive.sqlite3")
        sql_cursor = sql_con.cursor()

        sql_cursor.execute("SELECT arc.Theme FROM Archive arc GROUP BY arc.Theme ")
        self.unique_themes = sql_cursor.fetchall()

        sql_con.close()

        self.unique_themes = [theme[0] for theme in self.unique_themes]
        self.unique_themes_dict = dict(enumerate(self.unique_themes))

        self.themed_records_ids = []
        self.themed_record = []
        self.recordIds = []
        self.themeIDs = []

        self.sending_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # one_time_keyboard=True

        sending_markup_btn = types.KeyboardButton(text='/start')
        self.sending_markup.row(sending_markup_btn)
        self.bot_message = ""

        # Функция начала работы Telegram-бота

        @self.message_handler(commands=["start"])
        def start_message(message):
            if self.AppGui.get_bot_active_state():
                self.SelectedThemePosition = False

                # Отправка пользователю инструкций по эксплуатации

                self.send_message(message.chat.id, "Данный telegram-бот предназначен для работы с архивом"
                                                   "английских видео-материалов\n")

                self.bot_message = "В данном архиве представлены примеры по следующим темам английского языка\n\n"
                for theme_id, theme in enumerate(self.unique_themes):
                    self.themeIDs.append(theme_id)
                    self.bot_message += f"{theme_id} - {theme};\n"

                self.bot_message += "\nВведите соответсвующие число, чтобы получить доступ к примерам определенной темы"
                self.send_message(message.chat.id, self.bot_message, reply_markup=self.sending_markup)

            else:

                self.send_message(message.chat.id, "Работа Telegram-бота была прекращена! "
                                                   "Попробуйте позже. Введите команду /start",
                                  reply_markup=self.sending_markup)

                self.stop_polling()

        # Функция обработки событий, когда пользователь оправил текст

        @self.message_handler(content_types=["text"])
        def handler_for_text_message(message):

            if self.AppGui.get_bot_active_state():
                if int(message.text.lower()) in self.themeIDs and not self.SelectedThemePosition:

                    self.startPosition = False
                    self.SelectedThemePosition = True

                    msg = self.unique_themes_dict.get(int(message.text.lower()))

                    # Создание подключения к базе данных, чтобы получить доступ к записям определенной темы

                    sql_con = sql.connect(
                        os.path.abspath(os.path.dirname(sys.argv[0])) + "\\Database\\" + "Vk_group_archive.sqlite3")
                    sql_cursor = sql_con.cursor()

                    sql_cursor.execute("SELECT RecordID FROM Archive WHERE Theme = '{0}'".format(msg))

                    self.themed_records_id = sql_cursor.fetchall()

                    sql_con.close()

                    # Формирование ответа пользователю

                    message_text = f"Вы выбрали '{msg}' тему! \nВведите одно из следующих чисел: "

                    for Record in self.themed_records_id:
                        self.recordIds.append(Record[0])
                        message_text += f"{Record[0]} "

                    message_text += "\nДля получения определенной записи"

                    self.send_message(message.chat.id, message_text, reply_markup=self.sending_markup)

                elif int(message.text.lower()) in self.recordIds and self.SelectedThemePosition:

                    # Создание подключения к базе данных, чтобы получить доступ к записям определенной темы

                    sql_con = sql.connect(
                        os.path.abspath(os.path.dirname(sys.argv[0])) + "\\Database\\" + "Vk_group_archive.sqlite3")
                    sql_cursor = sql_con.cursor()

                    sql_cursor.execute("SELECT arc.Theme, arc.Link, arc.Message FROM Archive arc WHERE arc.RecordID = {0}".format(message.text))

                    self.themed_record = sql_cursor.fetchall()

                    sql_con.close()

                    # Формирование ответа пользователю, вывод необходимых данных касательно искомой записи

                    record_message = f"Запись:\n" \
                                     f"Тема примера - {self.themed_record[0][0]};\n\n" \
                                     f"Ссылка на видео - {self.themed_record[0][1]}\n\n"
                    subtitles = self.themed_record[0][2]

                    subtitles = subtitles.replace('\n', ' ')
                    record_message += f"""Субтитры - {subtitles} \n\n""".replace('\n', ' ')

                    self.send_message(message.chat.id, record_message)

                    # Возврат в исходную позицию

                    self.send_message(message.chat.id, "Данный telegram-бот предназначен для работы с архивом"
                                                       "английских видео-материалов\n")
                    self.send_message(message.chat.id, self.bot_message, reply_markup=self.sending_markup)

                    self.SelectedThemePosition = False

            else:
                self.send_message(message.chat.id, "Работа Telegram-бота была прекращена! "
                                                   "Попробуйте позже. Введите команду /start")

                self.stop_polling()

        # Функция обработчик команды /stop

        @self.message_handler(commands=["stop"])
        def stop_polling_bot(message):

            self.stop_polling()

        try:
            self.polling(none_stop=False)
        except Exception as e:
            pass


# Update Record GUI Window
# Класс обновления данных записи


class UpdateRecordGUI(tk.Toplevel):
    def __init__(self, treeview=None, selected_record_id=None):
        super(UpdateRecordGUI, self).__init__()

        # Задание интерфейса

        self.w_width, self.w_height = 425, 255

        self.s_width, self.s_height = self.winfo_screenwidth(), self.winfo_screenheight()

        self.geometry(
            f"{self.w_width}x{self.w_height}+{int((self.s_width - self.w_width) / 2)}+{int((self.s_height - self.w_height) / 2)}")

        self.title("Update record data in database")

        self.attributes("-topmost", True)
        self.focus()

        # Создание подключения к базе данных, чтобы получить названия всех уникальных тем

        sql_con = sql.connect(
            os.path.abspath(os.path.dirname(sys.argv[0])) + "\\Database\\" + "Vk_group_archive.sqlite3")
        sql_cursor = sql_con.cursor()

        sql_cursor.execute("SELECT * FROM Archive arc WHERE arc.RecordID={0}".format(selected_record_id))
        self.selected_record = sql_cursor.fetchall()

        sql_con.close()

        self.selected_record = self.selected_record[0]

        self.selected_record_id = selected_record_id

        self.Database_TreeView = treeview

        self.Database_TreeView.tag_configure("oddrow", background="#fff")
        self.Database_TreeView.tag_configure("evenrow", background="lightblue")

        self.Theme_lb = tk.Label(self, text="Theme: ")
        self.Theme_lb.grid(row=0, column=0, padx=5, pady=5, sticky="ne")

        self.Theme_entry = tk.Entry(self, width=55)
        self.Theme_entry.grid(row=0, column=1, padx=5, pady=5, sticky="wn")
        self.Theme_entry.delete(0, tk.END)
        self.Theme_entry.insert(0, self.selected_record[1])

        self.VideoLink_lb = tk.Label(self, text="Video Link: ")
        self.VideoLink_lb.grid(row=1, column=0, padx=5, pady=5, sticky="ne")

        self.VideoLink_entry = tk.Entry(self, width=55)
        self.VideoLink_entry.grid(row=1, column=1, padx=5, pady=5, sticky="nw")
        self.VideoLink_entry.delete(0, tk.END)
        self.VideoLink_entry.insert(0, self.selected_record[3])

        self.Message_lbFrame = tk.LabelFrame(self, text="Message", width=self.w_width - 10, height=150)
        self.Message_lbFrame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ne")

        self.Message_text = tk.Text(self.Message_lbFrame, width=38, height=7)
        self.Message_text.place(x=10, y=0, width=375, height=128)
        self.Message_text.delete("1.0", tk.END)
        self.Message_text.insert(tk.END, self.selected_record[2])

        self.Message_ScrollBar = tk.Scrollbar(self.Message_lbFrame, orient=tk.VERTICAL, command=self.Message_text.yview)
        self.Message_text["yscrollcommand"] = self.Message_ScrollBar.set

        self.Message_ScrollBar.place(x=self.w_width - 38, y=0, width=18, height=128)

        self.btn_frame = tk.Frame(self, width=50)
        self.btn_frame.grid(row=3, column=1, columnspan=1, padx=5, sticky="ne")

        self.submit_record_btn = tk.Button(self.btn_frame, text="Clear All", command=self.ClearAllFields)
        self.submit_record_btn.grid(row=0, column=0, columnspan=1, padx=5, sticky="e")

        self.submit_record_btn = tk.Button(self.btn_frame, text="Update Record", command=self.UpdateRecord)
        self.submit_record_btn.grid(row=0, column=1, columnspan=1, padx=0, sticky="e")

    # Функция очистки всех полей, срабатывает по нажатию на кнопку

    def ClearAllFields(self):
        self.withdraw()
        clear = mb.askyesno(title="Clear all fields", message="Are you sure you want to clear all fields?")

        self.update()
        self.deiconify()

        if clear:
            self.Theme_entry.delete(0, tk.END)
            self.VideoLink_entry.delete(0, tk.END)
            self.Message_text.delete("1.0", tk.END)
        else:
            return

    # Функция обновления данных записи, срабатывает по нажатию на кнопку

    def UpdateRecord(self):

        # Получение пути до текущего py или exe-файла
        current_path = os.path.abspath(os.path.dirname(sys.argv[0]))

        # Подгрузка файла базы данных

        sql_con = sql.connect(current_path + "\\Database\\" + "Vk_group_archive.sqlite3")
        sql_cursor = sql_con.cursor()

        # Обновление записи

        sql_cursor.execute(
            "UPDATE Archive SET Theme =?, Message=?, Link=?, CreationData=? WHERE RecordID = ?;",
            (str(self.Theme_entry.get()), str(self.Message_text.get("1.0", tk.END)),
             str(self.VideoLink_entry.get()), datetime.now(), self.selected_record[0])
        )

        sql_con.commit()

        # Удаление старой записи из интерфейса

        self.Database_TreeView.delete(self.Database_TreeView.selection()[0])

        sql_cursor.execute("SELECT * FROM Archive")
        data = sql_cursor.fetchall()
        id_counter = len(data)

        # Добавление новой записи в интерфейс

        if id_counter % 2:
            self.Database_TreeView.insert(parent="", index="end", iid=self.selected_record[0],
                                          value=(self.selected_record[0], data[-1][1], data[-1][2][:50] + '...',
                                                 data[-1][3], data[-1][4]), tags=("evenrow",))
        else:
            self.Database_TreeView.insert(parent="", index="end", iid=self.selected_record[0],
                                          value=(self.selected_record[0], data[-1][1], data[-1][2][:50] + '...',
                                                 data[-1][3], data[-1][4]), tags=("oddrow",))

        self.withdraw()

        mb.showinfo(title="Successful Operation", message="The record has been successfully updated!")

        del self


# New Record GUI Window
# Класс добавления новой записи в базу данных


class newRecordGUI(tk.Toplevel):
    def __init__(self, treeview=None):
        super(newRecordGUI, self).__init__()

        # Задание интерфейса

        self.w_width, self.w_height = 425, 255

        self.s_width, self.s_height = self.winfo_screenwidth(), self.winfo_screenheight()

        self.geometry(
            f"{self.w_width}x{self.w_height}+{int((self.s_width - self.w_width) / 2)}+{int((self.s_height - self.w_height) / 2)}")

        self.title("Create new record to the database")

        self.attributes("-topmost", True)
        self.focus()

        self.Database_TreeView = treeview

        self.Database_TreeView.tag_configure("oddrow", background="#fff")
        self.Database_TreeView.tag_configure("evenrow", background="lightblue")

        self.Theme_lb = tk.Label(self, text="Theme: ")
        self.Theme_lb.grid(row=0, column=0, padx=5, pady=5, sticky="ne")

        self.Theme_entry = tk.Entry(self, width=55)
        self.Theme_entry.grid(row=0, column=1, padx=5, pady=5, sticky="wn")

        self.VideoLink_lb = tk.Label(self, text="Video Link: ")
        self.VideoLink_lb.grid(row=1, column=0, padx=5, pady=5, sticky="ne")

        self.VideoLink_entry = tk.Entry(self, width=55)
        self.VideoLink_entry.grid(row=1, column=1, padx=5, pady=5, sticky="nw")

        self.Message_lbFrame = tk.LabelFrame(self, text="Message", width=self.w_width - 10, height=150)
        self.Message_lbFrame.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ne")

        self.Message_text = tk.Text(self.Message_lbFrame, width=38, height=7)
        self.Message_text.place(x=10, y=0, width=375, height=128)

        self.Message_ScrollBar = tk.Scrollbar(self.Message_lbFrame, orient=tk.VERTICAL, command=self.Message_text.yview)
        self.Message_text["yscrollcommand"] = self.Message_ScrollBar.set

        self.Message_ScrollBar.place(x=self.w_width - 38, y=0, width=18, height=128)

        self.btn_frame = tk.Frame(self, width=50)
        self.btn_frame.grid(row=3, column=1, columnspan=1, padx=5, sticky="ne")

        self.submit_record_btn = tk.Button(self.btn_frame, text="Clear All", command=self.ClearAllFields)
        self.submit_record_btn.grid(row=0, column=0, columnspan=1, padx=5, sticky="e")

        self.submit_record_btn = tk.Button(self.btn_frame, text="Save Record", command=self.AddRecord)
        self.submit_record_btn.grid(row=0, column=1, columnspan=1, padx=0, sticky="e")

    #  Очистка всех полей

    def ClearAllFields(self):
        self.withdraw()
        clear = mb.askyesno(title="Clear all fields", message="Are you sure you want to clear all fields?")

        self.update()
        self.deiconify()

        if clear:
            self.Theme_entry.delete(0, tk.END)
            self.VideoLink_entry.delete(0, tk.END)
            self.Message_text.delete("1.0", tk.END)
        else:
            return

    # Добавление новой записи

    def AddRecord(self):
        current_path = os.path.abspath(os.path.dirname(sys.argv[0]))
        sql_con = sql.connect(current_path + "\\Database\\" + "Vk_group_archive.sqlite3")
        sql_cursor = sql_con.cursor()

        sql_cursor.execute(
            "INSERT INTO" + "'Archive'" + "(Theme, Message, Link, CreationData) VALUES (?, ?, ?, ?);",
            (str(self.Theme_entry.get()), str(self.Message_text.get("1.0", tk.END)),
             str(self.VideoLink_entry.get()), datetime.now()))

        sql_con.commit()

        sql_cursor.execute("SELECT * FROM Archive")
        data = sql_cursor.fetchall()
        id_counter = len(data)

        if id_counter % 2:
            self.Database_TreeView.insert(parent="", index="end", iid=data[-1][0],
                                          value=(data[-1][0], data[-1][1], data[-1][2][:50] + '...',
                                                 data[-1][3], data[-1][4]), tags=("evenrow",))
        else:
            self.Database_TreeView.insert(parent="", index="end", iid=data[-1][0],
                                          value=(data[-1][0], data[-1][1], data[-1][2][:50] + '...',
                                                 data[-1][3], data[-1][4]), tags=("oddrow",))

        self.withdraw()

        mb.showinfo(title="Successful Operation", message="New record has been successfully added!")

        self.update()
        self.deiconify()

        self.Theme_entry.delete(0, tk.END)
        self.VideoLink_entry.delete(0, tk.END)
        self.Message_text.delete("1.0", tk.END)


# Main Gui Window
# Класс главного окна приложения

class GUI(tk.Tk):
    def __init__(self):
        super(GUI, self).__init__()

        # Формирования интерфейса

        self.w_width, self.w_height = 640, 480

        self.s_width, self.s_height = self.winfo_screenwidth(), self.winfo_screenheight()

        self.geometry(f"{self.w_width}x{self.w_height}+"
                      f"{int((self.s_width - self.w_width) / 2)}+"
                      f"{int((self.s_height - self.w_height) / 2)}")

        self.title("Vk ChatBot - English group archive v1.0.1 by IgorVeshkin")

        self.resizable(False, False)

        # Adding widgets in window

        self.Database_Frame = tk.Frame(self)
        self.Database_Frame.place(x=10, y=10, width=self.w_width - 10, height=self.w_height / 2 + 20)

        self.Database_TreeView = ttk.Treeview(self.Database_Frame)

        self.Database_TreeView["column"] = ("ID", "Theme", "Message", "Video Link", "Creation Data")

        self.Database_TreeView.column("#0", width=0, stretch=tk.NO)
        self.Database_TreeView.column("ID", minwidth=20, width=40, anchor=tk.CENTER)
        self.Database_TreeView.column("Theme", minwidth=50, width=160, anchor=tk.CENTER)
        self.Database_TreeView.column("Message", minwidth=140, width=240, anchor=tk.CENTER)
        self.Database_TreeView.column("Video Link", minwidth=140, width=200, anchor="nw")
        self.Database_TreeView.column("Creation Data", minwidth=140, width=160, anchor=tk.CENTER)

        self.Database_TreeView.heading("ID", text="ID")
        self.Database_TreeView.heading("Theme", text="Theme")
        self.Database_TreeView.heading("Message", text="Message")
        self.Database_TreeView.heading("Video Link", text="Video Link")
        self.Database_TreeView.heading("Creation Data", text="Creation Data")

        self.Database_TreeView.place(relwidth=0.95, relheight=0.93)

        style = ttk.Style()
        style.configure("Treeview.Heading", rowheight=14)
        style.configure("Treeview", rowheight=30,
                        background="#d3d3d3",
                        foreground="black",
                        fieldbackground="#d3d3d3")

        style.map("Treeview", background=[("selected", "lightgray")], foreground=[("selected", 'black')])

        # Variables to store data of current record of treeview

        self.tree_item = None
        self.tree_cur_data = None
        self.previous_item = None
        self.cur_item = None

        self.Database_TreeView.bind("<Button-1>", self.treeview_onmouse_pressed)

        self.TreeView_ScrollBar = tk.Scrollbar(self.Database_Frame, command=self.Database_TreeView.yview)

        self.TreeView_ScrollBar_x = tk.Scrollbar(self.Database_Frame, orient=tk.HORIZONTAL,
                                                 command=self.Database_TreeView.xview)

        self.Database_TreeView['yscrollcommand'] = self.TreeView_ScrollBar.set

        self.Database_TreeView['xscrollcommand'] = self.TreeView_ScrollBar_x.set

        self.TreeView_ScrollBar.place(relx=0.952, y=0, width=15, relheight=0.95)
        self.TreeView_ScrollBar_x.place(x=0, rely=0.93, relwidth=0.95, height=15)

        # Adding Menu LabelFrame

        self.Lb_Frame = tk.LabelFrame(self, text="Menu", labelanchor="nw")
        self.Lb_Frame.place(x=10, y=self.w_height / 2 + 30, width=self.w_width - 20, height=self.w_height / 2 - 40)

        # Adding widgets to Menu Frame

        self.select_table_combobox = ttk.Combobox(self.Lb_Frame, values=("Main_Table", "Not_Main_Table"), width=21)
        self.select_table_combobox.grid(row=0, column=0, sticky="ne", padx=15, pady=10)
        self.select_table_combobox.set(self.select_table_combobox["values"][0])
        self.select_table_combobox.bind("<Key>", "break")

        self.add_record_btn = tk.Button(self.Lb_Frame, text="Добавить запись", width=20, command=lambda:
        newRecordGUI(treeview=self.Database_TreeView))

        self.add_record_btn.grid(row=1, column=0, sticky="ne", padx=15, pady=10)

        self.delete_record_btn = tk.Button(self.Lb_Frame, text="Удалить текущую запись", width=20,
                                           command=self.delete_current_record)
        self.delete_record_btn.grid(row=2, column=0, sticky="ne", padx=15, pady=10)
        self.delete_record_btn["state"] = tk.DISABLED

        self.update_record_btn = tk.Button(self.Lb_Frame, text="Отредактировать запись", width=20,
                                           command=self.enter_update_window)
        self.update_record_btn.grid(row=3, column=0, sticky="ne", padx=15, pady=10)
        self.update_record_btn["state"] = tk.DISABLED

        # Внедрение элементов управления Telegram-ботом

        self.TelegramBot_status_label = tk.Label(self.Lb_Frame, text="TelegramBot status:")
        self.TelegramBot_status_label.config(font=("Courier", 14))
        self.TelegramBot_status_label.grid(row=0, column=1, sticky="nw", padx=0, pady=10)

        self.TelegramBot_status_changeable_label = tk.Label(self.Lb_Frame, text="unactive")
        self.TelegramBot_status_changeable_label.config(font=("Courier", 14), fg="red")
        self.TelegramBot_status_changeable_label.grid(row=0, column=2, sticky="nw", padx=0, pady=10)

        self.TelegramBot_activation_btn = tk.Button(self.Lb_Frame, text="Запустить Telegram-бота", width=20,
                                                    command=self.start_Telebot)
        self.TelegramBot_activation_btn.grid(row=1, column=1, sticky="nw", padx=0, pady=10)

        # Переключатель для Telebot-a

        self.Telebot_active = False

        # Переменная для хранения Telegram-бота

        self.TelegramBot = None

        # Добавление данных в таблицу интерфейса программы

        self.current_path = os.path.abspath(os.path.dirname(sys.argv[0]))

        if not os.path.isdir(self.current_path + "\\Database\\"):
            os.mkdir(self.current_path + "\\Database\\")

        sql_con = sql.connect(self.current_path + "\\Database\\" + "Vk_group_archive.sqlite3")
        sql_cursor = sql_con.cursor()

        sql_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Archive';")
        tb_name = sql_cursor.fetchall()

        # Если в базе данных отсутствует нужная для хранения данных таблица, то она создасться

        if len(tb_name) == 0:
            sql_cursor.execute("""
                CREATE TABLE Archive (
                    RecordID INTEGER PRIMARY KEY autoincrement,
                    Theme varchar(255),
                    Message text,
                    Link varchar(255),
                    CreationData TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """)

        sql_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

        tables_list = sql_cursor.fetchall()

        self.select_table_combobox["values"] = tables_list[:-1]

        self.select_table_combobox.set(self.select_table_combobox["values"][0])

        sql_cursor.execute("SELECT * FROM Archive")

        self.data = sql_cursor.fetchall()

        sql_cursor.close()

        counter = 0

        self.Database_TreeView.tag_configure("oddrow", background="#fff")
        self.Database_TreeView.tag_configure("evenrow", background="lightblue")

        for record in self.data:
            if counter % 2 == 0:
                self.Database_TreeView.insert(parent="", index="end", iid=counter,
                                              value=(record[0], record[1], record[2][:50],
                                                     record[3], record[4]), tags=("evenrow",))
            else:
                self.Database_TreeView.insert(parent="", index="end", iid=counter,
                                              value=(record[0], record[1], record[2][:50], record[3], record[4]),
                                              tags=("oddrow",))

            counter += 1

        self.popup_menu = tk.Menu(self,
                                  tearoff=0)

        self.popup_menu.add_command(label="Копировать поле Theme",
                                    command=lambda: self.copy_record_data(field="Theme"))

        self.popup_menu.add_command(label="Копировать поле Message",
                                    command=lambda: self.copy_record_data(field="Message"))
        self.popup_menu.add_separator()
        self.popup_menu.add_command(label="Копировать поле Video Link",
                                    command=lambda: self.copy_record_data(field="Video Link"))

        self.popup_menu.add_command(label="Копировать поле Creation Data",
                                    command=lambda: self.copy_record_data(field="Creation Data"))

        self.Database_TreeView.bind("<Button-3>", self.show_popup)

        self.mainloop()

    # Функция получения состояния телеграм-бота

    def get_bot_active_state(self):
        return self.Telebot_active

    # Создание телеграм-бота

    def bot_creation(self, token, gui):
            self.TelegramBot = EnglishArchiveBot(given_token=token,
                                                 window_gui=gui)

    # Запуск Telegram-Бота

    def start_Telebot(self):
        self.Telebot_active = not self.Telebot_active
        lbl_color, lbl_text, btn_text = "", "", ""

        if self.Telebot_active:

            BotThread = thread.Thread(target=self.bot_creation, args=(

                "5680683777:AAFnqeLZI0--UgxRvpQrybGIdaHyXK89ecE",
                self,
            ),
                                      daemon=True)

            BotThread.start()

            lbl_color, lbl_text, btn_text = "green", "active", "Отключить Telegram-бота"

        else:

            lbl_color, lbl_text, btn_text = "red", "inactive", "Запустить Telegram-бота"

        self.TelegramBot_status_changeable_label.config(fg=lbl_color, text=lbl_text)
        self.TelegramBot_activation_btn.config(text=btn_text)

    # Функция запуска редактирования записи

    def enter_update_window(self):
        if len(self.Database_TreeView.selection()) > 1:
            mb.showwarning(title="Внимание", message="Редактирование нескольких записей одновременно невозможно")
        else:
            UpdateRecordGUI(treeview=self.Database_TreeView, selected_record_id=self.tree_cur_data[0])

    # Функция копирования данных записи из интерфейса программы в буфер обмена

    def copy_record_data(self, field=""):
        self.clipboard_clear()

        sql_con = sql.connect(self.current_path + "\\Database\\" + "Vk_group_archive.sqlite3")
        sql_cursor = sql_con.cursor()

        element_to_copy_from = self.Database_TreeView.selection()[0]
        tree_current_data_to_copy = self.Database_TreeView.item(element_to_copy_from, "values")

        sql_cursor.execute("SELECT * FROM Archive WHERE RecordID={0}".format(tree_current_data_to_copy[0]))
        current_record = sql_cursor.fetchall()

        sql_con.close()

        if field == "Theme":
            self.clipboard_append(current_record[0][1])
        if field == "Message":
            message = f"""{current_record[0][2]}""".replace("\\n", ' ')
            self.clipboard_append(message)
        if field == "Video Link":
            self.clipboard_append(current_record[0][3])
        if field == "Creation Data":
            self.clipboard_append(current_record[0][4])

        self.update()

    # Show popup menu
    # Отображение выпадающего мени при нажатии на элемент таблицы правой кнопкой мыши

    def show_popup(self, event):

        self.tree_item = self.Database_TreeView.identify_row(event.y)
        self.tree_cur_data = self.Database_TreeView.item(self.tree_item, "values")

        if self.tree_item:
            try:
                selection = self.Database_TreeView.selection()
                self.Database_TreeView.selection_set(self.tree_item)

                self.delete_record_btn["state"] = tk.NORMAL
                self.update_record_btn["state"] = tk.NORMAL

                self.popup_menu.tk_popup(event.x_root,
                                         event.y_root)

            finally:
                self.popup_menu.grab_release()

        else:
            self.delete_record_btn["state"] = tk.DISABLED
            self.update_record_btn["state"] = tk.DISABLED
            tk.messagebox.showwarning(title="Внимание", message="Выберите запись перед открытием контексного меню")

    # Функция изменения интерфейса при выборе элемента из таблицы

    def treeview_onmouse_pressed(self, event):
        self.previous_item = None

        try:
            self.tree_item = self.Database_TreeView.identify_row(event.y)
            self.tree_cur_data = self.Database_TreeView.item(self.tree_item, "values")

        except IndexError as error:

            for row in self.Database_TreeView.get_children():
                self.Database_TreeView.delete(row)

            counter = 0

            sql_con = sql.connect(self.current_path + "\\Database\\" + "Vk_group_archive.sqlite3")
            sql_cursor = sql_con.cursor()

            sql_cursor.execute("SELECT * FROM Archive")

            self.data = sql_cursor.fetchall()

            sql_cursor.close()

            for record in self.data:
                if counter % 2 == 0:
                    self.Database_TreeView.insert(parent="", index="end", iid=counter,
                                                  value=(record[0], record[1], record[2][:50],
                                                         record[3], record[4]), tags=("evenrow",))
                else:
                    self.Database_TreeView.insert(parent="", index="end", iid=counter,
                                                  value=(record[0], record[1], record[2][:50], record[3], record[4]),
                                                  tags=("oddrow",))

                counter += 1

        if self.tree_item:
            self.previous_item = self.tree_item
            self.delete_record_btn["state"] = tk.NORMAL
            self.update_record_btn["state"] = tk.NORMAL
        else:
            if self.previous_item:
                self.tree_item = self.previous_item

            self.delete_record_btn["state"] = tk.DISABLED
            self.update_record_btn["state"] = tk.DISABLED

    # Функция удаления текущей выбранной записи записи

    def delete_current_record(self):

        self.cur_item = self.Database_TreeView.selection()

        if self.cur_item:

            sql_con = sql.connect(self.current_path + "\\Database\\" + "Vk_group_archive.sqlite3")
            sql_cursor = sql_con.cursor()

            # Deleting from database

            tree_item = self.Database_TreeView.selection()

            for item2 in tree_item:
                tree_current_data = self.Database_TreeView.item(item2, "values")

                sql_cursor.execute("DELETE FROM Archive WHERE RecordID={0}".format(tree_current_data[0]))
                sql_con.commit()

            # Deleting from treeview

            for item in self.cur_item:
                self.Database_TreeView.delete(item)

            sql_con.close()

            self.delete_record_btn["state"] = tk.DISABLED
            self.update_record_btn["state"] = tk.DISABLED
            self.tree_item = None
            self.tree_cur_data = None


# Главная функция - main


def main():
    App = GUI()


# Запуск функции main


if __name__ == "__main__":
    main()

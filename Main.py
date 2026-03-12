import csv
import os
import sys
import time

from PyQt5 import uic
from PyQt5.QtGui import QPixmap, QMovie, QIcon
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *
import sqlite3
from pydub import AudioSegment
from itertools import islice
import datetime


from form.dialog import CustomDialog


SongList = {}


class Music_Player(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('images/icon.png'))
        uic.loadUi('form/project_player.ui', self)
        self.counter = 0
        self.player = QMediaPlayer()
        self.music_plays_flag = False
        self.initUI()

    def initUI(self):
        self.start_playing.clicked.connect(self.playing_music)
        self.next_song.clicked.connect(self.counter_up)
        self.to_music_list.clicked.connect(self.open_music_list)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.PlayMode)
        self.timer.start(1000)
        self.horizontalSlider.sliderMoved[int].connect(self.slider_scrolled)
        self.pic = QPixmap('images/city.jpeg')
        self.image_label.setPixmap(self.pic.scaledToWidth(450))

    def PlayMode(self):
        if self.music_plays_flag:
            self.horizontalSlider.setMinimum(0)
            self.horizontalSlider.setMaximum(self.player.duration())
            self.horizontalSlider.setValue(self.horizontalSlider.value() + 1000)
        self.start.setText(time.strftime('%M:%S', time.localtime(self.player.position() / 1000)))
        self.end.setText(time.strftime('%M:%S', time.localtime(self.player.duration() / 1000)))

        if self.player.position() == self.player.duration() and self.autoplaying.isChecked() and \
                self.player.duration() != 0:
            self.counter_up()

    def slider_scrolled(self):
        self.player.setPosition(self.horizontalSlider.value())
        self.start.setText(time.strftime('%M:%S', time.localtime(self.player.position() / 1000)))

    def counter_up(self):
        if self.counter >= len(SongList) - 1:
            self.counter = 0
        else:
            self.counter += 1
        self.player = QMediaPlayer()
        self.horizontalSlider.setValue(0)
        self.music_plays_flag = False
        self.playing_music()

    def open_music_list(self):
        ex.close_player()
        ex.open_music_list()

    def playing_music(self, Song=False):
        if Song is False:
            if len(SongList) == 0:
                self.open_music_list()
            else:
                if not self.player.isAudioAvailable():
                    self.mp3_url = SongList[list(SongList.keys())[self.counter]]
                    file_info = QFileInfo(self.mp3_url)
                    url = QUrl.fromLocalFile(file_info.absoluteFilePath())
                    content = QMediaContent(url)
                    print(SongList)
                    self.player.setMedia(content)
                    self.now_playing.setText(f'Сейчас играет: {list(SongList.keys())[self.counter]}')
                    ex.show_current_song()
                    ex.HistoryInsert((list(SongList.keys())[self.counter], self.mp3_url,
                                      str(datetime.datetime.now())[:-7]))

                if not self.music_plays_flag:
                    self.music_plays_flag = True
                    self.player.play()
                    self.start_playing.setText('Пауза')
                elif self.music_plays_flag:
                    self.music_plays_flag = False
                    self.player.pause()
                    self.start_playing.setText('Старт')

        else:
            file_info = QFileInfo(Song[0])
            url = QUrl.fromLocalFile(file_info.absoluteFilePath())
            content = QMediaContent(url)
            self.player.setMedia(content)
            self.music_plays_flag = True
            self.player.play()
            self.start_playing.setText('Пауза')
            ex.show_current_song(Song[1])
            ex.HistoryInsert((Song[1], Song[0], str(datetime.datetime.now())[:-7]))

    def getSongName(self):
        return list(SongList.keys())[self.counter]

    def setCoolImage(self, path):
        if path[-4:] != '.gif':
            self.jevil_place.clear()
            pic = QPixmap(path)
            self.image_label.setPixmap(pic.scaledToWidth(450))
        else:
            self.image_label.clear()
            image = QMovie(path)
            image.setScaledSize(QSize(200, 200))
            self.jevil_place.setMovie(image)
            image.start()


class Music_list(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('form/project_audio_list.ui', self)
        self.setWindowIcon(QIcon('images/icon.png'))
        self.initUI()

    def initUI(self):
        self.player = QMediaPlayer()
        self.listWidget.itemDoubleClicked.connect(self.MouseDoubleClick)
        self.add_audio.clicked.connect(self.audio_add)
        self.add_couple_of_audio.clicked.connect(self.audio_add)
        self.del_audio.clicked.connect(self.audio_del)
        self.redact_files.clicked.connect(self.redacting_music)
        self.save_playlist.clicked.connect(self.SavePlaylist)
        self.open_playlist.clicked.connect(self.OpenPlaylist)

    def audio_add(self, redacted_file_path=False):
        if redacted_file_path is False:
            if self.sender().text() == 'Добавить аудио-файл':
                filename, ok = QFileDialog.getOpenFileName(
                    self,
                    "Выберите файл",
                    "D:\\",
                    "Музыка (*.mp3 *.WAV)"
                )
                if '.mp3' in filename or '.wav' in filename:
                    song = filename.split('/')[-1]
                    if song not in list(SongList.keys()):
                        SongList[song] = filename
                        self.listWidget.addItem(song)
            else:
                directory = QFileDialog.getExistingDirectory(
                    self,
                    "Выбрать папку с музыкой",
                    "D:\\",
                    QFileDialog.ShowDirsOnly
                )
                if len(directory) == 0:
                    return
                for filename in os.listdir(directory):
                    if '.mp3' in filename or '.wav' in filename:
                        if filename not in list(SongList.keys()):
                            songpath = directory + '/' + filename
                            SongList[filename] = songpath
                            self.listWidget.addItem(filename)
            self.listWidget.setCurrentRow(0)
        else:
            song = redacted_file_path.split('/')[-1]
            if song not in list(SongList.keys()):
                SongList[song] = redacted_file_path
                self.listWidget.addItem(song)

    def audio_del(self):
        if len(SongList) == 0:
            QMessageBox.about(self, "Ошибка!", "Нечего удалять!")
            return
        del SongList[next(islice(SongList, self.listWidget.currentRow(), None))]
        self.listWidget.takeItem(self.listWidget.currentRow())

    def MouseDoubleClick(self):
        song_name = self.listWidget.selectedItems()[0].text()
        self.mp3_url = SongList[song_name]
        ex.MouseDoubleClickSong((self.mp3_url, song_name))

    def redacting_music(self):
        if len(SongList) == 0:
            QMessageBox.about(self, "Ошибка!", "Выберите файл для редактирования.")
            return
        song_name = self.listWidget.selectedItems()[0].text()
        self.redactor = Redactor(song_name)
        self.redactor.show()

    def SavePlaylist(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "Выбрать папку с музыкой",
            "D:\\",
            QFileDialog.ShowDirsOnly
        )
        if len(directory) == 0:
            return
        playlist = []
        for i in SongList.items():
            songs = {}
            songs['name'] = i[0]
            songs['path'] = i[1]
            playlist.append(songs)
        name = ''
        while name == '':
            name, done = QInputDialog.getText(
                self, 'Введите название плейлиста', 'Введите название плейлиста:')
            if done is False:
                return
            if name == '':
                QMessageBox.about(self, "Ошибка!", "Введите название плейлиста.")
        with open(f'{directory}/{name}.csv', 'w', newline='', encoding="utf8") as f:
            writer = csv.DictWriter(
                f, fieldnames=list(playlist[0].keys()),
                delimiter=';', quoting=csv.QUOTE_NONNUMERIC)
            writer.writeheader()
            for d in playlist:
                writer.writerow(d)

    def OpenPlaylist(self):
        path = QFileDialog.getOpenFileName(
            self,
            "Выберите плейлист",
            "D:\\",
            "Плейлист (*.csv)"
        )[0]
        if len(path) == 0:
            return
        question = CustomDialog()
        if question.exec():
            pass
        else:
            self.listWidget.clear()
            SongList.clear()
        with open(path, encoding="utf8") as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';', quotechar='"')
            for i in reader:
                if i['name'] not in list(SongList.keys()):
                    SongList[i['name']] = i['path']
                    self.listWidget.addItem(i['name'])


class Redactor(QWidget):
    def __init__(self, audio_file):
        super().__init__()
        self.audio_file = audio_file
        uic.loadUi('form/project_redactor.ui', self)
        self.setWindowIcon(QIcon('images/icon.png'))
        self.initUI()

    def initUI(self):
        self.title.setText(f'Сейчас редактируется: {self.audio_file}')
        self.player = QMediaPlayer()
        self.player1 = QMediaPlayer()
        self.mp3_url = SongList[self.audio_file]
        file_info = QFileInfo(self.mp3_url)
        url = QUrl.fromLocalFile(file_info.absoluteFilePath())
        content = QMediaContent(url)
        self.player.setMedia(content)
        self.player1.setMedia(content)
        self.player.durationChanged.connect(self.check_duration)
        self.start.sliderMoved[int].connect(self.start_slider_scrolled, 1)
        self.end.sliderMoved[int].connect(self.end_slider_scrolled, 2)
        self.done.clicked.connect(self.save_file)
        self.save_path.setText('D:/')
        self.loud_changer.setRange(-100, 100)
        self.done_loud_and_speed.clicked.connect(self.save_file)
        self.merger.clicked.connect(self.save_file)


    def start_slider_scrolled(self):
        self.player.setPosition(self.start.value())
        self.start_timer.setText(time.strftime('%M:%S', time.localtime(self.player.position() / 1000)))

    def end_slider_scrolled(self):
        self.player1.setPosition(self.end.value())
        self.end_timer.setText(time.strftime('%M:%S', time.localtime(self.player1.position() / 1000)))

    def check_duration(self, d):
        if d > 0:
            self.start.setMinimum(0)
            self.start.setMaximum(self.player.duration())
            self.end.setMinimum(0)
            self.end.setMaximum(self.player.duration())

    def save_file(self):
        if self.save_path.text() == '':
            QMessageBox.about(self, "Ошибка!", "Путь сохранения файла не введён.")
            return
        if self.new_file_name.text() == '':
            QMessageBox.about(self, "Ошибка!", "Название файла не введёно.")
            return
        if self.sender().text() == 'Сохранить обрезанный файл':
            redacting_file = AudioSegment.from_file(SongList[self.audio_file])
            trimmed_file = redacting_file[self.start.value():self.end.value()]
            trimmed_file.export(self.save_path.text() + self.new_file_name.text(), format="mp3")
            if self.add_to_playlist.isChecked():
                ex.AddRedactedFile(self.save_path.text() + self.new_file_name.text())
        elif self.sender().text() == 'Сохранить файл с громкостью':
            redacting_file = AudioSegment.from_file(SongList[self.audio_file])
            louder_file = redacting_file + self.loud_changer.value()
            louder_file.export(self.save_path.text() + self.new_file_name.text(), format="mp3")
            if self.add_to_playlist.isChecked():
                ex.AddRedactedFile(self.save_path.text() + self.new_file_name.text())
        elif self.sender().text() == 'Склеить':
            redacting_file = AudioSegment.from_file(SongList[self.audio_file])
            if self.second_file_name.text() not in list(SongList.keys()):
                QMessageBox.about(self, "Ошибка!", "Такого файла нет в плейлисте.")
                return
            file_2 = AudioSegment.from_file(SongList[self.second_file_name.text()])
            merge_file = redacting_file + file_2
            merge_file.export(self.save_path.text() + self.new_file_name.text(), format="mp3")
            if self.add_to_playlist.isChecked():
                ex.AddRedactedFile(self.save_path.text() + self.new_file_name.text())


class Settings(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('form/project_settings.ui', self)
        self.setWindowIcon(QIcon('images/icon.png'))
        self.image_list = {'city.jpeg': 'images/city.jpeg',
                           'party.png': 'images/party.png',
                           'rainy.png': 'images/rainy.png'}
        self.current_image = 'city.jpeg'
        self.picture_list.addItem('city.jpeg')
        self.picture_list.addItem('party.png')
        self.picture_list.addItem('rainy.png')
        self.initUI()

    def initUI(self):
        self.add_button.clicked.connect(self.add_image)
        self.choose_image.clicked.connect(self.set_current_image)
        self.picture_list.itemDoubleClicked.connect(self.set_current_image)
        self.del_button.clicked.connect(self.delete_image)

    def add_image(self):
        path = QFileDialog.getOpenFileName(
            self,
            "Выберите картинку",
            "D:\\",
            "Картинки (*.png *.jpg *.jpeg)"
        )[0]
        if len(path) == 0:
            return
        filename = path.split('/')[-1]
        if filename not in list(self.image_list.keys()):
            self.image_list[filename] = path
            self.picture_list.addItem(filename)

    def set_current_image(self):
        self.current_image = self.picture_list.selectedItems()[0].text()
        self.current_image_label.setText(f'Сейчас выбрано: {self.current_image}')
        if self.current_image[-4:] != '.gif':
            image = QPixmap(self.image_list[self.current_image])
            self.preview.setPixmap(image.scaledToWidth(200))
        else:
            image = QMovie(self.image_list[self.current_image])
            image.setScaledSize(QSize(200, 200))
            self.preview.setMovie(image)
            image.start()
        ex.SetImage(self.image_list[self.current_image])

    def delete_image(self):
        if len(SongList) == 0:
            QMessageBox.about(self, "Ошибка!", "Нечего удалять!")
            return
        del self.image_list[next(islice(self.image_list, self.picture_list.currentRow(), None))]
        self.picture_list.takeItem(self.picture_list.currentRow())


class History(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('form/project_hystory.ui', self)
        self.setWindowIcon(QIcon('images/icon.png'))
        self.initUI()

    def initUI(self):
        self.refresh.clicked.connect(self.download_history)
        self.del_history.clicked.connect(self.delete_history)

    def download_history(self):
        res = ex.GiveHistory()
        new_res = []
        for i in res:
            new_res.append((i[1], i[2], i[3]))
        new_res.reverse()
        title = ['Название', "Путь", "Дата и время"]
        self.history_widget.setColumnCount(3)
        self.history_widget.setRowCount(0)
        self.history_widget.setHorizontalHeaderLabels(title)
        for i, row in enumerate(new_res):
            self.history_widget.setRowCount(
                self.history_widget.rowCount() + 1)
            for j, elem in enumerate(row):
                self.history_widget.setItem(
                    i, j, QTableWidgetItem(str(elem)))

    def delete_history(self):
        ex.DeleteHistory()


class MusicApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('form/project_main.ui', self)
        self.setWindowIcon(QIcon('images/icon.png'))
        self.initUI()
        self.SongList = []
        self.music_widget = Music_list()
        self.player_widget = Music_Player()
        self.settings_widget = Settings()
        self.history_window = History()
        self.history = sqlite3.connect('files/history.db')
        cursor = self.history.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
        orderid INT PRIMARY KEY,
        name TEXT NOT NULL,
        path TEXT NOT NULL,
        data TEXT NOT NULL
        )
        ''')
        self.history.commit()
        self.history.close()

    def initUI(self):
        self.list_of_music.clicked.connect(self.open_music_list)
        self.play_button.clicked.connect(self.open_player)
        self.settings.clicked.connect(self.open_settings)
        self.history_button.clicked.connect(self.open_history)

    def open_music_list(self):
        self.music_widget.show()

    def open_player(self):
        self.player_widget.show()

    def close_music_list(self):
        self.music_widget.hide()

    def close_player(self):
        self.player_widget.hide()

    def open_settings(self):
        self.settings_widget.show()

    def open_history(self):
        self.history_window.show()

    def show_current_song(self, dc=False):
        if dc is False:
            songname = self.player_widget.getSongName()
            self.current_song.setText(f'Сейчас играет: {songname}')
        else:
            songname = dc
            self.current_song.setText(f'Сейчас играет: {songname}')

    def MouseDoubleClickSong(self, songpath):
        self.player_widget.playing_music(songpath)

    def AddRedactedFile(self, songpath):
        self.music_widget.audio_add(songpath)

    def SetImage(self, path):
        self.player_widget.setCoolImage(path)

    def HistoryInsert(self, new_data):
        self.history = sqlite3.connect('files/history.db')
        cursor = self.history.cursor()
        cursor.execute('INSERT INTO Users (name, path, data) VALUES (?, ?, ?)', new_data)
        self.history.commit()
        self.history.close()

    def GiveHistory(self):
        self.history = sqlite3.connect('files/history.db')
        cursor = self.history.cursor()
        res = cursor.execute('select * from Users').fetchall()
        return res

    def DeleteHistory(self):
        self.history = sqlite3.connect('files/history.db')
        cursor = self.history.cursor()
        cursor.execute("DELETE FROM Users")
        self.history.commit()
        self.history.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MusicApp()
    ex.show()
    sys.exit(app.exec())
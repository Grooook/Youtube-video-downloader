import pytube as pt
from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.uic import loadUi
import PySimpleGUIQt as sg
import sys
import datetime
import math
import urllib
import os


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


class Worker_download(QtCore.QRunnable):
    def __init__(self, video, audio, full_path):
        super(Worker_download, self).__init__()
        self.video = video
        self.audio = audio
        self.full_path = full_path

    @pyqtSlot()
    def run(self):
        try:
            path, filename = os.path.split(self.full_path)
            path = path[8:]
            if os.path.exists(filename):
                os.remove(filename)
            if self.video.is_progressive:
                self.video.download(output_path=path, filename='[' + str(self.video.resolution) + ']' + filename)
            else:
                self.video.download(filename='video_systems')
                self.audio.download(filename='audio_systems')
                if os.path.exists('merge.bat'):
                    os.remove('merge.bat')
                myBat = open(r'merge.bat', 'w+')
                myBat.write('echo y | ffmpeg -i video_systems.mp4 -i audio_systems.webm -c:v copy -c:a copy %s'
                            % (path + '/[' + str(self.video.resolution) + ']' + filename))
                myBat.close()
                os.system('merge.bat')

            if os.path.exists('video_systems.mp4'):
                os.remove('video_systems.mp4')
            if os.path.exists('audio_systems.webm'):
                os.remove('audio_systems.webm')
        except Exception as e:
            print(e)


class Youtube_GUI(QtWidgets.QMainWindow):
    resized = QtCore.pyqtSignal()

    def __init__(self, request='', main_page_show=True):
        super(Youtube_GUI, self).__init__()
        loadUi('gui elements/GUI.ui', self)
        self.setWindowTitle("Youtube video downloader")
        self.setWindowIcon(QtGui.QIcon('gui elements/icon.jpg'))
        self.threadpool = QtCore.QThreadPool()
        self.pb_find.clicked.connect(self.find_video)
        self.find_counter = 0

    def keyPressEvent(self, e):
        if e.key() == 16777220 or e.key() == 16777221:  # 1677722[0,1] seems to be enter
            self.find_video()

    def resizeEvent(self, event):
        self.resized.emit()
        if 'lbl_img' in self.__dict__:
            self.lbl_img.setPixmap(
                self.pixmap.scaled(int(self.size().width() / 2), int(self.size().height() / 2),
                                   QtCore.Qt.KeepAspectRatio,
                                   QtCore.Qt.SmoothTransformation))

        return super(Youtube_GUI, self).resizeEvent(event)

    def get_resolution(self, obj):
        return int(obj.resolution[:-1])

    def get_kpbs(self, obj):
        return int(obj.abr[:-4])

    def show_progress_bar(self, stream, _chunk, bytes_remaining):
        self.pbar.setValue(int(round((1 - bytes_remaining / stream.filesize) * 100, 3)))

    def find_video(self):
        url = self.url.text()
        try:
            yt = pt.YouTube(url)
            yt.register_on_progress_callback(self.show_progress_bar)
            videos = yt.streams.filter(file_extension='mp4')
            result_videos = list()
            for video in videos:
                stream_exists = False
                for i in result_videos:
                    if video.resolution == i.resolution or video.resolution == None:
                        stream_exists = True
                        break
                if not stream_exists:
                    result_videos.append(video)
            result_streams = sorted(result_videos, key=self.get_resolution)
            preview = yt.thumbnail_url
            urllib.request.urlretrieve(preview, 'gui elements/preview.jpg')

            audios = yt.streams.filter(only_audio=True)
            audios = sorted(audios, key=self.get_kpbs)
            self.draw_content(yt, result_streams, audios)
            self.find_counter += 1
            self.error_log.setText('')

        except Exception as e:
            self.error_log.setText('Not found')
            print(e)

    def download(self, video, audio):
        try:
            QtWidgets.QApplication.processEvents()
            dlg = QtWidgets.QFileDialog(directory='video.mp4', caption='Save as' )
            dlg.setDirectory("Downloads")
            dlg.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
            dlg.setOptions(QtWidgets.QFileDialog.ShowDirsOnly)
            dlg.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)

            if dlg.exec_():
                if dlg.result() == 1:
                    full_path = dlg.selectedUrls()[0].toString()
                    if not full_path.endswith('.mp4'):
                        full_path += '.mp4'
                    try:
                        self.pbar.hide()
                    except:
                        pass
                    self.pbar = QtWidgets.QProgressBar(self)
                    self.pbar.setGeometry(30, 40, 200, 25)
                    self.gridLayout.addWidget(self.pbar, 8, 0, 1, 1)
                    self.pbar.setValue(0)
                    worker = Worker_download(video, audio, full_path)
                    self.threadpool.start(worker)
        except Exception as e:
            print(e)

    def draw_content(self, yt, videos, audios):
        if self.find_counter > 0:
            self.lbl_img.hide()
            self.lbl_title.hide()
            self.lbl_date.hide()
            self.lbl_len.hide()
            self.lbl_author.hide()
            self.combobox.hide()
        self.lbl_img = QtWidgets.QLabel(self)
        self.pixmap = QtGui.QPixmap('gui elements/preview.jpg')
        self.lbl_img.setMinimumSize(400, 250)
        self.lbl_img.setPixmap(
            self.pixmap.scaled(int(self.size().width() / 2), int(self.size().height() / 2), QtCore.Qt.KeepAspectRatio,
                               QtCore.Qt.SmoothTransformation))
        self.setMinimumSize(600, 500)
        self.gridLayout.addWidget(self.lbl_img, 3, 0, 1, 1)
        self.combobox = QtWidgets.QComboBox(self)
        self.gridLayout.addWidget(self.combobox, 7, 0, 1, 1)

        self.lbl_title = QtWidgets.QLabel(self)
        self.lbl_title.setText('Title: ' + yt.title)
        self.lbl_len = QtWidgets.QLabel(self)
        self.lbl_len.setText('Length: ' + str(datetime.timedelta(seconds=yt.length)))
        self.lbl_author = QtWidgets.QLabel(self)
        self.lbl_author.setText('Author: ' + yt.author)
        self.lbl_date = QtWidgets.QLabel(self)
        self.lbl_date.setText('Publish date: ' + (yt.publish_date).strftime("%d-%b-%Y"))
        self.lbl_title.setWordWrap(True)
        self.gridLayout.addWidget(self.lbl_title, 2, 0, 1, 1)
        self.gridLayout.addWidget(self.lbl_author, 4, 0, 1, 1)
        self.gridLayout.addWidget(self.lbl_len, 5, 0, 1, 1)
        self.gridLayout.addWidget(self.lbl_date, 6, 0, 1, 1)

        for video in videos:
            if video.is_progressive:
                self.combobox.addItem('Video quality: ' + str(video.resolution) +
                                      ' FPS: ' + str(video.fps) + ' file size: '
                                      + str(convert_size(video.filesize)))
            else:
                self.combobox.addItem('Video quality: ' + str(video.resolution) +
                                      ' FPS: ' + str(video.fps) + ' file size: '
                                      + str(convert_size(video.filesize + audios[-1].filesize)))

        self.btn_download = QtWidgets.QPushButton('Download', self)
        self.btn_download.clicked.connect(lambda che: self.download(videos[self.combobox.currentIndex()], audios[-1]))
        self.gridLayout.addWidget(self.btn_download, 7, 1, 1, 1)

        spacerItem = QtWidgets.QSpacerItem(20, 313, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 9, 0, 1, 1)


if __name__ == '__main__':
    try:
        app = QtWidgets.QApplication(sys.argv)
        trayIcon = QtWidgets.QSystemTrayIcon(QtGui.QIcon('gui elements/icon.jpg'),parent=app)
        trayIcon.show()
        ui = Youtube_GUI()
        trayIcon.setVisible(True)
        ui.show()

    except Exception as e:
        print(e)

try:
    sys.exit(app.exec_())
except:
    print('Exiting')

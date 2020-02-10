import os
import sys
import subprocess
import signal
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import *
from functools import partial

framerate = 30
quality = 20
codec = 'libx264'
container = 'mkv'
bufferSize = 1024;
outdir = 'out'
tm = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3]

def launch(cmd):
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return subprocess.Popen(cmd, startupinfo=startupinfo, stdin=subprocess.PIPE)

class WebCamCapture(QSystemTrayIcon):
    # ffmpeg subprocess
    sc = None
    wc = None
    # Menu
    menu = None
    # selected video and audio devices
    video = None
    audio = None
    # is UScreenCapture found
    uscreen_capture_found = False;

    def __init__(self, icon, parent=None):
        QSystemTrayIcon.__init__(self, icon, parent)
        self.menu = QMenu(parent)
        self.setContextMenu(self.menu)                

    def stopProcess(self, process):
        try:
            process.stdin.write(b"q")
        except:
            pass

    def exit(self):
        self.stopProcess(self.sc)
        self.stopProcess(self.wc)
        QtCore.QCoreApplication.exit()

    def startScreenCapture(self):
        if self.uscreen_capture_found:
           self.sc = launch('ffmpeg -rtbufsize {}M -f dshow -i video="UScreenCapture" -vf select=gt(scene\,0.001) -r {} -q {} -c:v {} {}/desktop_{}.{}'
                 .format(bufferSize, framerate, quality, codec, outdir, tm, container))
        else:
           self.sc = launch('ffmpeg -rtbufsize {}M -f gdigrab -framerate {} -i desktop -c:v {} {}/desktop_{}.{}'
                 .format(bufferSize, framerate, codec, outdir, tm, container))
    
    def startWebCamCapture(self):
        self.wc = launch('ffmpeg -rtbufsize {}M -f dshow -i video="{}":audio="{}" -framerate {} -q {} -c:v {} {}/cam_{}.{}'
                 .format(bufferSize, self.video.text(), self.audio.text(), framerate, quality, codec, outdir, tm, container))

    def videoActionClicked(self):
        action = self.sender()
        if not action.isChecked():
            video.setChecked(False)
            self.stopProcess(self.wc)
            video = action
            video.setChecked(True)
            self.startWebCamCapture()

    def audioActionClicked(self):
        action = self.sender()
        if not action.isChecked():
            audio.setChecked(False)
            self.stopProcess(self.wc)
            audio = action
            audio.setChecked(True)
            self.startWebCamCapture()
   
    def listDevices(self):
        video_devices_menu = self.menu.addMenu("Video")
        audio_devices_menu = self.menu.addMenu("Audio")

        video_devices = QActionGroup(video_devices_menu)
        audio_devices = QActionGroup(audio_devices_menu)

        lst = subprocess.run('ffmpeg -list_devices true -f dshow -i dummy', capture_output=True, text=True)
        lines = lst.stderr.splitlines()
        for i in range(len(lines) - 1):
            if (lines[i].find('UScreenCapture') != -1):
                self.uscreen_capture_found = True;

            if (lines[i].find('DirectShow video devices') != -1):
                name = lines[i + 1].split("\"")                
                action = QAction(name[1], video_devices_menu, checkable = True)
                video_devices_menu.addAction(action)

                video_devices.addAction(action);
                if (len(video_devices.actions()) == 1):
                    action.setChecked(True)
                    self.video = action

                action.triggered.connect(self.videoActionClicked)

            if (lines[i].find('DirectShow audio devices') != -1):
                name = lines[i + 1].split("\"")                
                action = QAction(name[1], audio_devices_menu, checkable = True)
                audio_devices_menu.addAction(action)

                audio_devices.addAction(action)
                if (len(audio_devices.actions()) == 1):
                    action.setChecked(True)
                    self.audio = action

                action.triggered.connect(self.audioActionClicked)

        video_devices.setExclusive(True)
        audio_devices.setExclusive(True)

        # add exit menu
        self.menu.addAction("Exit", self.exit)

    def process(self):
        os.chdir('./bin')
        os.makedirs(outdir, exist_ok=True)
        
        self.listDevices()
        self.startScreenCapture()
        self.startWebCamCapture()

def main():
  app = QApplication(sys.argv)
  w = QWidget()
  trayIcon = WebCamCapture(QtGui.QIcon('cam.ico'), w)
  trayIcon.show()  
  trayIcon.process()
  sys.exit(app.exec_())

if __name__== "__main__":
    main()

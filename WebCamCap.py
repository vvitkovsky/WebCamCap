import os
import sys
import subprocess
import signal
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui

framerate = 30
quality = 20
codec = 'libx264'
bufferSize = 1024;
outdir = 'out'
tm = datetime.now().strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3]

def launch(cmd):
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return subprocess.Popen(cmd, startupinfo=startupinfo, stdin=subprocess.PIPE)

class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    sc = None
    wc = None

    def __init__(self, icon, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, icon, parent)
        menu = QtWidgets.QMenu(parent)
        exitAction = menu.addAction("Exit")
        self.setContextMenu(menu)
        menu.triggered.connect(self.exit)

    def exit(self):
        try:
            self.sc.stdin.write(b"q")
        except:
            pass

        try:
            self.wc.stdin.write(b"q")
        except:
            pass

        QtCore.QCoreApplication.exit()

    def process(self):
        os.chdir('./bin')
        os.makedirs(outdir, exist_ok=True)

        camName = ""
        audioName = ""
        screenCaptureFound = False;

        # find capture devices
        lst = subprocess.run('ffmpeg -list_devices true -f dshow -i dummy', capture_output=True, text=True)
        lines = lst.stderr.splitlines()
        for i in range(len(lines) - 1):
            if (lines[i].find('UScreenCapture') != -1):
                screenCaptureFound = True;
            if (lines[i].find('DirectShow video devices') != -1):
                name = lines[i + 1].split("\"")
                camName = name[1]
            if (lines[i].find('DirectShow audio devices') != -1):
                name = lines[i + 1].split("\"")
                audioName = name[1]
  
        # launch capture
        if screenCaptureFound:
            self.sc = launch('ffmpeg -rtbufsize {}M -f dshow -i video="UScreenCapture" -vf select=gt(scene\,0.001) -r {} -q {} -c:v {} {}/desktop_{}.mp4'
                 .format(bufferSize, framerate, quality, codec, outdir, tm))
        else:
            self.sc = launch('ffmpeg -rtbufsize {}M -f gdigrab -framerate {} -c:v {} {}/desktop_{}.mp4'
                 .format(bufferSize, framerate, codec, outdir, tm))

        self.wc = launch('ffmpeg -rtbufsize {}M -f dshow -i video="{}":audio="{}" -framerate {} -q {} -c:v {} {}/cam_{}.mp4'
                 .format(bufferSize, camName, audioName, framerate, quality, codec, outdir, tm))

def main(image):
  app = QtWidgets.QApplication(sys.argv)
  w = QtWidgets.QWidget()
  trayIcon = SystemTrayIcon(QtGui.QIcon(image), w)
  trayIcon.show()  
  trayIcon.process()
  sys.exit(app.exec_())

if __name__== "__main__":
    on='cam.ico'
    main(on)

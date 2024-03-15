import sys
import time
from xarm.wrapper import XArmAPI
import PyQt5
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap
import cv2
import os
from pathlib import Path
from PyQt5.QtCore import QTimer, QSize
from PyQt5.QtGui import QImage, QPixmap


# Hack to make PyQt and cv2 load simultaneously
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.fspath(
    Path(PyQt5.__file__).resolve().parent / "Qt5" / "plugins"
)


class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Player")
        self.setGeometry(100, 100, 1200, 800)  # Start window bigger
        self.initUI()
        self.initCameras()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateFrame)
        self.timer.start(30)  # Update interval in ms
        # self.arm = XArmAPI("192.168.1.212")
        # self.arm.motion_enable(enable=True)
        # self.arm.set_mode(5)
        # self.arm.set_state(state=0)
        # self.arm.reset(wait=True)

    def initUI(self):
        # Root vertical layout
        rootVLayout = QVBoxLayout()

        # Video Labels with larger size
        self.videoLabel32 = QLabel(self)
        self.videoLabel33 = QLabel(self)
        self.videoLabel2 = QLabel(self)

        # Set a larger minimum size for the video display areas
        # self.videoLabel32.setMinimumSize(QSize(800, 600))
        # self.videoLabel33.setMinimumSize(QSize(800, 600))
        # self.videoLabel2.setMinimumSize(QSize(800, 600))


        # Horizontal layouts for buttons
        hLayoutX = QHBoxLayout()
        self.btnMinusX = QPushButton("-X")
        self.btnPlusX = QPushButton("+X")
        hLayoutX.addWidget(self.btnMinusX)
        hLayoutX.addWidget(self.btnPlusX)

        hLayoutY = QHBoxLayout()
        self.btnMinusY = QPushButton("-Y")
        self.btnPlusY = QPushButton("+Y")
        hLayoutY.addWidget(self.btnMinusY)
        hLayoutY.addWidget(self.btnPlusY)

        rootVLayout.addWidget(self.videoLabel33)
        rootVLayout.addLayout(hLayoutX)
        rootVLayout.addWidget(self.videoLabel32)
        rootVLayout.addLayout(hLayoutY)
        rootVLayout.addWidget(self.videoLabel2)

        # Vertical layout for Z and STOP buttons
        vLayoutZ = QVBoxLayout()
        self.btnPlusZ = QPushButton("+Z")
        self.btnMinusZ = QPushButton("-Z")
        self.btnStop = QPushButton("STOP")
        vLayoutZ.addWidget(self.btnPlusZ)
        vLayoutZ.addWidget(self.btnMinusZ)
        vLayoutZ.addWidget(self.btnStop)

        # Add Z control vertical layout to the root layout
        rootVLayout.addLayout(vLayoutZ)

        # Replace or add these in the addControlButtons method or where you initialize buttons
        self.btnMinusX.pressed.connect(lambda: self.buttonPressedAction((-1, 0, 0)))
        self.btnMinusX.released.connect(lambda: self.buttonReleasedAction((-1, 0, 0)))
        self.btnPlusX.pressed.connect(lambda: self.buttonPressedAction((1, 0, 0)))
        self.btnPlusX.released.connect(lambda: self.buttonReleasedAction((1, 0, 0)))

        self.btnMinusY.pressed.connect(lambda: self.buttonPressedAction((0, -1, 0)))
        self.btnMinusY.released.connect(lambda: self.buttonReleasedAction((0, -1, 0)))
        self.btnPlusY.pressed.connect(lambda: self.buttonPressedAction((0, 1, 0)))
        self.btnPlusY.released.connect(lambda: self.buttonReleasedAction((0, 1, 0)))

        self.btnPlusZ.pressed.connect(lambda: self.buttonPressedAction((0, 0, 1)))
        self.btnPlusZ.released.connect(lambda: self.buttonReleasedAction((0, 0, 1)))
        self.btnMinusZ.pressed.connect(lambda: self.buttonPressedAction((0, 0, -1)))
        self.btnMinusZ.released.connect(lambda: self.buttonReleasedAction((0, 0, -1)))

        self.setLayout(rootVLayout)

    def initCameras(self):
        # Initialize camera captures
        # self.cap32 = cv2.VideoCapture('/dev/video32')
        # self.cap33 = cv2.VideoCapture('/dev/video33')
        # self.cap2 = cv2.VideoCapture('/dev/video2')
        self.cap32 = cv2.VideoCapture('/dev/video0')
        self.cap33 = cv2.VideoCapture('/dev/video2')
        self.cap2 = cv2.VideoCapture('/dev/video2')

    def updateFrame(self):
        # Read frame from each camera and update on respective QLabel
        for cap, label in [(self.cap32, self.videoLabel32), (self.cap33, self.videoLabel33), (self.cap2, self.videoLabel2)]:
            ret, frame = cap.read()
            if ret:
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
                p = convertToQtFormat.scaled(label.width(), label.height(), aspectRatioMode=Qt.KeepAspectRatio)
                label.setPixmap(QPixmap.fromImage(p))

    # def buttonPressed(self, vector):
    #     # Placeholder function for button press actions
    #     print(f"Button pressed with vector: {vector}")
    #     p = self.arm.position
    #     m = 1
    #     self.arm.set_position(x=p[0] + vector[0] * m,
    #                           y=p[1] + vector[1] * m,
    #                           z=p[2] + vector[2] * m)

    def buttonPressedAction(self, vector):
        v=list(vector)
        mult = 15
        v[0] *= mult
        v[1] *= mult
        v[2] *= mult
        self.arm.vc_set_cartesian_velocity(speeds=[v[0], v[1], v[2], 0, 0, 0],
                                           duration=1)
        print(f"Button pressed with vector: {vector}")
        # Your pressed action logic here

    def buttonReleasedAction(self, vector):
        self.arm.vc_set_cartesian_velocity(speeds=[0, 0, 0, 0, 0, 0])
        print(f"Button released with vector: {vector}")
        # Your released action logic here

    def closeEvent(self, event):
        # Release resources
        self.arm.set_mode(0)
        self.arm.set_state(state=0)
        self.arm.reset(wait=True)
        self.arm.disconnect()
        self.cap32.release()
        self.cap33.release()
        self.cap2.release()

    def stopFunction(self):
        self.arm.set_state(4)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VideoPlayer()
    ex.show()
    sys.exit(app.exec_())

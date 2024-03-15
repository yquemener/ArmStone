import sys
import cv2
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QPushButton, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QRectF
from PyQt5.QtGui import QImage, QPixmap, QPainter
import sys
import cv2
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QRect
from PyQt5.QtGui import QImage, QPixmap
import os
from pathlib import Path
import PyQt5
from xarm.wrapper import XArmAPI

# Hack to make PyQt and cv2 load simultaneously
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.fspath(
    Path(PyQt5.__file__).resolve().parent / "Qt5" / "plugins"
)


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path

    def run(self):
        cap = cv2.VideoCapture(self.video_path)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.change_pixmap_signal.emit(qt_image)
            else:
                break
        cap.release()


class VideoView(QWidget):
    def __init__(self, video_path):
        super().__init__()
        self.setWindowTitle("Video View")

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)

        self.zoom_button = QPushButton("Zoom", self)
        self.zoom_button.setCheckable(True)
        self.zoom_button.toggled.connect(self.toggle_zoom)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.view)
        self.layout.addWidget(self.zoom_button)
        self.setLayout(self.layout)

        self.video_item = QGraphicsPixmapItem()
        self.scene.addItem(self.video_item)

        self.thread = VideoThread(video_path)
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.start()

        self.is_zoomed = False

    def update_image(self, qt_img):
        pixmap = QPixmap.fromImage(qt_img)
        self.video_item.setPixmap(pixmap)
        if not self.zoom_button.isChecked():
            self.view.fitInView(self.video_item, Qt.KeepAspectRatio)

    def toggle_zoom(self, checked):
        if checked:
            # When zoom is checked, show the video unscaled (cropped by the QGraphicsView).
            self.view.setDragMode(QGraphicsView.ScrollHandDrag)
            self.view.resetTransform()  # Reset any scaling to show the video unscaled.
        else:
            # When zoom is unchecked, scale the video to fit the QGraphicsView.
            self.view.setDragMode(QGraphicsView.NoDrag)
            self.view.fitInView(self.video_item, Qt.KeepAspectRatio)


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        try:
            self.arm = XArmAPI("192.168.1.212")
            self.arm.motion_enable(enable=True)
            self.arm.set_mode(5)
            self.arm.set_state(state=0)
            self.arm.reset(wait=True)
        except Exception:
            print ("Could not initialize the arm")

    def initUI(self):
        self.layout = QVBoxLayout()

        self.setLayout(self.layout)

        videoLayout = QHBoxLayout()
        v1Layout = QVBoxLayout()
        self.video_view1 = VideoView('/dev/video32')
        v1Layout.addWidget(self.video_view1)
        v1buttons = QHBoxLayout()
        self.btnMinusX = QPushButton("-X")
        self.btnPlusX = QPushButton("+X")
        v1buttons.addWidget(self.btnPlusX)
        v1buttons.addWidget(self.btnMinusX)
        v1Layout.addLayout(v1buttons)
        videoLayout.addLayout(v1Layout)

        v2Layout = QVBoxLayout()
        self.video_view2 = VideoView('/dev/video33')
        v2Layout.addWidget(self.video_view2)
        v2buttons = QHBoxLayout()
        self.btnMinusY = QPushButton("-Y")
        self.btnPlusY = QPushButton("+Y")
        v2buttons.addWidget(self.btnMinusY)
        v2buttons.addWidget(self.btnPlusY)
        v2Layout.addLayout(v2buttons)
        videoLayout.addLayout(v2Layout)

        zButLayout = QVBoxLayout()
        self.btnPlusZ = QPushButton("+Z")
        self.btnMinusZ = QPushButton("-Z")
        self.btnStop = QPushButton("STOP")
        zButLayout.addWidget(self.btnPlusZ)
        zButLayout.addWidget(self.btnMinusZ)
        zButLayout.addWidget(self.btnStop)
        videoLayout.addLayout(zButLayout)

        self.layout.addLayout(videoLayout)

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

        self.btnStop.clicked.connect(self.stopFunction)

    def buttonPressedAction(self, vector):
        v=list(vector)
        mult = 15
        v[0] *= mult
        v[1] *= mult
        v[2] *= mult
        self.arm.vc_set_cartesian_velocity(speeds=[v[0], v[1], v[2], 0, 0, 0],
                                           duration=1)

    def buttonReleasedAction(self, vector):
        self.arm.vc_set_cartesian_velocity(speeds=[0, 0, 0, 0, 0, 0])

    def stopFunction(self):
        self.arm.set_state(4)

    def closeEvent(self, event):
        # Release resources
        self.arm.set_mode(0)
        self.arm.set_state(state=0)
        self.arm.reset(wait=True)
        self.arm.disconnect()
        self.cap32.release()
        self.cap33.release()
        self.cap2.release()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWidget()
    main_win.show()
    sys.exit(app.exec_())
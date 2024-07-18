import sys
from datetime import datetime

import cv2
from PyQt5.QtWidgets import QWidget, QApplication, QVBoxLayout, QPushButton, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QRectF, QTimer
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
import numpy as np
import torch
from PIL import Image

# Hack to make PyQt and cv2 load simultaneously
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.fspath(
    Path(PyQt5.__file__).resolve().parent / "Qt5" / "plugins"
)

DATASET_DIRECTORY="/home/yves/Projects/MUAL/OpenArmVision/visionUI/vhelio_holes"

# TODO: button to rearm when blocking

def make_uid():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.processor = MLImageProcessor()
        self.do_process = False
        self.save_next_frame = False

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

                if self.save_next_frame:
                    self.save_next_frame = False
                    fulldir = f"{DATASET_DIRECTORY}/candidates/"
                    if not os.path.exists(fulldir):
                        os.mkdir(fulldir)
                    uid = make_uid()
                    filename = f"{uid}.jpg"
                    fullpath = fulldir + "/" + filename
                    Image.fromarray(rgb_image).save(fullpath)

                if self.do_process:
                    self.processor.process(
                        self.processor.qimageToCvImage(qt_image))
                    qt_image = self.processor.cvImageToQImage(self.processor.rendered_image)

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

        self.autosave_button = QPushButton("Autosave (1 sec)", self)
        self.autosave_button.setCheckable(True)
        self.autosave_button.toggled.connect(self.toggle_autosave)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.save_next_frame)

        self.do_process_button = QPushButton("Vision")
        self.do_process_button.setCheckable(True)
        self.do_process_button.setChecked(False)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.view)
        self.layout.addWidget(self.zoom_button)
        self.layout.addWidget(self.autosave_button)
        self.layout.addWidget(self.do_process_button)
        self.setLayout(self.layout)

        self.video_item = QGraphicsPixmapItem()
        self.scene.addItem(self.video_item)

        self.thread = VideoThread(video_path)
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.do_process_button.pressed.connect(self.set_processing)
        self.thread.start()

        self.is_zoomed = False

    def set_processing(self):
        self.thread.do_process = not self.do_process_button.isChecked()

    def save_next_frame(self):
        self.thread.save_next_frame=True

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

    def toggle_autosave(self, checked):
        if self.autosave_button.isChecked():
            self.autosave_timer.start(1000)
        else:
            self.autosave_timer.stop()

    @staticmethod
    def make_uid():
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")

    def create_candidate(self):
        fulldir = f"{DATASET_DIRECTORY}/candidates/"
        if not os.path.exists(fulldir):
            os.mkdir(fulldir)
        uid = self.make_uid()

        filename = f"{uid}.jpg"
        fullpath = fulldir+"/"+filename
        Image.fromarray(self.capture.current_np).save(fullpath)

#     @staticmethod
#     def qimageToCvImage(qimage):
#         qimage = qimage.convertToFormat(QImage.Format.Format_RGB32)
#         width = qimage.width()
#         height = qimage.height()
#         ptr = qimage.bits()
#         ptr.setsize(qimage.byteCount())
#         arr = np.array(ptr).reshape(height, width, 4)  # 4 for RGBA
#         return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
#
#     @staticmethod
#     def cvImageToQImage(image):
#         if len(image.shape)==3:
#             height, width, channel = image.shape
#             fmt = QImage.Format_RGB888
#         else:
#             height, width = image.shape
#             channel = 1
#             fmt = QImage.Format_Grayscale8
#         bytesPerLine = channel * width
#         return QImage(image.data, width, height, bytesPerLine, fmt)

class MLImageProcessor:
    def __init__(self, model_file='/home/yves/Projects/MUAL/yolov5/runs/train/exp167/weights/best.pt'):
        self.ml_model = torch.hub.load('../../yolov5/', 'custom',
                                       path=model_file,
                                       source='local')
        self.ml_model.conf = 0.25
        pass

    def process(self, image):
        # return image
        current_np = np.array(image)

        self.ml_model.eval()
        with torch.no_grad():
            results = self.ml_model(current_np).xyxy[0]
        results = results.detach().tolist()

        for arr in results:
            print(arr)
            if arr[5]==1.0:
                color = (0,255,0)
            else:
                color = (255, 0, 0)
            image = cv2.rectangle(image, (int(arr[0]), int(arr[1]), int(arr[2]-arr[0]), int(arr[3]-arr[1])), color, 1)

        self.rendered_image = image  # The final processed image
        return image

    @staticmethod
    def qimageToCvImage(qimage):
        qimage = qimage.convertToFormat(QImage.Format.Format_RGB32)
        width = qimage.width()
        height = qimage.height()
        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())
        arr = np.array(ptr).reshape(height, width, 4)  # 4 for RGBA
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)

    @staticmethod
    def cvImageToQImage(image):
        if len(image.shape)==3:
            height, width, channel = image.shape
            fmt = QImage.Format_RGB888
        else:
            height, width = image.shape
            channel = 1
            fmt = QImage.Format_Grayscale8
        bytesPerLine = channel * width
        return QImage(image.data, width, height, bytesPerLine, fmt)


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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWidget()
    main_win.show()
    sys.exit(app.exec_())

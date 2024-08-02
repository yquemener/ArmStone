import sys
import time
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
import socket

# Hack to make PyQt and cv2 load simultaneously
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.fspath(
    Path(PyQt5.__file__).resolve().parent / "Qt5" / "plugins"
)

DATASET_DIRECTORY="/home/yves/Projects/HLA/MUAL/OpenArmVision/visionUI/vhelio_holes"

# TODO: button to rearm when blocking
# TODO: less path hardcoded
# TODO: Arm IP not hardcoded
# TODO: (remote?) controls for camera focus and 50Hz
# TODO: bugfix double model loading
# TODO: clic to select hole
# TODO: open/close clamp with button
# TODO: Calibration lines

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
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
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

        self.log_view = QLabel()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.view)
        self.layout.addWidget(self.log_view)
        self.layout.addWidget(self.zoom_button)
        self.layout.addWidget(self.autosave_button)
        self.layout.addWidget(self.do_process_button)
        self.setLayout(self.layout)

        self.video_item = QGraphicsPixmapItem()
        self.scene.addItem(self.video_item)

        self.thread = VideoThread(video_path)
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.do_process_button.pressed.connect(self.set_processing)
        # self.scene.mousePressEvent.connect()
        self.view.mousePressEvent = self.video_onclick
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
        delta = self.thread.processor.delta
        self.log_view.setText(f"dx = {delta[0]:.2f}\ndz = {delta[1]:.2f}")

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

    def video_onclick(self, event):
        p = self.view.mapToScene(event.pos())
        print(p.x(), p.y())
        self.thread.processor.click_pos = (p.x(), p.y())


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
    def __init__(self, model_file='/home/yves/Projects/HLA/MUAL/OpenArmVision/visionUI/thirdparty/yolov5/runs/train/exp168/weights/best.pt'):
        self.ml_model = torch.hub.load('/home/yves/Projects/HLA/MUAL/OpenArmVision/visionUI/thirdparty/yolov5/', 'custom',
                                       path=model_file,
                                       source='local')
        self.ml_model.conf = 0.5
        self.tip_pos_history = list()
        self.holes_history = list()
        self.closest_hole_history = list()
        self.tip = (0,0)
        self.closest_hole = (0,0)
        self.delta = (0, 0)
        self.click_pos = None

    def process(self, image):
        # return image
        current_np = np.array(image)

        self.ml_model.eval()
        with torch.no_grad():
            results = self.ml_model(current_np).xyxy[0]
        results = results.detach().tolist()

        holes = list()
        tips = list()
        for arr in results:
            cx = int((arr[0] + arr[2]) / 2)
            cy = int((arr[1] + arr[3]) / 2)
            if arr[5]==0.0:
                color = (0,255,0)
                image = cv2.line(image, (cx-2, cy), (cx+2, cy), color, 1)
                image = cv2.line(image, (cx, cy-2), (cx, cy+2), color, 1)
                tips.append([arr[4], cx,cy])
            else:
                color = (255, 0, 0)
                image = cv2.rectangle(image, (int(arr[0]), int(arr[1]), int(arr[2]-arr[0]), int(arr[3]-arr[1])), color, 1)
                holes.append([arr[4], cx,cy])

        # Process tip
        if len(tips) > 0:
            if len(self.tip_pos_history) == 0:
                tips = list(reversed(sorted(tips)))
                self.tip_pos_history.append(tips[0][1:])
            else:
                dists = list()
                for tip in tips:
                    dx = abs(tip[1] - self.tip[0])
                    dy = abs(tip[2] - self.tip[1])
                    dists.append(((dx ** 2 + dy ** 2), tip[1:]))
                closest_tip = sorted(dists)[0][1]
                self.tip_pos_history.append(closest_tip)
        if len(self.tip_pos_history) > 0:
            self.tip = np.average(self.tip_pos_history[-10:], axis=0)

        # Process closest hole
        if self.click_pos is None:
            target = self.tip
        else:
            target = self.click_pos
        if len(holes) > 0:
            dists = list()
            for hole in holes:
                dx = abs(hole[1] - target[0])
                dy = abs(hole[2] - target[1])
                dists.append(((dx**2+dy**2), hole[1], hole[2]))
            closest_hole = list(sorted(dists))[0][1:]
            self.closest_hole_history.append(closest_hole)
        if len(self.closest_hole_history)>0:
            self.closest_hole = np.average(self.closest_hole_history[-10:], axis=0)
        # Display tip
        color = (0, 0, 255)
        cx = int(self.tip[0])
        cy = int(self.tip[1])
        image = cv2.line(image, (cx - 10, cy), (cx + 10, cy), color, 1)
        image = cv2.line(image, (cx, cy - 10), (cx, cy + 10), color, 1)

        # Display closest hole
        color = (255, 0, 0)
        cx = int(self.closest_hole[0])
        cy = int(self.closest_hole[1])
        image = cv2.line(image, (cx - 10, cy), (cx + 10, cy), color, 1)
        image = cv2.line(image, (cx, cy - 10), (cx, cy + 10), color, 1)

        self.delta = (self.tip[0]-self.closest_hole[0], self.tip[1]-self.closest_hole[1])

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
        self.servoingEnable = [0, 0, 0]
        try:
            if socket.gethostname() == "ivl":
                self.arm = XArmAPI("192.168.1.216")
            else:
                self.arm = XArmAPI("192.168.1.212")
            self.arm.motion_enable(enable=True)
            self.arm.set_mode(5)
            self.arm.set_state(state=0)
            self.arm.reset(wait=False)
        except Exception:
            print ("Could not initialize the arm")


    def initUI(self):
        self.layout = QVBoxLayout()

        self.setLayout(self.layout)

        videoLayout = QHBoxLayout()
        v1Layout = QVBoxLayout()
        if socket.gethostname() == "ivl":
            self.video_view1 = VideoView('/dev/video2')
            self.video_view2 = VideoView('/dev/video4')
        else:
            self.video_view1 = VideoView('/dev/video32')
            self.video_view2 = VideoView('/dev/video33')
        v1Layout.addWidget(self.video_view1)
        self.btnAutoX = QPushButton("Auto X")
        v1Layout.addWidget(self.btnAutoX)
        v1buttons = QHBoxLayout()
        self.btnMinusX = QPushButton("-X")
        self.btnPlusX = QPushButton("+X")
        v1buttons.addWidget(self.btnPlusX)
        v1buttons.addWidget(self.btnMinusX)
        v1Layout.addLayout(v1buttons)
        videoLayout.addLayout(v1Layout)

        v2Layout = QVBoxLayout()
        v2Layout.addWidget(self.video_view2)
        self.btnAutoY = QPushButton("Auto Y")
        v2Layout.addWidget(self.btnAutoY)
        v2buttons = QHBoxLayout()
        self.btnMinusY = QPushButton("-Y")
        self.btnPlusY = QPushButton("+Y")
        v2buttons.addWidget(self.btnPlusY)
        v2buttons.addWidget(self.btnMinusY)
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
        self.btnAutoX.clicked.connect(self.autoX)

        self.btnMinusY.pressed.connect(lambda: self.buttonPressedAction((0, -1, 0)))
        self.btnMinusY.released.connect(lambda: self.buttonReleasedAction((0, -1, 0)))
        self.btnPlusY.pressed.connect(lambda: self.buttonPressedAction((0, 1, 0)))
        self.btnPlusY.released.connect(lambda: self.buttonReleasedAction((0, 1, 0)))
        self.btnAutoY.clicked.connect(self.autoY)

        self.btnPlusZ.pressed.connect(lambda: self.buttonPressedAction((0, 0, 1)))
        self.btnPlusZ.released.connect(lambda: self.buttonReleasedAction((0, 0, 1)))
        self.btnMinusZ.pressed.connect(lambda: self.buttonPressedAction((0, 0, -1)))
        self.btnMinusZ.released.connect(lambda: self.buttonReleasedAction((0, 0, -1)))

        self.btnStop.clicked.connect(self.stopFunction)

        self.timerServoing = QTimer()
        self.timerServoing.setInterval(100)
        self.servoingStartTime = 0
        self.timerServoing.timeout.connect(self.servoing)

    def servoing(self):
        speed = 0.1
        if time.time()-self.servoingStartTime > 4:
            self.timerServoing.stop()
            self.servoingEnable = [0,0,0]
            return
        deltax = self.video_view1.thread.processor.delta[0] * speed * self.servoingEnable[0]
        deltay = self.video_view2.thread.processor.delta[0] * speed * self.servoingEnable[1]
        self.arm.vc_set_cartesian_velocity(speeds=[deltax, deltay, 0, 0, 0, 0],
                                           duration=0.1)

    def autoX(self):
        self.servoingStartTime = time.time()
        self.timerServoing.start()
        self.servoingEnable[0] = 1

    def autoY(self):
        self.servoingStartTime = time.time()
        self.timerServoing.start()
        self.servoingEnable[1] = 1

    def buttonPressedAction(self, vector):
        v=list(vector)
        mult = 15
        v[0] *= mult
        v[1] *= mult
        v[2] *= mult
        self.arm.vc_set_cartesian_velocity(speeds=[v[0], v[1], v[2], 0, 0, 0], duration=10)

    def buttonReleasedAction(self, vector):
        self.arm.vc_set_cartesian_velocity(speeds=[0, 0, 0, 0, 0, 0])

    def stopFunction(self):
        self.arm.set_state(4)

    def closeEvent(self, event):
        # Release resources
        return # or not
        self.arm.set_mode(0)
        self.arm.set_state(state=0)
        self.arm.reset(wait=True)
        self.arm.disconnect()

    def onImageChanged(self):
        return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWidget()
    main_win.show()
    sys.exit(app.exec_())

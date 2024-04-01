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
import numpy as np
import torch

# Hack to make PyQt and cv2 load simultaneously
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.fspath(
    Path(PyQt5.__file__).resolve().parent / "Qt5" / "plugins"
)


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.processor = MLImageProcessor()

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
                try:
                    self.processor.process(
                        self.processor.qimageToCvImage(qt_image))
                    qt_image = self.processor.cvImageToQImage(self.processor.rendered_image)
                except Exception:
                    pass
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


# class ImageProcessor:
#     def __init__(self):
#         pass
#
#     def process(self, image):
#         gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#         blurred = cv2.GaussianBlur(gray, (5, 5), 0)
#
#         # Enhance contrast if needed (optional)
#         # gray = cv2.equalizeHist(gray)
#
#         # Threshold to find darker areas
#         _, binary = cv2.threshold(blurred, 80, 255, cv2.THRESH_BINARY)
#
#         # Use Flood Fill from a known point to isolate the tool
#         mask = np.zeros((gray.shape[0] + 2, gray.shape[1] + 2), np.uint8)
#         tooldetect = binary
#         cv2.floodFill(tooldetect, mask, (400, 16), 128)
#         tooldetect = (tooldetect==128).astype(np.uint8)*255
#
#         # Find contours and the tool's tip
#         contours, _ = cv2.findContours(tooldetect, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#         toolTip = None
#         for contour in contours:
#             # Assuming the tool's contour is the largest one
#             if toolTip is None or cv2.contourArea(contour) > cv2.contourArea(toolTip):
#                 toolTip = contour
#
#         if toolTip is not None:
#             # Find the tip (bottom point) of the tool
#             bottomPoint = max(toolTip, key=lambda point: point[0][1])
#             cv2.circle(image, (bottomPoint[0][0], bottomPoint[0][1]), 5, (0, 0, 255), -1)
#
#         # Create a blank image for drawing contours
#         self.contoursImg = np.zeros_like(image)
#
#         # Draw the contours on the blank image
#         cv2.drawContours(self.contoursImg, contours, -1, (0, 255, 0), 2)  # Drawing in green with a thickness of 2
#
#         # Holes finder
#         _, binary = cv2.threshold(blurred, 30, 255, cv2.THRESH_BINARY)  # Adjust threshold
#         contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#
#         # 3. Shape Analysis
#         for contour in contours:
#             if len(contour) >= 5:  # Need at least 5 points to fit ellipse
#                 ellipse = cv2.fitEllipse(contour)
#                 area = cv2.contourArea(contour)
#                 if self.isEllipsoid(ellipse, area):
#                     cv2.ellipse(image, ellipse, (0, 255, 0), 2)  # Draw ellipse in green
#
#                     x1,y1 = int(ellipse[0][0]),int(ellipse[0][1])
#                     x2, y2 = bottomPoint[0]
#                     cv2.line(image, [x1, y1], [x2, y1],(255,0,0), 2)
#                     cv2.line(image, [x2, y2], [x2, y1],(255,0,0), 2)
#
#
#
#         self.currentImage = image  # The final processed image
#         self.binaryImage = binary  # After applying the threshold
#         self.floodFillImg = blurred
#         self.rendered_image = image
#
#     def process_hole(self, image):
#         # 1. Pre-processing
#         gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#         blurred = cv2.GaussianBlur(gray, (5, 5), 0)
#
#         # 2. Blob Detection
#         _, binary = cv2.threshold(blurred, 30, 255, cv2.THRESH_BINARY_INV)  # Adjust threshold as needed
#         contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#
#         # 3. Shape Analysis
#         for contour in contours:
#             if len(contour) >= 5:  # Need at least 5 points to fit ellipse
#                 ellipse = cv2.fitEllipse(contour)
#                 area = cv2.contourArea(contour)
#                 if self.isEllipsoid(ellipse, area):
#                     cv2.ellipse(image, ellipse, (0, 255, 0), 2)  # Draw ellipse in green
#
#         return image
#
#     def isEllipsoid(self, ellipse, area):
#         # Implement logic to determine if the contour fits an ellipsoid shape
#         # This could involve checking the aspect ratio and area of the fitted ellipse
#         (center, axes, orientation) = ellipse
#         majoraxis_length = max(axes)
#         minoraxis_length = min(axes)
#         aspect_ratio = majoraxis_length / minoraxis_length
#
#         # Example criteria, adjust as needed
#         return aspect_ratio < 2 and 100 < area < 5000  # Example criteria
#
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
    def __init__(self, model_file='../../../OpenArmVision/yolov5/runs/train/exp166/weights/best.pt'):
        self.ml_model = torch.hub.load('../../../OpenArmVision/yolov5/', 'custom',
                                       path=model_file,
                                       source='local')
        self.ml_model.conf = 0.05

    def process(self, image):
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
        self.cap32.release()
        self.cap33.release()
        self.cap2.release()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = MainWidget()
    main_win.show()
    sys.exit(app.exec_())
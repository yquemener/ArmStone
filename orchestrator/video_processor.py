import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QFileDialog, QLineEdit, QCheckBox, QVBoxLayout, \
    QHBoxLayout
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
import os
import cv2
from pathlib import Path
import PyQt5
import numpy as np

# Hack to make PyQt and cv2 load simultaneously
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.fspath(
    Path(PyQt5.__file__).resolve().parent / "Qt5" / "plugins"
)


class ImageViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.frameFiles = []
        self.cap1 = cv2.VideoCapture("/dev/video32")
        self.currentIndex = 0
        self.isPlaying = False
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.nextFrame)
        self.processFrames = False
        self.mode = 'video'

    def initUI(self):
        self.setWindowTitle('Poupette Vision')
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()

        self.imageLabel = QLabel(self)
        self.layout.addWidget(self.imageLabel)

        self.frameIndicator = QLineEdit(self)
        self.frameIndicator.setFixedWidth(100)
        self.layout.addWidget(self.frameIndicator)

        self.openButton = QPushButton('Open', self)
        self.openButton.clicked.connect(self.openFolder)
        self.layout.addWidget(self.openButton)

        controlLayout = QHBoxLayout()
        self.playButton = QPushButton('Play', self)
        self.playButton.clicked.connect(self.play)
        controlLayout.addWidget(self.playButton)

        self.pauseButton = QPushButton('Pause', self)
        self.pauseButton.clicked.connect(self.pause)
        controlLayout.addWidget(self.pauseButton)

        self.prevButton = QPushButton('<', self)
        self.prevButton.clicked.connect(lambda: self.changeFrame(-1))
        controlLayout.addWidget(self.prevButton)

        self.nextButton = QPushButton('>', self)
        self.nextButton.clicked.connect(lambda: self.changeFrame(1))
        controlLayout.addWidget(self.nextButton)

        self.processCheckbox = QCheckBox('Process', self)
        self.processCheckbox.stateChanged.connect(self.toggleProcessing)
        controlLayout.addWidget(self.processCheckbox)

        self.frameIndicator.editingFinished.connect(self.skipToFrame)

        self.videoButton = QPushButton('Video', self)
        self.videoButton.clicked.connect(lambda: self.changeDisplayMode('video'))
        self.layout.addWidget(self.videoButton)

        self.binaryButton = QPushButton('Binary', self)
        self.binaryButton.clicked.connect(lambda: self.changeDisplayMode('binary'))
        self.layout.addWidget(self.binaryButton)

        self.floodFillButton = QPushButton('FloodFill', self)
        self.floodFillButton.clicked.connect(lambda: self.changeDisplayMode('floodfill'))
        self.layout.addWidget(self.floodFillButton)

        self.contoursButton = QPushButton('Contours', self)
        self.contoursButton.clicked.connect(lambda: self.changeDisplayMode('contours'))
        self.layout.addWidget(self.contoursButton)

        self.layout.addLayout(controlLayout)
        self.setLayout(self.layout)

    def openFolder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder:
            self.loadFolder(folder)

    def loadFolder(self, folder):
            self.frameFiles = sorted([os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.jpg')])
            self.currentIndex = 0
            self.showFrame()

    def play(self):
        self.isPlaying = True
        self.timer.start(33)  # ~30 fps

    def pause(self):
        self.isPlaying = False
        self.timer.stop()

    def nextFrame(self):
        self.changeFrame(1)

    def changeFrame(self, step):
        if self.frameFiles:
            self.currentIndex = (self.currentIndex + step) % len(self.frameFiles)
            self.showFrame()

    def showFrame(self):
        if 0 <= self.currentIndex < len(self.frameFiles):
            framePath = self.frameFiles[self.currentIndex]
            pixmap = QPixmap(framePath)
            self.frameIndicator.setText(str(self.currentIndex))
            self.currentImage = self.pixmapToCvImage(pixmap)
        # ret, self.currentImage = self.cap1.read()

        if self.processFrames:
            self.currentImage = self.process(self.currentImage)
        if self.mode == 'video':
            self.displayImage(self.currentImage)
        elif self.mode == 'binary':
            self.displayImage(self.binaryImage)
        elif self.mode == 'floodfill':
            self.displayImage(self.floodFillImg)
        elif self.mode == 'contours':
            self.displayImage(self.contoursImg)



    def changeDisplayMode(self, mode):
        self.mode = mode

    def displayImage(self, image):
        if image is not None:
            pixmap = self.cvImageToQPixmap(image)
            self.imageLabel.setPixmap(
                pixmap.scaled(self.imageLabel.width(), self.imageLabel.height(), Qt.KeepAspectRatio))

    def process(self, image):
        # Convert QPixmap to OpenCV format
        # image = self.pixmapToCvImage(pixmap)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Enhance contrast if needed (optional)
        # gray = cv2.equalizeHist(gray)

        # Threshold to find darker areas
        _, binary = cv2.threshold(blurred, 80, 255, cv2.THRESH_BINARY)  # Adjust threshold based on actual tool color

        # Use Flood Fill or Connected Components from a known point to isolate the tool
        # Assuming flood fill for demonstration; adapt as necessary
        mask = np.zeros((gray.shape[0] + 2, gray.shape[1] + 2), np.uint8)  # Mask for floodFill
        tooldetect = binary
        cv2.floodFill(tooldetect, mask, (400, 16), 128)
        tooldetect = (tooldetect==128).astype(np.uint8)*255

        # Find contours and the tool's tip
        contours, _ = cv2.findContours(tooldetect, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        toolTip = None
        for contour in contours:
            # Assuming the tool's contour is the largest one
            if toolTip is None or cv2.contourArea(contour) > cv2.contourArea(toolTip):
                toolTip = contour

        if toolTip is not None:
            # Find the tip (bottom point) of the tool
            bottomPoint = max(toolTip, key=lambda point: point[0][1])
            # Draw the point
            cv2.circle(image, (bottomPoint[0][0], bottomPoint[0][1]), 5, (0, 0, 255), -1)

        # Create a blank image for drawing contours
        self.contoursImg = np.zeros_like(image)

        # Draw the contours on the blank image
        cv2.drawContours(self.contoursImg, contours, -1, (0, 255, 0), 2)  # Drawing in green with a thickness of 2

        # Holes finder
        _, binary = cv2.threshold(blurred, 30, 255, cv2.THRESH_BINARY)  # Adjust threshold
        contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # 3. Shape Analysis
        for contour in contours:
            if len(contour) >= 5:  # Need at least 5 points to fit ellipse
                ellipse = cv2.fitEllipse(contour)
                area = cv2.contourArea(contour)
                if self.isEllipsoid(ellipse, area):
                    cv2.ellipse(image, ellipse, (0, 255, 0), 2)  # Draw ellipse in green

                    x1,y1 = int(ellipse[0][0]),int(ellipse[0][1])
                    x2, y2 = bottomPoint[0]
                    cv2.line(image, [x1, y1], [x2, y1],(255,0,0), 2)
                    cv2.line(image, [x2, y2], [x2, y1],(255,0,0), 2)



        self.currentImage = image  # The final processed image
        self.binaryImage = binary  # After applying the threshold
        self.floodFillImg = blurred

        # Initially display the current (final processed) image
        self.displayImage(self.currentImage)

        return image

    def process_hole(self, pixmap):
        # Convert QPixmap to OpenCV format
        image = self.pixmapToCvImage(pixmap)

        # 1. Pre-processing
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 2. Blob Detection
        _, binary = cv2.threshold(blurred, 30, 255, cv2.THRESH_BINARY_INV)  # Adjust threshold as needed
        contours, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # 3. Shape Analysis
        for contour in contours:
            if len(contour) >= 5:  # Need at least 5 points to fit ellipse
                ellipse = cv2.fitEllipse(contour)
                area = cv2.contourArea(contour)
                if self.isEllipsoid(ellipse, area):
                    cv2.ellipse(image, ellipse, (0, 255, 0), 2)  # Draw ellipse in green

        return image

    def isEllipsoid(self, ellipse, area):
        # Implement logic to determine if the contour fits an ellipsoid shape
        # This could involve checking the aspect ratio and area of the fitted ellipse
        (center, axes, orientation) = ellipse
        majoraxis_length = max(axes)
        minoraxis_length = min(axes)
        aspect_ratio = majoraxis_length / minoraxis_length

        # Example criteria, adjust as needed
        return aspect_ratio < 2 and 100 < area < 5000  # Example criteria

    def pixmapToCvImage(self, pixmap):
        # Convert QPixmap to QImage
        qimage = pixmap.toImage()
        qimage = qimage.convertToFormat(QImage.Format.Format_RGB32)

        width = qimage.width()
        height = qimage.height()

        ptr = qimage.bits()
        ptr.setsize(qimage.byteCount())
        arr = np.array(ptr).reshape(height, width, 4)  # 4 for RGBA
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)

    def cvImageToQPixmap(self, image):
        if len(image.shape)==3:
            height, width, channel = image.shape
            fmt = QImage.Format_RGB888
        else:
            height, width = image.shape
            channel = 1
            fmt = QImage.Format_Grayscale8
        bytesPerLine = channel * width
        qimage = QImage(image.data, width, height, bytesPerLine, fmt)
        return QPixmap.fromImage(qimage.rgbSwapped())

    def toggleProcessing(self, state):
        self.processFrames = bool(state)
        self.showFrame()

    def skipToFrame(self):
        frameNumber = self.frameIndicator.text()
        if frameNumber.isdigit():
            newIndex = int(frameNumber)
            if 0 <= newIndex < len(self.frameFiles):
                self.currentIndex = newIndex
                self.showFrame()
            else:
                self.frameIndicator.setText(str(self.currentIndex))  # Reset to current index if out of range
        else:
            self.frameIndicator.setText(str(self.currentIndex))  # Reset if not a valid number


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ImageViewer()
    ex.show()
    ex.loadFolder("/home/yves/Projects/active/HLA/MUAL/data/videos/20240214/raw/vid1")
    sys.exit(app.exec_())

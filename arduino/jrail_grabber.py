import sys
import serial
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLineEdit, QMessageBox
from PyQt5.QtCore import Qt, QTimer
import time

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setupSerial()
        self.number=100
        time.sleep(1)
        self.sendNumber()

    def setupSerial(self):
        # Setup serial connection
        try:
            self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
            #self.ser.flush()
        except serial.SerialException:
            QMessageBox.critical(self, "Serial Connection Error", "Failed to connect to the serial port.")
            self.close()

    def initUI(self):
        self.number = 130  # Initialize the number attribute

        # Create a vertical box layout
        vbox = QVBoxLayout()

        # Create a line edit widget to display the number
        self.lineEdit = QLineEdit(self)
        self.lineEdit.setText(str(self.number))
        self.lineEdit.setAlignment(Qt.AlignRight)
        self.lineEdit.returnPressed.connect(self.onReturnPressed)

        # Create "+" button with auto-repeat
        self.btn_increase = QPushButton('+', self)
        self.btn_increase.setAutoRepeat(True)
        self.btn_increase.setAutoRepeatInterval(100)  # Repeats every 100ms
        self.btn_increase.clicked.connect(self.increase_number)

        # Create "-" button with auto-repeat
        self.btn_decrease = QPushButton('-', self)
        self.btn_decrease.setAutoRepeat(True)
        self.btn_decrease.setAutoRepeatInterval(100)  # Repeats every 100ms
        self.btn_decrease.clicked.connect(self.decrease_number)

        # Add widgets to the layout
        vbox.addWidget(self.lineEdit)
        vbox.addWidget(self.btn_increase)
        vbox.addWidget(self.btn_decrease)

        # Set the layout on the application's window
        self.setLayout(vbox)

        # Set the window properties
        self.setWindowTitle('Servo Control')
        self.setGeometry(300, 300, 200, 150)  # x, y, width, height

    def onReturnPressed(self):
        # Set number from the line edit on pressing Enter
        try:
            num = int(self.lineEdit.text())
            self.number = max(0, min(180, num))  # Ensure number is between 0 and 180
            self.lineEdit.setText(str(self.number))
            self.sendNumber()
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid integer.")

    def increase_number(self):
        self.number = min(180, self.number + 1)  # Ensure number does not exceed 180
        self.lineEdit.setText(str(self.number))
        self.sendNumber()

    def decrease_number(self):
        self.number = max(0, self.number - 1)  # Ensure number is not less than 0
        self.lineEdit.setText(str(self.number))
        self.sendNumber()

    def sendNumber(self):
        if self.ser.is_open:
            self.ser.write(f"111 {self.number} 222\n".encode('utf-8'))  # Send the number as a string with a newline
            print(self.number)
            
    def closeEvent(self, event):
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()  # Close serial port when the application is closed

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())


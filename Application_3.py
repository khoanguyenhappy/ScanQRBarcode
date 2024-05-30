import sys
import cv2
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QFileDialog
from PyQt5.uic import loadUi
from pyzbar.pyzbar import decode
import numpy as np
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi('bai5.ui', self)
        self.setWindowTitle("Barcode reader application")

        self.is_live = False
        self.image_list = []
        self.current_image_index = 0

        self.scene = QGraphicsScene()
        self.graphicsView.setScene(self.scene)

        self.capture = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

        self.btn_Live.clicked.connect(self.toggle_live)
        self.btn_Trigger.clicked.connect(self.capture_image)
        self.btn_Saveimage.clicked.connect(self.save_image)
        self.btn_Loadimage.clicked.connect(self.load_image)
        self.btn_Loadvideo.clicked.connect(self.load_video)
        self.btn_Playback.clicked.connect(self.load_folder)
        self.btn_Backimage.clicked.connect(self.prev_image)
        self.btn_Nextimage.clicked.connect(self.next_image)

        self.label.setStyleSheet("color: green;")
        self.frame_ok_ng.setStyleSheet("background-color: yellow;")

    def toggle_live(self):
        if not self.is_live:
            self.is_live = True
            self.btn_Live.setText("STOP")
            self.capture = cv2.VideoCapture(0)
            self.timer.start(30)
        else:
            self.is_live = False
            self.btn_Live.setText("LIVE")
            self.timer.stop()
            self.scene.clear()
            self.frame_ok_ng.setStyleSheet("background-color: yellow;")

    def capture_image(self):
        if not self.is_live:
            ret, frame = self.capture.read()
            if ret:
                self.read_barcode(frame)
                self.update_graphics_view(self.scene, frame)

    def save_image(self):
        if not self.is_live:
            if self.scene.items():
                file_dialog = QFileDialog()
                file_path = file_dialog.getSaveFileName(self, "Save Image", "", "Images (*.png *.jpg *.bmp)")
                if file_path:
                    pixmap = self.scene.items()[0].pixmap()
                    pixmap.save(file_path)
            else:
                print("No image to save")

    def load_image(self):
        if not self.is_live:
            file_dialog = QFileDialog()
            file_path = file_dialog.getOpenFileName(self, "Load Image", "", "Images (*.png *.jpg *.bmp)")
            if file_path:
                image = cv2.imread(file_path)
                self.image_list = [image]
                self.current_image_index = 0
                self.process_and_display_image(image)

    def load_video(self):
        if not self.is_live:
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(self, "Load video", "", "Video (*.mp4 *.avi)")
            if file_path:
                self.capture = cv2.VideoCapture(file_path)
                self.timer = QTimer(self)
                self.timer.timeout.connect(self.update_frame)
                self.timer.start(70)

    def update_frame(self):
        ret, frame = self.capture.read()
        if ret:
            self.read_barcode(frame)
            self.update_graphics_view(self.scene, frame)

    def update_graphics_view(self, graphics_view, frame):
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()

        graphics_view.clear()
        graphics_view.addPixmap(QPixmap.fromImage(q_image))

    def read_barcode(self, frame):
        decoded_objects = decode(frame)
        all_codes = []
        self.Text_Content_Code.setPlainText("")
        self.frame_ok_ng.setStyleSheet("background-color: red;")
        for obj in decoded_objects:
            data = obj.data.decode('utf-8')
            all_codes.append(data)
            combined_codes = '\n'.join(all_codes)
            self.Text_Content_Code.setPlainText(combined_codes)
            if self.Text_Content_Code.toPlainText() != "":
                self.frame_ok_ng.setStyleSheet("background-color: green;")

            rect_points = obj.polygon

            if len(rect_points) > 4:
                hull = cv2.convexHull(np.array([point for point in rect_points], dtype=np.float32))
                cv2.polylines(frame, [hull], isClosed=True, color=(0, 255, 0), thickness=2)
            else:
                cv2.polylines(frame, [np.array(rect_points, dtype=np.int32)], isClosed=True, color=(0, 255, 0),
                              thickness=2)

            cv2.putText(frame, data, (rect_points[0][0], rect_points[0][1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0),
                        2)

    def load_folder(self):
        if not self.is_live:
            folder_dialog = QFileDialog()
            folder_path = folder_dialog.getExistingDirectory(self, "Load Image Folder")
            if folder_path:
                image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.bmp'))]
                self.image_list = [cv2.imread(os.path.join(folder_path, f)) for f in image_files]
                self.current_image_index = 0
                if self.image_list:
                    self.process_and_display_image(self.image_list[self.current_image_index])

    def process_and_display_image(self, image):
        self.read_barcode(image)
        self.update_graphics_view(self.scene, image)

    def prev_image(self):
        if not self.is_live and self.image_list:
            self.current_image_index = (self.current_image_index - 1) % len(self.image_list)
            self.process_and_display_image(self.image_list[self.current_image_index])

    def next_image(self):
        if not self.is_live and self.image_list:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_list)
            self.process_and_display_image(self.image_list[self.current_image_index])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

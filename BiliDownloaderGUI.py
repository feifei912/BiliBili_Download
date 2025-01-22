import os
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import qtawesome
from BiliVideoDownloader import BiliVideoDownloader


class BiliDownloaderGUI(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.downloader = BiliVideoDownloader()
        # Window dragging state
        self.m_flag = False
        self.m_Position = None

        # Use a frameless window and enable translucent background
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Create the main layout
        self.main_widget = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QGridLayout(self.main_widget)
        self.main_layout.setSpacing(0)
        self.setCentralWidget(self.main_widget)

        # Set a title bar widget at the top (for dragging and control buttons)
        self.setup_title_bar()
        # Set up the main content area
        self.setup_content_area()
        # Apply styles
        self.init_style()

    def setup_title_bar(self):
        """Create a custom title bar with typical right-corner controls."""
        self.title_bar = QtWidgets.QWidget()
        self.title_bar.setObjectName("title_bar")
        self.title_bar_layout = QtWidgets.QHBoxLayout(self.title_bar)
        self.title_bar_layout.setContentsMargins(10, 0, 10, 0)

        # A title label on the left
        self.title_label = QtWidgets.QLabel("哔哩哔哩下载器")
        self.title_label.setStyleSheet("color: white; background-color: transparent;")
        self.title_label.setAutoFillBackground(True)
        self.title_label.setObjectName("title_label")
        self.title_label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)

        # Controls on the right
        self.btn_min = QtWidgets.QPushButton("")
        self.btn_max = QtWidgets.QPushButton("")
        self.btn_close = QtWidgets.QPushButton("")
        for btn in (self.btn_min, self.btn_max, self.btn_close):
            btn.setFixedSize(15, 15)

        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_max.clicked.connect(self.toggle_max_restore)
        self.btn_close.clicked.connect(self.close)

        self.title_bar_layout.addWidget(self.title_label)
        self.title_bar_layout.addStretch()
        self.title_bar_layout.addWidget(self.btn_min)
        self.title_bar_layout.addWidget(self.btn_max)
        self.title_bar_layout.addWidget(self.btn_close)

        # Insert the title bar in the main layout (row 0)
        self.main_layout.addWidget(self.title_bar, 0, 0, 1, 12)

    def toggle_max_restore(self):
        """Toggle between Maximize and Restore."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def setup_content_area(self):
        """Set up the main content area (below the title bar)."""
        # Create a widget to hold left and right sections
        self.content_widget = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QGridLayout(self.content_widget)
        self.content_layout.setSpacing(0)

        # Create left and right sections
        self.setup_left_widget()
        self.setup_right_widget()

        # Add to layout (rows start at 1 to place below the title bar)
        self.main_layout.addWidget(self.content_widget, 1, 0, 12, 12)

    def setup_left_widget(self):
        """Left panel with buttons."""
        self.left_widget = QtWidgets.QWidget()
        self.left_widget.setObjectName('left_widget')
        self.left_layout = QtWidgets.QGridLayout()
        self.left_widget.setLayout(self.left_layout)

        # Menu buttons
        self.left_button_1 = QtWidgets.QPushButton(qtawesome.icon('fa.download', color='black'), "开始下载")
        self.left_button_1.setObjectName('left_button')
        self.left_button_1.setStyleSheet("color: black;")
        self.left_button_1.clicked.connect(self.start_download)

        self.left_button_2 = QtWidgets.QPushButton(qtawesome.icon('fa.folder-open', color='black'), "保存目录")
        self.left_button_2.setObjectName('left_button')
        self.left_button_2.setStyleSheet("color: black;")
        self.left_button_2.clicked.connect(self.browse_path)
        # Label or title in the left panel
        self.left_label_1 = QtWidgets.QPushButton("配置列表")
        self.left_label_1.setObjectName('left_label')
        self.left_label_1.setStyleSheet("color: black;")

        # Add them to the layout
        self.left_layout.addWidget(self.left_label_1, 0, 0, 1, 1)
        self.left_layout.addWidget(self.left_button_1, 1, 0, 1, 1)
        self.left_layout.addWidget(self.left_button_2, 2, 0, 1, 1)

        # Place the left widget in the content layout
        self.content_layout.addWidget(self.left_widget, 0, 0, 12, 3)

    def setup_right_widget(self):
        """Right panel (inputs, progress bar, etc.)."""
        self.right_widget = QtWidgets.QWidget()
        self.right_widget.setObjectName('right_widget')
        self.right_layout = QtWidgets.QGridLayout()
        self.right_widget.setLayout(self.right_layout)

        self.setup_input_area()
        self.setup_download_options()
        self.setup_progress_area()

        self.content_layout.addWidget(self.right_widget, 0, 3, 12, 9)

    def setup_input_area(self):
        """设置输入区域"""
        input_widget = QtWidgets.QWidget()
        input_layout = QtWidgets.QGridLayout(input_widget)

        # SESSDATA输入框
        self.sessdata_label = QtWidgets.QLabel('SESSDATA:')
        self.sessdata_input = QtWidgets.QLineEdit()
        self.sessdata_input.setPlaceholderText("请输入SESSDATA")

        # BV号输入框
        self.bv_label = QtWidgets.QLabel('BV号:')
        self.bv_input = QtWidgets.QLineEdit()
        self.bv_input.setPlaceholderText("请输入BV号")

        # 检查按钮
        self.check_button = QtWidgets.QPushButton("检查视频")
        self.check_button.clicked.connect(self.check_video)

        input_layout.addWidget(self.sessdata_label, 0, 0)
        input_layout.addWidget(self.sessdata_input, 0, 1, 1, 3)
        input_layout.addWidget(self.bv_label, 1, 0)
        input_layout.addWidget(self.bv_input, 1, 1, 1, 2)
        input_layout.addWidget(self.check_button, 1, 3)

        self.right_layout.addWidget(input_widget, 0, 0, 2, 12)

    def setup_download_options(self):
        """设置下载选项区域"""
        options_widget = QtWidgets.QWidget()
        options_layout = QtWidgets.QGridLayout(options_widget)

        # 质量选择
        self.quality_label = QtWidgets.QLabel('视频质量:')
        self.quality_combo = QtWidgets.QComboBox()

        # 保存路径
        self.path_label = QtWidgets.QLabel('保存路径:')
        self.path_input = QtWidgets.QLineEdit()
        self.path_input.setText(os.path.join(os.path.expanduser("~"), "Downloads"))
        self.browse_button = QtWidgets.QPushButton("浏览")
        self.browse_button.clicked.connect(self.browse_path)

        options_layout.addWidget(self.quality_label, 0, 0)
        options_layout.addWidget(self.quality_combo, 0, 1, 1, 2)
        options_layout.addWidget(self.path_label, 1, 0)
        options_layout.addWidget(self.path_input, 1, 1, 1, 2)
        options_layout.addWidget(self.browse_button, 1, 3)

        self.right_layout.addWidget(options_widget, 2, 0, 2, 12)

    def setup_progress_area(self):
        """设置进度条区域"""
        progress_widget = QtWidgets.QWidget()
        progress_layout = QtWidgets.QGridLayout(progress_widget)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")

        self.status_label = QtWidgets.QLabel("就绪")
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)

        progress_layout.addWidget(self.progress, 0, 0, 1, 12)
        progress_layout.addWidget(self.status_label, 1, 0, 1, 12)

        self.right_layout.addWidget(progress_widget, 4, 0, 2, 12)

    def mousePressEvent(self, event):
        """Allow window dragging when user clicks on the title bar (or empty areas)."""
        # Check if the click is within the title bar's area
        if event.button() == QtCore.Qt.LeftButton:
            # Use geometry to check if click is on the title bar
            title_bar_geo = self.title_bar.geometry()
            global_pos = self.mapToGlobal(event.pos())
            title_bar_top_left = self.title_bar.mapToGlobal(title_bar_geo.topLeft())
            title_bar_bottom_right = self.title_bar.mapToGlobal(title_bar_geo.bottomRight())

            if (title_bar_top_left.x() <= global_pos.x() <= title_bar_bottom_right.x() and
                    title_bar_top_left.y() <= global_pos.y() <= title_bar_bottom_right.y()):
                self.m_flag = True
                self.m_Position = event.globalPos() - self.pos()
                event.accept()
            self.setCursor(QtGui.QCursor(QtCore.Qt.OpenHandCursor))

    def mouseMoveEvent(self, event):
        """Handle the window moving."""
        if self.m_flag and event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.m_Position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Unset dragging state."""
        self.m_flag = False
        self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def browse_path(self):
        """Choose save path."""
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "选择保存目录", self.path_input.text()
        )
        if path:
            self.path_input.setText(path)

    def check_video(self):
        """检查视频信息"""
        try:
            sessdata = self.sessdata_input.text().strip()
            bvid = self.bv_input.text().strip()
            if not sessdata or not bvid:
                QtWidgets.QMessageBox.warning(self, "警告", "请输入SESSDATA和BV号")
                return

            self.status_label.setText("正在检查视频信息...")
            self.progress.setValue(20)

            self.downloader.set_cookie(sessdata)
            if not self.downloader.inspect_bvid(bvid):
                QtWidgets.QMessageBox.warning(self, "警告", "无效的BV号")
                self.status_label.setText("视频检查失败")
                self.progress.setValue(0)
                return

            cid = self.downloader.video.get_cid(bvid, 1)
            title = self.downloader.get_title(bvid)
            quality_list = self.downloader.video.get_quality(bvid, cid)

            self.quality_combo.clear()
            quality_map = {
                127: "8K",
                120: "4K",
                116: "1080P高码率",
                112: "1080P+",
                80: "1080P",
                64: "720P",
                32: "480P",
                16: "360P"
            }
            for q in quality_list:
                self.quality_combo.addItem(f"{quality_map.get(q, f'{q}')} - {q}", q)

            self.progress.setValue(100)
            self.status_label.setText("视频信息获取成功")
            QtWidgets.QMessageBox.information(self, "成功", f"视频信息获取成功！\n标题：{title}")

        except Exception as e:
            self.status_label.setText("视频检查失败")
            self.progress.setValue(0)
            QtWidgets.QMessageBox.critical(self, "错��", f"检查视频时出错：{str(e)}")

    def start_download(self):
        """开始下载"""
        try:
            sessdata = self.sessdata_input.text().strip()
            bvid = self.bv_input.text().strip()
            save_path = self.path_input.text().strip()
            if not all([sessdata, bvid, save_path]):
                QtWidgets.QMessageBox.warning(self, "警告", "请填写所有必要信息")
                return

            quality = self.quality_combo.currentData()
            if not quality:
                QtWidgets.QMessageBox.warning(self, "警告", "请先检查视频并选择质量")
                return

            self.status_label.setText("正在下载...")
            self.progress.setValue(20)

            self.downloader.set_cookie(sessdata)
            videore, audiore = self.downloader.video.get_video(bvid, pages=1, quality=quality)

            self.progress.setValue(50)
            self.status_label.setText("正在保存文件...")

            filename_temp = self.downloader.save(save_path, videore, audiore)

            self.progress.setValue(80)
            self.status_label.setText("正在合并音视频...")

            title = self.downloader.get_title(bvid)
            self.downloader.merge_videos(filename_temp, os.path.join(save_path, title))

            self.progress.setValue(100)
            self.status_label.setText("下载完成！")
            QtWidgets.QMessageBox.information(self, "成功", "视频下载完成！")

        except Exception as e:
            self.status_label.setText("下载失败")
            self.progress.setValue(0)
            QtWidgets.QMessageBox.critical(self, "错误", f"下载过程中出错：{str(e)}")

    def init_style(self):
        """Apply styles to the UI."""
        self.main_widget.setStyleSheet('''
            QWidget {
                background-color: #FFFFFF;
                border-radius: 10px;
            }
        ''')
        self.title_bar.setStyleSheet('''
            QWidget#title_bar {
                background-color: #2B2B2B;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QLabel#title_label {
                color: #FFFFFF;
                font-size: 16px;
                font-weight: bold;
                padding-left: 5px;
            }
            QPushButton {
                border: none;
                background-color: #2B2B2B;
            }
            QPushButton:hover {
                background-color: #383838;
            }
        ''')

        self.left_widget.setStyleSheet('''
            QWidget#left_widget {
                background-color: #2B2B2B;
                border-bottom-left-radius: 10px;
            }
            QPushButton#left_label {
                border: none;
                color: white;
                font-size: 16px;
                font-weight: 700;
                padding: 15px;
                text-align: center;
            }
            QPushButton#left_button {
                border: none;
                color: white;
                font-size: 14px;
                font-weight: 500;
                padding: 10px 0;
                padding-left: 30px;
                text-align: left;
                text-align: center;  /* 改为居中对齐 */
                margin: 5px 20px;    /* 添加左右边距 */
            }
            QPushButton#left_button:hover {
                border-left: 4px solid #F76677;
                font-weight: 700;
                background-color: #383838;
                border-radius: 5px;  /* 添加圆角 */
            }
        ''')

        self.right_widget.setStyleSheet('''
            QWidget#right_widget {
                background-color: #FFFFFF;
                border-bottom-right-radius: 10px;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
                font-weight: 500;
                padding: 10px;
                border: none;
            }
            QLineEdit {
                border: 1px solid #DCE1E8;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #FFFFFF;
            }
            QLineEdit:focus {
                border: 1px solid #4A90E2;
                outline: none;
            }
            QPushButton {
                border: 1px solid #DCE1E8;
                border-radius: 6px;
                padding: 8px 16px;
                background-color: #4A90E2;
                color: white;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
            QPushButton:pressed {
                background-color: #2D66A3;
            }
            QComboBox {
                border: 1px solid #DCE1E8;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: #FFFFFF;
            }
            QComboBox:hover {
                border: 1px solid #4A90E2;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
            QProgressBar {
                border: none;
                border-radius: 4px;
                text-align: center;
                background-color: #F5F5F5;
            }
            QProgressBar::chunk {
                background-color: #4A90E2;
                border-radius: 4px;
            }
            QLabel#status_label {
                color: #666666;
                font-size: 13px;
            }
        ''')

        # Style for the custom minimize, maximize, close buttons
        self.btn_min.setStyleSheet('''
            QPushButton {
                background: #6DDF6D;
                border-radius: 7px;
            }
            QPushButton:hover {
                background: #50C050;
            }
        ''')
        self.btn_max.setStyleSheet('''
            QPushButton {
                background: #F7D674;
                border-radius: 7px;
            }
            QPushButton:hover {
                background: #F6C846;
            }
        ''')
        self.btn_close.setStyleSheet('''
            QPushButton {
                background: #F76677;
                border-radius: 7px;
            }
            QPushButton:hover {
                background: #F54E50;
            }
        ''')


def main():
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

    app = QtWidgets.QApplication(sys.argv)

    # 获取屏幕分辨率
    screen_geometry = QtWidgets.QApplication.desktop().availableGeometry()
    screen_width = screen_geometry.width()
    screen_height = screen_geometry.height()

    # 计算窗口目标尺寸：取屏幕宽高的三分之一，但限制最大值为 800×600
    target_width = min(int(screen_width / 1.5), 800)
    target_height = min(int(screen_height / 1.5), 600)

    gui = BiliDownloaderGUI()
    gui.resize(target_width, target_height)
    gui.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
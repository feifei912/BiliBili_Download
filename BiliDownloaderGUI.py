import os
import sys
import json
import time
import asyncio
import qtawesome
from PyQt5 import QtCore, QtGui, QtWidgets
from BiliVideoDownloader import BiliVideoDownloader


class BiliDownloaderGUI(QtWidgets.QMainWindow):
    # 定义类级别的信号
    download_progress = QtCore.pyqtSignal(int, str)

    def __init__(self):
        # 首先调用父类的初始化
        super().__init__()

        # 设置程序图标
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'favicon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        else:
            # 如果没有找到图标文件，使用 qtawesome 的图标作为备选
            self.setWindowIcon(qtawesome.icon('fa.download', color='#4A90E2'))

        # 初始化所有实例变量
        self.downloader = BiliVideoDownloader()
        self.m_flag = False
        self.m_Position = None
        # 配置文件路径
        self.config_file = os.path.join(os.path.expanduser("~"), ".bilidownloader_config.json")
        self.config = {
            'last_save_path': os.path.join(os.path.expanduser("~"), "Downloads")
        }
        # 历史记录文件路径
        self.history_file = os.path.join(os.path.expanduser("~"), ".bilidownloader_history.json")

        # 加载配置
        self.load_config()

        # 设置窗口属性
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # 创建主布局
        self.main_widget = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QGridLayout(self.main_widget)
        self.main_layout.setSpacing(0)
        self.setCentralWidget(self.main_widget)

        # 设置界面组件
        self.setup_title_bar()
        self.setup_content_area()
        self.init_style()

        # 连接信号到更新函数
        self.download_progress.connect(self.update_progress)

    def update_progress(self, value, status):
        """更新进度条和状态标签"""
        self.progress.setValue(value)
        self.status_label.setText(status)

    def load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
        except Exception as e:
            print(f"加载配置文件失败: {e}")

    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def cleanup_temp_files(self, temp_dir):
        """清理临时文件夹"""
        try:
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"清理临时文件失败: {str(e)}")

    def setup_title_bar(self):
        """创建自定义标题栏，包含右上角控制按钮"""
        self.title_bar = QtWidgets.QWidget()
        self.title_bar.setObjectName("title_bar")
        self.title_bar_layout = QtWidgets.QHBoxLayout(self.title_bar)
        self.title_bar_layout.setContentsMargins(45, 0, 10, 0)

        # 左侧标题标签
        self.title_label = QtWidgets.QLabel("哔哩哔哩下载器")
        self.title_label.setStyleSheet("color: white; background-color: transparent;")
        self.title_label.setAutoFillBackground(True)
        self.title_label.setObjectName("title_label")
        self.title_label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)

        # 右侧的控件按钮
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

        # 在主布局中插入标题栏（第 0 行）
        self.main_layout.addWidget(self.title_bar, 0, 0, 1, 12)

    def toggle_max_restore(self):
        """在最大化和还原之间切换"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def setup_content_area(self):
        """设置主要内容区域(标题栏下方)"""
        # 创建用于容纳左右两部分的组件
        self.content_widget = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QGridLayout(self.content_widget)
        self.content_layout.setSpacing(0)

        # 创建左右两部分
        self.setup_left_widget()
        self.setup_right_widget()

        # 添加到布局中(从第1行开始，位于标题栏下方)
        self.main_layout.addWidget(self.content_widget, 1, 0, 12, 12)

    def setup_left_widget(self):
        """左侧面板包含按钮"""
        self.left_widget = QtWidgets.QWidget()
        self.left_widget.setObjectName('left_widget')
        self.left_layout = QtWidgets.QGridLayout()
        self.left_widget.setLayout(self.left_layout)

        # 左侧标签
        self.left_label_1 = QtWidgets.QPushButton("配置列表")
        self.left_label_1.setObjectName('left_label')
        self.left_label_1.setStyleSheet("color: black;")

        # 左侧按钮
        self.left_button_1 = QtWidgets.QPushButton(qtawesome.icon('fa.download', color='black'), "开始下载")
        self.left_button_1.setObjectName('left_button')
        self.left_button_1.setStyleSheet("color: black;")
        self.left_button_1.clicked.connect(self.start_download)

        self.left_button_2 = QtWidgets.QPushButton(qtawesome.icon('fa.folder-open', color='black'), "打开目录")
        self.left_button_2.setObjectName('left_button')
        self.left_button_2.setStyleSheet("color: black;")
        self.left_button_2.clicked.connect(self.browse_path)

        # 添加历史记录按钮
        self.left_button_3 = QtWidgets.QPushButton(qtawesome.icon('fa.history', color='black'), "下载历史")
        self.left_button_3.setObjectName('left_button')
        self.left_button_3.setStyleSheet("color: black;")
        self.left_button_3.clicked.connect(self.show_history)

        # 将按钮和标签添加到左侧布局中
        self.left_layout.addWidget(self.left_label_1, 0, 0, 1, 1)
        self.left_layout.addWidget(self.left_button_1, 2, 0, 1, 1)
        self.left_layout.addWidget(self.left_button_2, 1, 0, 1, 1)
        self.left_layout.addWidget(self.left_button_3, 3, 0, 1, 1)

        # 将左侧组件添加到主布局中
        self.content_layout.addWidget(self.left_widget, 0, 0, 12, 3)

    def setup_right_widget(self):
        """右侧面板包含输入框、下载选项和进度条"""
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

        # SESSDATA输入框和标签
        self.sessdata_label = QtWidgets.QLabel('SESSDATA:')
        self.sessdata_input = QtWidgets.QLineEdit()
        self.sessdata_input.setPlaceholderText("请输入SESSDATA")

        # 添加保存cookie的复选框
        self.save_cookie_checkbox = QtWidgets.QCheckBox("记住cookie（不建议在公共设备上使用）")
        self.save_cookie_checkbox.setObjectName("save_cookie_checkbox")
        # 根据配置设置复选框状态
        self.save_cookie_checkbox.setChecked(self.config.get('save_cookie', False))
        # 如果之前保存了SESSDATA，自动填充
        if self.config.get('save_cookie') and self.config.get('sessdata'):
            self.sessdata_input.setText(self.config['sessdata'])

        # BV号输入框和标签
        self.bv_label = QtWidgets.QLabel('BV号:')
        self.bv_input = QtWidgets.QLineEdit()
        self.bv_input.setPlaceholderText("请输入BV号")

        # 检查按钮
        self.check_button = QtWidgets.QPushButton("检查视频")
        self.check_button.clicked.connect(self.check_video)

        # 修改布局，调整复选框位置使其与SESSDATA对齐
        input_layout.addWidget(self.sessdata_label, 0, 0)  # SESSDATA标签
        input_layout.addWidget(self.sessdata_input, 0, 1, 1, 3)  # SESSDATA输入框
        input_layout.addWidget(self.save_cookie_checkbox, 1, 1, 1, 3)  # 复选框右移，与输入框对齐
        input_layout.addWidget(self.bv_label, 2, 0)  # BV号标签
        input_layout.addWidget(self.bv_input, 2, 1, 1, 2)  # BV号输入框
        input_layout.addWidget(self.check_button, 2, 3)  # 检查按钮

        # 设置布局的间距
        input_layout.setContentsMargins(10, 10, 10, 10)  # 设置外边距
        input_layout.setSpacing(10)  # 设置组件之间的间距

        self.right_layout.addWidget(input_widget, 0, 0, 2, 12)

    def setup_download_options(self):
        """设置下载选项区域"""
        options_widget = QtWidgets.QWidget()
        options_layout = QtWidgets.QGridLayout(options_widget)

        # 质量选择
        self.quality_label = QtWidgets.QLabel('视频质量:')
        self.quality_combo = QtWidgets.QComboBox()

        # 保存路径 - 使用配置中的路径
        self.path_label = QtWidgets.QLabel('保存路径:')
        self.path_input = QtWidgets.QLineEdit()
        self.path_input.setText(self.config['last_save_path'])
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
        """允许用户点击标题栏进行窗口拖动"""
        if event.button() == QtCore.Qt.LeftButton:
            # 使用几何位置检查点击是否在标题栏区域
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
        """处理窗口移动"""
        if self.m_flag and event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.m_Position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """取消拖动状态"""
        self.m_flag = False
        self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

    def browse_path(self):
        """选择保存路径"""
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, "选择保存目录", self.path_input.text()
        )
        if path:
            self.path_input.setText(path)
            # 保存新的路径到配置
            self.config['last_save_path'] = path
            self.save_config()

    def load_history(self):
        """加载下载历史记录
        从history_file加载JSON格式的历史记录
        如果文件不存在或出错则返回空列表
        """
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载历史记录失败: {e}")
        return []

    def save_history(self, download_info):
        """保存下载历史记录
        Args:
            download_info: 包含下载信息的字典,包括标题、清晰度、保存路径等
        将新的下载记录添加到历史记录中,并限制最多保存100条
        """
        try:
            history = self.load_history()
            # 添加时间戳
            download_info['timestamp'] = QtCore.QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')
            history.append(download_info)
            # 只保留最近100条记录
            if len(history) > 100:
                history = history[-100:]
            # 保存到文件
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def show_history(self):
        """显示下载历史记录窗口
        创建一个新窗口显示所有下载记录
        使用表格形式展示,包含时间、标题、清晰度、保存路径等信息
        """
        history = self.load_history()
        if not history:
            QtWidgets.QMessageBox.information(self, "下载历史", "暂无下载记录")
            return

        # 创建历史记录窗口
        history_dialog = QtWidgets.QDialog(self)
        history_dialog.setWindowTitle("下载历史")
        history_dialog.setMinimumWidth(500)
        history_dialog.setMinimumHeight(400)

        # 创建表格并设置列
        table = QtWidgets.QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["时间", "视频标题", "清晰度", "保存路径"])
        # 自动调整列宽
        table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        # 填充数据(倒序显示,最新的在上面)
        table.setRowCount(len(history))
        for row, item in enumerate(reversed(history)):
            table.setItem(row, 0, QtWidgets.QTableWidgetItem(item.get('timestamp', '')))
            table.setItem(row, 1, QtWidgets.QTableWidgetItem(item.get('title', '')))
            table.setItem(row, 2, QtWidgets.QTableWidgetItem(item.get('quality', '')))
            table.setItem(row, 3, QtWidgets.QTableWidgetItem(item.get('save_path', '')))

        # 设置窗口布局
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(table)
        history_dialog.setLayout(layout)

        history_dialog.exec_()

    def check_video(self):
        """检查视频信息"""
        try:
            sessdata = self.sessdata_input.text().strip()
            bvid = self.bv_input.text().strip()
            if not sessdata or not bvid:
                QtWidgets.QMessageBox.warning(self, "警告", "请输入SESSDATA和BV号")
                return

            # 保存cookie配置
            self.config['save_cookie'] = self.save_cookie_checkbox.isChecked()
            if self.config['save_cookie']:
                self.config['sessdata'] = sessdata
            else:
                self.config['sessdata'] = ''
            self.save_config()

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
            QtWidgets.QMessageBox.critical(self, "错误", f"检查视频时出错：{str(e)}")

    def start_download(self):
        """开始下载处理"""
        try:
            # 获取并验证必要的输入参数
            sessdata = self.sessdata_input.text().strip()
            bvid = self.bv_input.text().strip()
            save_path = self.path_input.text().strip()

            # 检查必要参数是否完整
            if not all([sessdata, bvid, save_path]):
                QtWidgets.QMessageBox.warning(self, "警告", "请填写所有必要信息")
                return

            # 保存cookie配置
            self.config['save_cookie'] = self.save_cookie_checkbox.isChecked()
            if self.config['save_cookie']:
                self.config['sessdata'] = sessdata
            else:
                self.config['sessdata'] = ''
            self.save_config()

            # 获取选择的视频质量
            quality = self.quality_combo.currentData()
            if not quality:
                QtWidgets.QMessageBox.warning(self, "警告", "请先检查视频并选择质量")
                return

            # 创建下载器实例并传入进度回调
            self.downloader = BiliVideoDownloader(
                progress_callback=lambda progress, status: self.download_progress.emit(progress, status)
            )

            # 更新状态显示
            self.status_label.setText("正在下载...")
            self.progress.setValue(0)

            # 设置下载器的cookie
            self.downloader.set_cookie(sessdata)

            # 获取视频和音频流
            videore, audiore = self.downloader.video.get_video(bvid, pages=1, quality=quality)

            # 创建临时文件路径
            temp_dir = os.path.join(save_path, '.temp')
            os.makedirs(temp_dir, exist_ok=True)
            filename_temp = os.path.join(temp_dir, str(int(time.time())))

            # 获取视频标题
            title = self.downloader.get_title(bvid)
            final_path = os.path.join(save_path, title)

            # 开始下载
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(
                    self.downloader.download_both(filename_temp, videore, audiore)
                )
            finally:
                loop.close()

            if not success:
                raise Exception("下载失败")

            # 在合并之前直接发送进度信号
            self.download_progress.emit(90, "正在合并视频，请稍后...")
            QtWidgets.QApplication.processEvents()  # 确保UI更新

            # 合并视频
            if not self.downloader.merge_videos(filename_temp, final_path):
                raise Exception("合并失败")

            # 合并完成后发送完成信号
            self.download_progress.emit(100, "下载完成！")

            # 清理临时文件夹
            try:
                if os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"清理临时文件夹失败: {str(e)}")

            # 保存下载历史记录
            download_info = {
                'title': title,
                'quality': f"{self.quality_combo.currentText()}",
                'save_path': save_path,
                'bvid': bvid,
                'timestamp': QtCore.QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')
            }
            self.save_history(download_info)

            # 保存新的配置
            self.config['last_save_path'] = save_path
            self.save_config()

            # 显示成功消息
            success_message = f"视频下载完成！\n保存位置：{final_path}.mp4"
            QtWidgets.QMessageBox.information(self, "成功", success_message)

        except Exception as e:
            # 更新失败状态
            self.status_label.setText("下载失败")
            self.progress.setValue(0)

            # 显示详细的错误信息
            error_message = (
                f"下载过程中出错：\n{str(e)}\n\n"
                "可能的原因：\n"
                "1. 网络连接不稳定\n"
                "2. 存储空间不足\n"
                "3. 视频文件过大\n"
                "4. SESSDATA无效或过期\n"
                "\n建议：\n"
                "- 检查网络连接\n"
                "- 确保有足够的存储空间\n"
                "- 尝试下载较低质量的视频\n"
                "- 更新SESSDATA"
            )
            QtWidgets.QMessageBox.critical(self, "错误", error_message)

            # 打印错误日志
            print(f"下载失败 - BV号: {bvid}, 错误信息: {str(e)}")

    def init_style(self):
        """设置窗口样式"""
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
                padding-left: 0px;
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
                    padding: 10px 0;
                    text-align: center;
                    margin: 5px 20px;
                }
                QPushButton#left_button {
                    border: none;
                    color: white;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 10px 0;
                    text-align: center;
                    margin: 5px 20px;
                }
                QPushButton#left_button:hover {
                    background-color: #383838;
                    border-radius: 5px;
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

        # 添加复选框样式
        self.save_cookie_checkbox.setStyleSheet('''
                QCheckBox {
                    color: #666666;
                    font-size: 12px;
                    padding: 5px 0;
                }
                QCheckBox:hover {
                    color: #333333;
                }
                QCheckBox:checked {
                    color: #4A90E2;
                }
            ''')

        # 控制按钮样式
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
import os
import re
import sys
import json
import time
import asyncio
import qtawesome
import subprocess
from PyQt5 import QtCore, QtGui, QtWidgets
from BiliVideoDownloader import BiliVideoDownloader
from ffmpeg_manager import FFmpegManager, get_ffmpeg


class EllipsisTableWidgetItem(QtWidgets.QTableWidgetItem):
    def __init__(self, text):
        super().__init__()
        self.full_text = text
        self.setTextWithEllipsis(text)

    def setTextWithEllipsis(self, text, width=500):
        """设置带省略号的文本"""
        # 创建一个QFontMetrics对象来计算文本宽度
        metrics = QtGui.QFontMetrics(self.font())
        # 如果文本宽度超过限制
        if metrics.width(text) > width:
            # 逐个字符尝试，直到找到合适的长度
            for i in range(len(text), 0, -1):
                truncated_text = text[:i] + '...'
                if metrics.width(truncated_text) <= width:
                    super().setText(truncated_text)
                    return
        # 如果文本没有超过限制，直接设置
        super().setText(text)

    def text(self):
        """返回完整的文本"""
        return self.full_text

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

    def extract_bv_number(self, input_str):
        """提取BV号"""
        bv_pattern = re.compile(r'BV[a-zA-Z0-9]{10}')

        # 检查输入是否是BV号
        if bv_pattern.match(input_str):
            return input_str

        # 如果输入是链接，从链接中提取BV号
        match = bv_pattern.search(input_str)
        if match:
            return match.group(0)

        raise ValueError("输入的字符串中未找到有效的BV号")

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

        # 修改配置列表为按钮
        self.config_button = QtWidgets.QPushButton(qtawesome.icon('fa.cog', color='black'), "配置")
        self.config_button.setObjectName('left_button')
        self.config_button.setStyleSheet("color: black;")
        self.config_button.clicked.connect(self.show_config)

        # 左侧按钮
        self.left_button_1 = QtWidgets.QPushButton(qtawesome.icon('fa.download', color='black'), "开始下载")
        self.left_button_1.setObjectName('left_button')
        self.left_button_1.setStyleSheet("color: black;")
        self.left_button_1.clicked.connect(self.start_download)

        self.left_button_2 = QtWidgets.QPushButton(qtawesome.icon('fa.folder-open', color='black'), "打开目录")
        self.left_button_2.setObjectName('left_button')
        self.left_button_2.setStyleSheet("color: black;")
        self.left_button_2.clicked.connect(self.open_current_directory)

        # 添加历史记录按钮
        self.left_button_3 = QtWidgets.QPushButton(qtawesome.icon('fa.history', color='black'), "下载历史")
        self.left_button_3.setObjectName('left_button')
        self.left_button_3.setStyleSheet("color: black;")
        self.left_button_3.clicked.connect(self.show_history)

        # 添加使用说明按钮
        self.help_button = QtWidgets.QPushButton(qtawesome.icon('fa.question-circle', color='black'), "使用说明")
        self.help_button.setObjectName('left_button')
        self.help_button.setStyleSheet("color: black;")
        self.help_button.clicked.connect(self.show_instructions)

        # 将按钮添加到左侧布局中
        self.left_layout.addWidget(self.config_button, 0, 0, 1, 1)
        self.left_layout.addWidget(self.left_button_1, 1, 0, 1, 1)
        self.left_layout.addWidget(self.left_button_2, 2, 0, 1, 1)
        self.left_layout.addWidget(self.left_button_3, 3, 0, 1, 1)
        self.left_layout.addWidget(self.help_button, 4, 0, 1, 1)

        # 将左侧组件添加到主布局中
        self.content_layout.addWidget(self.left_widget, 0, 0, 12, 3)

    def setup_right_widget(self):
        """右侧面板包含输入框、下载选项和进度条"""
        self.right_widget = QtWidgets.QWidget()
        self.right_widget.setObjectName('right_widget')
        self.right_layout = QtWidgets.QGridLayout(self.right_widget)

        # 创建并添加 QStackedWidget
        self.right_stack = QtWidgets.QStackedWidget()
        self.right_layout.addWidget(self.right_stack, 0, 0)

        # 创建配置页面
        self.config_widget = QtWidgets.QWidget()
        self.config_widget.setObjectName('config_widget')  # 添加对象名，用于样式设置
        self.config_layout = QtWidgets.QGridLayout(self.config_widget)

        # 将所有配置相关的组件添加到配置页面
        self.setup_config_page()
        self.right_stack.addWidget(self.config_widget)

        # 创建说明页面
        self.instruction_widget = QtWidgets.QWidget()
        self.instruction_widget.setObjectName('instruction_widget')  # 添加对象名，用于样式设置
        self.instruction_layout = QtWidgets.QVBoxLayout(self.instruction_widget)
        self.setup_instruction_area()
        self.right_stack.addWidget(self.instruction_widget)

        self.content_layout.addWidget(self.right_widget, 0, 3, 12, 9)

        # 默认显示说明页面
        self.right_stack.setCurrentWidget(self.config_widget)

    def setup_config_page(self):
        """设置配置页面，包含所有下载相关的组件"""
        # 创建输入区域
        input_widget = QtWidgets.QWidget()
        input_layout = QtWidgets.QGridLayout(input_widget)

        # SESSDATA输入框和标签
        self.sessdata_label = QtWidgets.QLabel('SESSDATA:')
        self.sessdata_input = QtWidgets.QLineEdit()
        self.sessdata_input.setPlaceholderText("请输入SESSDATA")

        # 添加保存cookie的复选框
        self.save_cookie_checkbox = QtWidgets.QCheckBox("记住cookie（不建议在公共设备上使用）")
        self.save_cookie_checkbox.setObjectName("save_cookie_checkbox")
        self.save_cookie_checkbox.setChecked(self.config.get('save_cookie', False))
        if self.config.get('save_cookie') and self.config.get('sessdata'):
            self.sessdata_input.setText(self.config['sessdata'])

        # BV号输入框和标签
        self.bv_label = QtWidgets.QLabel('视频链接:')
        self.bv_input = QtWidgets.QLineEdit()
        self.bv_input.setPlaceholderText("请输入BV号或视频链接")

        # 检查按钮
        self.check_button = QtWidgets.QPushButton("检查视频")
        self.check_button.setObjectName('check_button')  # 添加对象名，用于样式设置
        self.check_button.clicked.connect(self.check_video)

        # 设置输入区域布局
        input_layout.addWidget(self.sessdata_label, 0, 0)
        input_layout.addWidget(self.sessdata_input, 0, 1, 1, 3)
        input_layout.addWidget(self.save_cookie_checkbox, 1, 1, 1, 3)
        input_layout.addWidget(self.bv_label, 2, 0)
        input_layout.addWidget(self.bv_input, 2, 1, 1, 2)
        input_layout.addWidget(self.check_button, 2, 3)

        # 下载选项区域
        options_widget = QtWidgets.QWidget()
        options_layout = QtWidgets.QGridLayout(options_widget)

        # 质量选择
        self.quality_label = QtWidgets.QLabel('视频质量:')
        self.quality_combo = QtWidgets.QComboBox()

        # 保存路径
        self.path_label = QtWidgets.QLabel('保存路径:')
        self.path_input = QtWidgets.QLineEdit()
        self.path_input.setText(self.config['last_save_path'])
        self.browse_button = QtWidgets.QPushButton("浏览")
        self.browse_button.setObjectName('browse_button')  # 添加对象名，用于样式设置
        self.browse_button.clicked.connect(self.browse_path)

        # 设置下载选项布局
        options_layout.addWidget(self.quality_label, 0, 0)
        options_layout.addWidget(self.quality_combo, 0, 1, 1, 2)
        options_layout.addWidget(self.path_label, 1, 0)
        options_layout.addWidget(self.path_input, 1, 1, 1, 2)
        options_layout.addWidget(self.browse_button, 1, 3)

        # 进度条区域
        progress_widget = QtWidgets.QWidget()
        progress_layout = QtWidgets.QGridLayout(progress_widget)

        self.progress = QtWidgets.QProgressBar()
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")

        self.status_label = QtWidgets.QLabel("就绪")
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)

        # 设置进度条布局
        progress_layout.addWidget(self.progress, 0, 0, 1, 12)
        progress_layout.addWidget(self.status_label, 1, 0, 1, 12)

        # FFmpeg信息和按钮区域
        ffmpeg_widget = QtWidgets.QWidget()
        ffmpeg_layout = QtWidgets.QGridLayout(ffmpeg_widget)
        ffmpeg_label = QtWidgets.QLabel("请确保已经下载安装ffmpeg")
        ffmpeg_label.setObjectName('ffmpeg_label')

        check_ffmpeg_button = QtWidgets.QPushButton("检测是否已安装")
        check_ffmpeg_button.setIcon(qtawesome.icon('fa.search', color='white'))
        check_ffmpeg_button.setObjectName('check_ffmpeg_button')
        check_ffmpeg_button.clicked.connect(self.check_ffmpeg)

        download_ffmpeg_button = QtWidgets.QPushButton("下载安装")
        download_ffmpeg_button.setIcon(qtawesome.icon('fa.download', color='white'))
        download_ffmpeg_button.setObjectName('download_ffmpeg_button')
        download_ffmpeg_button.clicked.connect(self.download_ffmpeg)

        ffmpeg_layout.addWidget(ffmpeg_label, 0, 0, 1, 2)
        ffmpeg_layout.addWidget(check_ffmpeg_button, 0, 2)
        ffmpeg_layout.addWidget(download_ffmpeg_button, 0, 3)

        # 将所有组件添加到配置页面布局中
        self.config_layout.addWidget(input_widget, 0, 0, 2, 12)
        self.config_layout.addWidget(options_widget, 2, 0, 2, 12)
        self.config_layout.addWidget(progress_widget, 4, 0, 2, 12)
        self.config_layout.addWidget(ffmpeg_widget, 6, 0, 1, 12)

    def setup_instruction_area(self):
        """设置使用说明区域"""
        # 创建主容器
        instruction_container = QtWidgets.QWidget()
        instruction_layout = QtWidgets.QVBoxLayout(instruction_container)
        instruction_layout.setContentsMargins(20, 20, 20, 20)
        instruction_layout.setSpacing(15)

        # 创建说明文本编辑器
        instruction_text = QtWidgets.QTextEdit()
        instruction_text.setReadOnly(True)
        instruction_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E5E5E5;
                border-radius: 8px;
                padding: 15px;
                background-color: #FFFFFF;
                font-family: "Microsoft YaHei", Arial, sans-serif;
                line-height: 1.6;
            }
            QTextEdit:focus {
                border-color: #4A90E2;
            }
        """)

        # HTML内容，使用更现代的样式
        html_content = """
        <style>
            body {
                font-family: "Microsoft YaHei", Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }
            h2 {
                color: #2B2B2B;
                border-bottom: 2px solid #4A90E2;
                padding-bottom: 8px;
                margin-bottom: 20px;
            }
            .section {
                margin-bottom: 20px;
                padding: 15px;
                background: #F8F9FA;
                border-radius: 8px;
            }
            .section-title {
                color: #4A90E2;
                font-weight: bold;
                margin-bottom: 10px;
                font-size: 16px;
            }
            ul {
                margin: 0;
                padding-left: 20px;
            }
            li {
                margin: 8px 0;
            }
            .highlight {
                background-color: #FFF3CD;
                padding: 2px 5px;
                border-radius: 3px;
            }
            .note {
                color: #856404;
                background-color: #FFF3CD;
                border: 1px solid #FFEEBA;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            }
            .author-section {
                background: #E8F4FE;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
            }
            a {
                color: #4A90E2;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
        </style>

        <h2>哔哩哔哩下载器使用说明</h2>

        <div class="section">
            <div class="section-title">1. 获取Cookie(SESSDATA)</div>
            <ul>
                <li>登录bilibili网站</li>
                <li>按<span class="highlight">F12</span>打开开发者工具</li>
                <li>找到 <span class="highlight">Network(网络)</span> 标签，在左侧的<span class="highlight">Name(名称)</span>中选择<span class="highlight">web?</span>开头的请求</li>
                <li>在 <span class="highlight">Headers(标头)</span> 下找到 <span class="highlight">Request Headers(请求标头)</span></li>
                <li>在 <span class="highlight">Cookie</span> 中复制 <span class="highlight">SESSDATA</span> 的值</li>
            </ul>
            <div class="note">
                • 若无法找到<strong>web?</strong>开头的请求，请点击首页的轮播图更换一张轮播图<br>
                • <strong>SESSDATA</strong>中需要复制的是"SESSDATA=xxxxxx;"中的<strong>"xxxxxx"</strong>部分<br>
                • 请勿分享您的Cookie(SESSDATA)给陌生人，以免造成账号安全问题
            </div>
        </div>

        <div class="section">
            <div class="section-title">2. FFmpeg安装</div>
            <ul>
                <li>使用配置页面下方按钮检测FFmpeg是否已安装</li>
                <li>如未安装，点击配置页面下方的<span class="highlight">"下载安装"</span>按钮进行安装</li>
                <li><strong>注意：首次下载安装可能需要较长时间，请耐心等待FFmpeg下载完成</strong></li>
            </ul>
        </div>

        <div class="section">
            <div class="section-title">3. 下载视频</div>
            <ul>
                <li>点击"配置"按钮打开配置界面</li>
                <li>输入SESSDATA和视频BV号或链接</li>
                <li>点击"检查视频"获取视频信息</li>
                <li>选择视频质量和保存路径</li>
            </ul>
            <div class="note">
                <strong>清晰度说明：</strong><br>
                • 无Cookie：仅支持480P及以下清晰度<br>
                • 普通用户：最高支持1080P清晰度<br>
                • 大会员：支持1080P高帧率及以上清晰度
            </div>
        </div>

        <div class="section">
            <div class="section-title">4. 实用功能</div>
            <ul>
                <li><strong>打开目录</strong>：快速访问下载文件夹</li>
                <li><strong>下载历史</strong>：查看和管理历史下载记录</li>
                <li><strong>记住Cookie</strong>：可选择保存SESSDATA（请勿在公共设备使用）</li>
            </ul>
        </div>

        <div class="author-section">
            <div class="section-title">5. 关于作者 ( • ̀ω•́ )✧</div>
            <ul>
                <li>作者：feifei912</li>
                <li>项目主页：https://github.com/feifei912/BiliBili_Download</li>
                <li>欢迎Star和Fork(〃'▽'〃)</li>
            </ul>
        </div>
        """

        instruction_text.setHtml(html_content)

        # 将组件添加到主布局
        instruction_layout.addWidget(instruction_text)

        # 将主容器添加到说明页面布局
        self.instruction_layout.addWidget(instruction_container)

    def show_config(self):
        """显示配置界面"""
        self.right_stack.setCurrentWidget(self.config_widget)

    def show_instructions(self):
        """显示使用说明"""
        self.right_stack.setCurrentWidget(self.instruction_widget)

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
        self.save_cookie_checkbox.setChecked(self.config.get('save_cookie', False))
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
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(10)

        # 使用正确的布局方法添加到config_layout
        self.config_layout.addWidget(input_widget, 0, 0, 2, 12)

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
        """显示下载历史记录窗口"""
        history = self.load_history()
        if not history:
            QtWidgets.QMessageBox.information(self, "下载历史", "暂无下载记录")
            return

        # 创建历史记录窗口
        history_dialog = QtWidgets.QDialog(self)
        history_dialog.setWindowTitle("下载历史")
        history_dialog.setMinimumWidth(800)
        history_dialog.setMinimumHeight(500)

        # 创建表格
        table = QtWidgets.QTableWidget()
        table.setColumnCount(5)  # 增加一列用于删除按钮
        table.setHorizontalHeaderLabels(["时间", "视频标题", "清晰度", "保存路径", "操作"])

        # 设置表格属性
        table.setEditTriggers(QtWidgets.QTableWidget.DoubleClicked)  # 允许双击编辑
        table.setSelectionBehavior(QtWidgets.QTableWidget.SelectRows)  # 整行选择
        table.setSelectionMode(QtWidgets.QTableWidget.SingleSelection)  # 单行选择模式

        # 设置列宽
        table.setColumnWidth(0, 150)  # 时间列
        table.setColumnWidth(1, 300)  # 标题列
        table.setColumnWidth(2, 100)  # 清晰度列
        table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)  # 路径列自适应
        table.setColumnWidth(4, 60)  # 操作列

        # 创建右键菜单
        table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(lambda pos: self.show_history_context_menu(pos, table))

        # 填充数据
        table.setRowCount(len(history))
        for row, item in enumerate(reversed(history)):
            # 时间
            time_item = QtWidgets.QTableWidgetItem(item.get('timestamp', ''))
            time_item.setFlags(time_item.flags() & ~QtCore.Qt.ItemIsEditable)  # 设置不可编辑
            table.setItem(row, 0, time_item)

            # 标题 - 使用自定义的带省略号的显示
            title = item.get('title', '')
            title_item = EllipsisTableWidgetItem(title)
            title_item.setToolTip(title)  # 鼠标悬停显示完整标题
            table.setItem(row, 1, title_item)

            # 清晰度
            quality_item = QtWidgets.QTableWidgetItem(item.get('quality', ''))
            quality_item.setFlags(quality_item.flags() & ~QtCore.Qt.ItemIsEditable)
            table.setItem(row, 2, quality_item)

            # 保存路径
            path_item = QtWidgets.QTableWidgetItem(item.get('save_path', ''))
            path_item.setFlags(path_item.flags() & ~QtCore.Qt.ItemIsEditable)
            table.setItem(row, 3, path_item)

            # 删除按钮
            delete_btn = QtWidgets.QPushButton("删除")
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_history_item(r, table))
            table.setCellWidget(row, 4, delete_btn)

        # 调用刷新删除按钮函数
        self.refresh_delete_buttons(table)

        # 创建底部按钮
        clear_all_btn = QtWidgets.QPushButton("清空记录")
        clear_all_btn.clicked.connect(lambda: self.clear_all_history(table))

        # 设置布局
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(table)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(clear_all_btn)
        layout.addLayout(button_layout)
        history_dialog.setLayout(layout)

        history_dialog.exec_()

    def delete_history_item(self, row, table):
        """删除单条历史记录"""
        reply = QtWidgets.QMessageBox.question(
            self, '确认删除',
            '确定要删除这条记录吗？',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            history = self.load_history()
            real_index = len(history) - 1 - row  # 由于显示是倒序的，需要计算实际索引
            if 0 <= real_index < len(history):
                history.pop(real_index)
                self.save_history_list(history)
                table.removeRow(row)
                # 重新设置删除按钮连接
                self.refresh_delete_buttons(table)

    # 添加refresh_delete_buttons方法
    def refresh_delete_buttons(self, table):
        """重新设置删除按钮连接"""
        row_count = table.rowCount()
        for row in range(row_count):
            delete_btn = table.cellWidget(row, 4)
            if delete_btn:
                delete_btn.clicked.disconnect()
                delete_btn.clicked.connect(lambda checked, r=row: self.delete_history_item(r, table))

    def clear_all_history(self, table):
        """清空所有历史记录"""
        reply = QtWidgets.QMessageBox.question(
            self, '确认清空',
            '确定要清空所有下载记录吗？此操作不可恢复！',
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self.save_history_list([])  # 保存空列表
            table.setRowCount(0)

    def save_history_list(self, history):
        """保存历史记录列表"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def show_history_context_menu(self, pos, table):
        """显示右键菜单"""
        menu = QtWidgets.QMenu()
        item = table.itemAt(pos)
        if item:
            row = item.row()
            delete_action = menu.addAction("删除")
            delete_action.triggered.connect(lambda: self.delete_history_item(row, table))

        clear_action = menu.addAction("清空所有记录")
        clear_action.triggered.connect(lambda: self.clear_all_history(table))

        menu.exec_(table.viewport().mapToGlobal(pos))

    # 在 BiliDownloaderGUI 类中添加一个新的方法来打开目录
    def open_current_directory(self):
        """打开当前设置的下载目录"""
        current_path = self.path_input.text().strip()
        if os.path.exists(current_path):
            # 根据不同的操作系统使用不同的命令打开文件夹
            if sys.platform == 'win32':
                os.startfile(current_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.Popen(['open', current_path])
            else:  # linux
                subprocess.Popen(['xdg-open', current_path])
        else:
            QtWidgets.QMessageBox.warning(self, "警告", "目录不存在！")

    def check_ffmpeg(self):
        """检测是否已安装FFmpeg"""
        try:
            ffmpeg_path = FFmpegManager().ensure_ffmpeg()
            if ffmpeg_path:
                QtWidgets.QMessageBox.information(self, "FFmpeg检测", f"系统已安装FFmpeg: {ffmpeg_path}")
            else:
                QtWidgets.QMessageBox.warning(self, "FFmpeg检测", "系统未安装FFmpeg")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"检测FFmpeg时出错: {str(e)}")

    def download_ffmpeg(self):
        """下载安装FFmpeg"""
        try:
            ffmpeg_path = get_ffmpeg()
            QtWidgets.QMessageBox.information(self, "FFmpeg下载", f"FFmpeg成功安装: {ffmpeg_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"下载安装FFmpeg时出错: {str(e)}")

    def check_video(self):
        """检查视频信息"""
        try:
            sessdata = self.sessdata_input.text().strip()
            input_str = self.bv_input.text().strip()
            if not sessdata or not input_str:
                QtWidgets.QMessageBox.warning(self, "警告", "请输入SESSDATA和BV号或链接")
                return

            # 提取BV号
            bvid = self.extract_bv_number(input_str)

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
            input_str = self.bv_input.text().strip()
            save_path = self.path_input.text().strip()

            # 检查必要参数是否完整
            if not all([sessdata, input_str, save_path]):
                QtWidgets.QMessageBox.warning(self, "警告", "请填写所有必要信息")
                return

            # 提取BV号
            bvid = self.extract_bv_number(input_str)

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

            # 在合并之前直接发送进度信信号
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

        self.right_stack.setStyleSheet('''
            QStackedWidget {
                border: none;
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

        table_style = '''
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QTableWidget::item:selected {
                background-color: #e6f3ff;
                color: black;
            }
            QPushButton {
                padding: 5px 10px;
                border-radius: 3px;
                background-color: #4A90E2;
                color: white;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
        '''
        # 配置页面样式
        self.config_widget.setStyleSheet('''
                QWidget#config_widget {
                    background-color: #FFFFFF;
                    border-bottom-right-radius: 10px;
                }
                QLabel {
                    color: #333333;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 10px;
                }
                QLineEdit {
                    border: 1px solid #DCE1E8;
                    border-radius: 6px;
                    padding: 8px 12px;
                    background-color: #FFFFFF;
                }
                QLineEdit:focus {
                    border: 1px solid #4A90E2;
                }
                QPushButton#check_button, QPushButton#browse_button {
                    border: 1px solid #DCE1E8;
                    border-radius: 6px;
                    padding: 8px 16px;
                    background-color: #4A90E2;
                    color: white;
                    font-weight: 500;
                    min-width: 80px;
                }
                QPushButton#check_button:hover, QPushButton#browse_button:hover {
                    background-color: #357ABD;
                }
                QComboBox {
                    border: 1px solid #DCE1E8;
                    border-radius: 6px;
                    padding: 8px 12px;
                    background-color: #FFFFFF;
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

        # 说明页面样式
        self.instruction_widget.setStyleSheet('''
                QWidget#instruction_widget {
                    background-color: #FFFFFF;
                    border-bottom-right-radius: 10px;
                }
                QTextEdit {
                    border: none;
                    background-color: #FFFFFF;
                    color: #333333;
                    font-size: 14px;
                    padding: 20px;
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
# B站视频下载软件

## 项目简介
B站视频下载软件是一款用Python编写的桌面应用程序，允许用户从Bilibili网站下载视频。用户可以输入BV号或B站视频链接，选择视频质量，并保存到指定路径。

## 功能特点
- 支持输入BV号或B站视频链接进行视频下载
- 支持选择视频质量
- 保存下载历史记录
- 支持断点续传
- 自动合并视频和音频文件

## 安装步骤

### 前置条件
- Python 3.13或更高版本
  - pip包管理工具
- 或者下载提供的exe文件

### 安装依赖项
1. 克隆项目到本地：
   ```bash
   git clone https://github.com/feifei912/BiliBili_Download.git
   cd BiliBili_Download
   ```

2. 安装所需依赖项：
   ```bash
   pip install -r requirements.txt
   ```

### 运行程序
1. 进入项目目录：
   ```bash
   cd BiliBili_Download
   ```

2. 运行主程序：
   ```bash
   python BiliDownloaderGUI.py
   ```

## 使用方法
1. 启动程序后，界面上方输入框中输入SESSDATA。
2. 在BV号输入框中输入BV号或B站视频链接。
3. 点击“检查视频”按钮，软件会自动获取视频信息。
4. 在视频质量下拉框中选择所需的视频质量。
5. 选择保存路径，点击“开始下载”按钮开始下载视频。
6. 下载完成后，视频会自动合并音频和视频文件，保存到指定路径。

## 文件说明

### BiliDownloaderGUI.py
该文件是程序的主界面文件，包含了主界面布局、用户交互逻辑、视频检查和下载功能。

### BiliVideoDownloader.py
该文件包含视频下载和合并的核心逻辑，包括断点续传、分块下载和文件合并等功能。

## 常见问题

### libpng warning: iCCP: known incorrect sRGB profile
这个警告信息表示在处理PNG图片时发现了一个已知的错误的sRGB配置文件。这个警告通常不会影响图像的正常使用，可以忽略。如果想消除这个警告，可以使用图片编辑工具重新保存图像文件，确保使用正确的sRGB配置文件。

### 如何获取SESSDATA？
SESSDATA是B站的用户认证信息，可以通过浏览器开发者工具获取。登录B站后，打开开发者工具，找到请求头中的cookie信息，复制其中的SESSDATA值。

## 贡献
欢迎贡献代码和提出改进建议！请提交Pull Request或在Issues中提出问题。

## 许可证
本项目基于MIT许可证，请参阅LICENSE文件了解更多信息。


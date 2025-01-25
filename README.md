<div align="center">

# BiliBili视频下载软件

[![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/feifei912/BiliBili_Download)](https://github.com/feifei912/BiliBili_Download/commits/master)
[![GitHub Stars](https://img.shields.io/github/stars/feifei912/BiliBili_Download)](https://github.com/feifei912/BiliBili_Download/stargazers)

</div>

## 目录
- [项目介绍](#项目介绍)
- [主要功能](#主要功能)
- [技术特性](#技术特性) 
- [软件架构](#软件架构)
- [安装说明](#安装说明)
- [使用教程](#使用教程)
- [常见问题](#常见问题)
- [更新日志](#更新日志)
- [许可证](#许可证)

## 项目介绍

BiliBili视频下载软件是一款基于Python开发的桌面应用程序，提供简洁直观的图形界面，支持B站视频的高质量下载。本软件使用PyQt5开发界面，支持多种清晰度选择、断点续传、自定义保存等功能，为用户提供流畅的下载体验。

## 主要功能

### 核心功能
- 支持BV号和视频链接多种输入方式
- 支持从360P到8K的多种清晰度选择
- 支持断点续传和分块下载
- 智能合并音视频流
- 自定义保存路径
- 下载历史管理

### 用户体验
- 现代化图形界面设计
- 实时下载进度显示
- 自动记忆用户配置
- 支持Cookie记忆功能
- 提供详细使用说明

### 系统集成
- 自动FFmpeg检测与安装(Windows)
- 智能错误处理与提示
- 支持自动清理临时文件

## 技术特性

- **并发下载**: 使用异步IO和多线程实现高效下载
- **智能分块**: 根据文件大小自动调整下载分块
- **断点续传**: 支持中断后继续下载功能
- **内存优化**: 大文件分块处理，避免内存溢出
- **错误重试**: 实现指数退避重试机制
- **性能监控**: 实时监控下载进度

## 软件架构

```
project/
├── BiliDownloaderGUI.py     # GUI界面实现
├── BiliVideoDownloader.py    # 视频下载核心逻辑
├── ffmpeg_manager.py         # FFmpeg管理模块
└── static/                   # 静态资源
    └── favicon.ico          # 程序图标
```

## 安装说明

### 环境要求
- Python 3.13+
- FFmpeg (可由程序自动安装)
- Windows/Linux/MacOS
- Linux/MacOS需要手动安装FFmpeg

### 依赖安装
```bash
git clone https://github.com/feifei912/BiliBili_Download.git
cd BiliBili_Download
pip install -r requirements.txt
```

### 主要依赖
```
PyQt5>=5.15.0
requests>=2.25.0
aiohttp>=3.8.0
aiofiles>=0.8.0
qtawesome>=1.0.0
```

## 使用教程

### 1. 获取Cookie (SESSDATA)
1. 登录bilibili网站
2. 按F12打开开发者工具
3. 选择Network标签
4. 找到带有SESSDATA的请求头
5. 复制SESSDATA值

### 2. 视频下载
1. 启动程序: `python BiliDownloaderGUI.py`
2. 输入SESSDATA和视频BV号/链接
3. 点击"检查视频"获取信息
4. 选择清晰度和保存路径
5. 点击"开始下载"

### 3. 清晰度说明
- 无Cookie: 最高480P
- 普通用户: 最高1080P
- 大会员: 支持1080P高帧率以上

## 常见问题

1. **清晰度受限**
   - 确认Cookie是否正确配置
   - 检查账号权限级别

2. **下载失败**
   - 检查网络连接
   - 确认磁盘空间充足
   - 查看是否需要更新Cookie

3. **FFmpeg相关**
   - 使用内置功能检测FFmpeg
   - 点击"下载安装"自动配置

## 更新日志

### v1.0.0 (2025-01-20 至 2025-01-25)
- 实现基础下载功能
- 添加GUI界面
- 支持清晰度选择
- 添加下载历史
- 实现断点续传
- 优化下载性能
- 添加FFmpeg管理
- 改进错误处理
- 完善使用说明
- 优化用户体验

## 许可证

本项目基于 MIT 许可证开源，详见 [LICENSE](LICENSE) 文件。

---

## 技术支持

### 参与贡献
1. Fork 本仓库
2. 创建新特性分支
3. 提交代码
4. 创建 Pull Request

### 问题反馈
- 提交 Issue
- 加入讨论组
- 发送邮件

### 致谢
- [BiliVideo_Download](https://github.com/keyblues/BiliVideo_Download) 提供下载实现思路
- 感谢所有项目贡献者

如果这个项目对您有帮助，欢迎:
- ⭐ Star 支持项目
- 🔃 Fork 开发新功能
- 📢 分享给其他人

# BiliBili视频下载软件

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/feifei912/BiliBili_Download)](https://github.com/feifei912/BiliBili_Download/commits/main)

## 目录
- [项目介绍](#项目介绍)
- [功能特点](#功能特点)
- [软件架构](#软件架构)
- [开发环境](#开发环境)
- [安装教程](#安装教程)
- [使用说明](#使用说明)
- [常见问题](#常见问题)
- [更新日志](#更新日志)
- [许可证](#许可证)

## 项目介绍

BiliBili视频下载软件是一款基于Python开发的桌面应用程序，提供简洁的图形界面，支持B站视频的批量下载、清晰度选择等功能。本软件使用PyQt5开发界面，支持Windows、Linux和MacOS等多个平台。

## 功能特点

- **图形界面**：基于PyQt5开发的现代化界面，操作简单直观
- **多清晰度支持**：支持从360P到8K的多种清晰度选择（部分清晰度需要大会员）
- **断点续传**：支持下载中断后继续下载
- **智能解析**：支持BV号、链接等多种输入方式
- **历史记录**：保存下载历史，方便重复下载
- **文件管理**：支持自定义保存路径和文件命名

## 软件架构

```
project/
├── BiliVideoDownloader.py    # 视频下载核心实现
├── BiliDownloaderGUI.py      # 图形界面实现
└── static/                   # 静态资源目录
    └── icons/               # 图标资源
```

## 开发环境

### 基础环境
- Python 3.13
- Windows/Linux/MacOS

### 主要依赖
```bash
PyQt5>=5.15.0
requests>=2.25.0
qtawesome>=1.0.0
```

## 安装教程

1. **克隆项目**
```bash
git clone https://github.com/feifei912/BiliBili_Download.git
cd BiliBili_Download
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

## 使用说明

### 图形界面模式
```bash
python BiliDownloaderGUI.py
```

### 主要功能
1. **视频下载**
   - 输入BV号或视频链接
   - 选择视频清晰度
   - 选择保存目录
   - 点击"开始下载"

2. **配置设置**
   - 设置默认下载目录
   - 配置用户Cookie（大会员需要）
   - 自定义文件命名格式

3. **下载管理**
   - 查看下载历史
   - 打开下载目录
   - 中断/继续下载

## 常见问题

1. **无法下载高清晰度视频？**
   
   - 720P及以上清晰度需要输入用户cookie，否则只能最高480P

   - 1080P高帧率及以上清晰度需要检查是否配置了正确的大会员Cookie
   
2. **下载速度慢？**
   - 检查网络连接
   - 降低视频清晰度
   
3. **下载失败？**
   - 检查视频链接是否有效
   - 确认是否有足够的磁盘空间
   - 查看错误日志获取详细信息

## 更新日志

### v1.0.0 (2025-01-25)

- 完善视频下载功能

- 优化图形界面设计
- 支持自定义保存路径
- 添加下载历史记录
- 增加断点续传功能
- 添加记忆功能，不用重复输入cookie以及保存路径
- 优化下载链接逻辑
- 美化图形界面设计
- 添加使用说明

## 许可证

本项目基于 MIT 许可证开源，详见 [LICENSE](LICENSE) 文件。

---

### 贡献
- 欢迎提交 Issue 和 Pull Request
- 代码规范遵循 PEP 8
- 提交代码前请先进行测试

### 致谢
感谢所有为本项目提供反馈和建议的用户。

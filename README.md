<div align="center">

# BiliBili视频下载软件

<p align="center">
    <em>🎬 一款简单易用的哔哩哔哩视频下载工具 </em>
</p>

[![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/feifei912/BiliBili_Download)](https://github.com/feifei912/BiliBili_Download/commits/master)
[![GitHub Stars](https://img.shields.io/github/stars/feifei912/BiliBili_Download)](https://github.com/feifei912/BiliBili_Download/stargazers)


</div>

## 🎯 特性一览

- 🚀 **高性能**: 支持异步IO和多线程下载
- 🎨 **简洁界面**: 现代化GUI设计，操作直观
- 📦 **多功能**: 最高支持8K、断点续传、自定义保存等
- 🔧 **易配置**: 自动安装FFmpeg，一键配置(Windows)
- 📝 **记忆功能**: 自动保存用户配置和下载历史
- ⚡ **智能下载**: 自动分块和音视频合并

## 📚 目录
- [软件介绍](#-软件介绍)
- [安装说明](#-安装说明)
- [使用教程](#-使用教程)
- [功能展示](#-功能展示)
- [技术特性](#-技术特性)
- [常见问题](#-常见问题)
- [更新日志](#-更新日志)
- [贡献指南](#-贡献指南)

## 🎵 软件介绍

本软件是一款基于Python开发的B站视频下载工具，提供图形化界面，支持以下功能：

- 支持从`360P`到`8K`的清晰度选择
- 支持`BV号`和`视频链接`输入
- 提供实时下载进度显示
- 支持自定义保存路径
- 内置下载历史管理

## ⚙️ 安装说明

### 环境要求
```bash
- Python 3.13+
- FFmpeg (Windows可自动安装)
- 支持Windows/Linux/MacOS
```

### 快速安装
```bash
# 克隆仓库
git clone https://github.com/feifei912/BiliBili_Download.git

# 进入目录
cd BiliBili_Download

# 安装依赖
pip install -r requirements.txt
```

## 🎮 功能展示

<details>
<summary>配置界面</summary>
<img src="https://github.com/user-attachments/assets/20978fdb-858e-4c1a-9dea-1a6777975c27" alt="配置界面">
</details>

<details>
<summary>下载历史界面</summary>
<img src="https://github.com/user-attachments/assets/51115e35-4ac8-4cda-a320-412c75080e0a" alt="下载历史界面">
</details>

<details>
<summary>使用说明界面</summary>
<img src="https://github.com/user-attachments/assets/2f39865b-41f8-4125-a2c9-17e392b6662a" alt="使用说明1">
<img src="https://github.com/user-attachments/assets/8517ecd6-00c7-4db5-a984-010ae9eb4bca" alt="使用说明2">
</details>

## 📝 使用教程

### 🔐 Cookie获取

<details>
<summary><b>详细步骤</b></summary>

#### 📝 基本步骤
1. 登录 [bilibili](https://www.bilibili.com/) 网站
2. 按 <kbd>F12</kbd> 打开开发者工具
3. 切换到 `Network` (网络) 标签
4. 找到以 `web?` 开头的请求
5. 在 `Headers` 中找到 `Cookie` 值
6. 提取 `SESSDATA=xxxxxx;` 中的 `xxxxxx` 部分

#### 💡 小贴士
- 如果找不到 `web?` 开头的请求，可以尝试：
  - 刷新页面
  - 点击首页轮播图
  - 切换任意视频
- 复制时请仅复制 `SESSDATA` 的值，不需要包含 `SESSDATA=` 和末尾的 `;`

#### ⚠️ 安全提醒
- 请勿将您的 Cookie 分享给他人
- 定期更新 Cookie 以确保安全
- 在公共设备上使用后及时退出登录
</details>

### 视频下载
```bash
# 1. 启动程序
python BiliDownloaderGUI.py

# 2. 输入必要信息
- SESSDATA
- 视频BV号/链接

# 3. 选择下载参数
- 选择清晰度
- 设置保存路径

# 4. 开始下载
```

### 清晰度权限
| 用户类型 | 最高清晰度 |
|---------|------------|
| 未登录   | 480P      |
| 普通用户 | 1080P     |
| 大会员   | 8K        |

## 🔧 技术特性

- **下载优化**
  - 异步IO下载
  - 智能分块处理
  - 断点续传支持
  - 内存优化管理
  
- **错误处理**
  - 自动重试机制
  - 智能错误提示
  - 异常状态恢复

## ❓ 常见问题

<details>
<summary>Q: 清晰度选择受限？</summary>
A: 检查Cookie是否正确，以及账号权限等级
</details>

<details>
<summary>Q: 下载失败怎么办？</summary>
A: 检查网络连接和存储空间，确认Cookie是否过期
</details>

<details>
<summary>Q: FFmpeg相关问题？</summary>
A: 使用程序内置的检测和安装功能
</details>

## 📅 更新日志

### v1.0.0 (2025-01-25)
- ✨ 新增基础下载功能
- 🎨 优化界面设计
- 🔧 添加配置管理
- 📝 完善使用文档

## 🤝 贡献指南

欢迎提交问题和建议！提交代码请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 提交 Pull Request

## 📜 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

<div align="center">

### 🌟 支持项目

如果这个项目对您有帮助，请考虑给它一个星标 ⭐

[问题反馈](https://github.com/feifei912/BiliBili_Download/issues) · [功能建议](https://github.com/feifei912/BiliBili_Download/pulls) · [项目主页](https://github.com/feifei912/BiliBili_Download)

</div>
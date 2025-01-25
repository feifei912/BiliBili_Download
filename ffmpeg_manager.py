import platform
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path
import subprocess


class FFmpegManager:
    FFMPEG_URLS = [
        'https://ghproxy.cn/https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip',
        'https://gh.llkk.cc/https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip',
        'https://github.site/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip',
        'https://github.store/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip',
    ]

    def __init__(self):
        if platform.system() != 'Windows':
            raise RuntimeError("这个版本只服务于Windows系统")

        # 设置FFmpeg路径
        self.base_path = Path(__file__).parent / 'ffmpeg'
        self.bin_path = self.base_path / 'bin'
        self.ffmpeg_path = self.bin_path / 'ffmpeg.exe'

    def check_system_ffmpeg(self):
        """检查系统是否已安装FFmpeg"""
        try:
            # 检查环境变量中的ffmpeg
            result = subprocess.run(['ffmpeg', '-version'],
                                    capture_output=True,
                                    text=True)
            if result.returncode == 0:
                # 获取实际的ffmpeg路径
                if platform.system() == 'Windows':
                    result = subprocess.run(['where', 'ffmpeg'],
                                            capture_output=True,
                                            text=True)
                    if result.returncode == 0:
                        return result.stdout.strip().split('\n')[0]
            return None
        except:
            return None

    def ensure_ffmpeg(self):
        """确保FFmpeg可用，优先使用系统FFmpeg"""
        # 先检查系统FFmpeg
        system_ffmpeg = self.check_system_ffmpeg()
        if system_ffmpeg:
            print(f"检查系统中的FFmpeg: {system_ffmpeg}")

            return system_ffmpeg

        # 检查已下载的FFmpeg
        if self.ffmpeg_path.exists():
            return str(self.ffmpeg_path)

        return None

    def download_ffmpeg(self):
        """下载并解压FFmpeg"""
        for url in self.FFMPEG_URLS:
            try:
                # 创建临时目录
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    archive_path = temp_path / "ffmpeg.zip"

                    # 下载文件
                    print(f"从 {url} 下载 FFmpeg...")
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req) as response:
                        with open(archive_path, 'wb') as out_file:
                            shutil.copyfileobj(response, out_file)

                    # 解压文件
                    print("解压 FFmpeg...")
                    with zipfile.ZipFile(archive_path) as zf:
                        # 查找ffmpeg.exe
                        ffmpeg_exe = next(
                            name for name in zf.namelist()
                            if name.endswith('ffmpeg.exe')
                        )

                        # 创建bin目录
                        self.bin_path.mkdir(parents=True, exist_ok=True)

                        # 解压ffmpeg.exe
                        zf.extract(ffmpeg_exe, temp_path)

                        # 移动到最终位置
                        shutil.move(temp_path / ffmpeg_exe, self.ffmpeg_path)

                    print("FFmpeg 成功安装!")
                    return str(self.ffmpeg_path)

            except Exception as e:
                print(f"从 {url} 下载失败: {e}")

        raise RuntimeError("FFmpeg下载或解压失败")


def get_ffmpeg():
    """获取FFmpeg路径的便捷函数"""
    manager = FFmpegManager()
    ffmpeg_path = manager.ensure_ffmpeg()
    if ffmpeg_path:
        return ffmpeg_path
    return manager.download_ffmpeg()


if __name__ == '__main__':
    # 测试代码
    try:
        ffmpeg_path = get_ffmpeg()
        print(f"FFmpeg 路径: {ffmpeg_path}")
    except Exception as e:
        print(f"错误: {e}")
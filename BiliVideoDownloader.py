import time
import re
import os
import asyncio
import aiohttp
import aiofiles
import requests
import platform
from concurrent.futures import ThreadPoolExecutor


class BiliVideoDownloader:
    def __init__(self, progress_callback=None):
        self.video = Video()
        self.error_download = []
        self.progress_callback = progress_callback

    def set_cookie(self, sess_data):
        """设置cookie"""
        self.video.cookies = {"SESSDATA": sess_data}

    async def download_file(self, url, filename, headers, cookies, description, progress_callback):
        """
        下载单个文件
        Args:
            url: 下载链接
            filename: 保存的文件名
            headers: 请求头
            cookies: cookie信息
            description: 下载描述（用于显示进度）
            progress_callback: 进度回调函数
        Returns:
            bool: 下载是否成功
        """
        total_size = 0
        downloaded = [0]
        part_files = []
        max_retries = 5
        base_chunk_size = 1024 * 1024  # 1MB
        max_concurrent_downloads = 8
        download_timeout = 30
        semaphore = asyncio.Semaphore(max_concurrent_downloads)

        async def get_content_length():
            """获取文件总大小"""
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.head(url, headers=headers, cookies=cookies) as response:
                        return int(response.headers.get('content-length', 0))
            except Exception as e:
                print(f"获取文件大小失败: {str(e)}")
                return 0

        async def download_chunk(start, end, chunk_index):
            """
            下载文件块
            Args:
                start: 开始位置
                end: 结束位置
                chunk_index: 块索引
            """
            part_file = f"{filename}.part{chunk_index}"
            part_files.append(part_file)

            async with semaphore:
                for retry in range(max_retries):
                    try:
                        chunk_headers = headers.copy()
                        chunk_headers['Range'] = f'bytes={start}-{end}'

                        timeout = aiohttp.ClientTimeout(total=download_timeout * (retry + 1))
                        async with aiohttp.ClientSession(timeout=timeout) as session:
                            async with session.get(url, headers=chunk_headers, cookies=cookies) as response:
                                if response.status != 206:
                                    raise Exception(f"服务器不支持断点续传: {response.status}")

                                async with aiofiles.open(part_file, 'wb') as f:
                                    async for data in response.content.iter_chunked(base_chunk_size):
                                        if data:
                                            await f.write(data)
                                            downloaded[0] += len(data)
                                            if total_size:
                                                percentage = min(100, downloaded[0] * 100 / total_size)
                                                if progress_callback:
                                                    try:
                                                        await progress_callback(percentage,
                                                                                f"{description}: {percentage:.1f}%")
                                                    except Exception as e:
                                                        print(f"进度回调出错: {str(e)}")
                                            await asyncio.sleep(0.001)
                                return True

                    except Exception as e:
                        if retry < max_retries - 1:
                            wait_time = (retry + 1) * 2  # 指数退避
                            print(f"\n下载块 {chunk_index} 失败: {str(e)}, {wait_time}秒后重试...")
                            await asyncio.sleep(wait_time)
                        else:
                            print(f"\n下载块 {chunk_index} 最终失败: {str(e)}")
                            raise

        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # 获取文件大小
            total_size = await get_content_length()
            if total_size == 0:
                raise Exception("无法获取文件大小")

            # 根据文件大小动态调整分块
            chunk_size = max(total_size // 32, 5 * 1024 * 1024)  # 最小5MB
            chunk_count = (total_size + chunk_size - 1) // chunk_size

            # 创建下载任务
            tasks = []
            for i in range(chunk_count):
                start = i * chunk_size
                end = min(start + chunk_size - 1, total_size - 1)
                tasks.append(download_chunk(start, end, i))

            # 执行所有下载任务
            await asyncio.gather(*tasks)

            # 合并文件块
            async with aiofiles.open(filename, 'wb') as outfile:
                for i in range(chunk_count):
                    part_file = f"{filename}.part{i}"
                    if os.path.exists(part_file):
                        async with aiofiles.open(part_file, 'rb') as infile:
                            while True:
                                chunk = await infile.read(base_chunk_size)
                                if not chunk:
                                    break
                                await outfile.write(chunk)
                                await asyncio.sleep(0.001)  # 避免阻塞

            return True

        except Exception as e:
            print(f"\n下载失败: {str(e)}")
            return False

        finally:
            # 清理分块文件
            for part_file in part_files:
                try:
                    if os.path.exists(part_file):
                        os.remove(part_file)
                except Exception as e:
                    print(f"清理分块文件失败: {str(e)}")

    async def download_both(self, filename_temp, videore, audiore):
        """
        下载视频和音频文件
        """
        try:
            async def progress_wrapper(progress, status, file_type):
                if file_type == "audio":
                    # 音频下载占20%
                    total_progress = progress * 0.2
                else:  # video
                    # 视频下载占70% (20-90%)
                    total_progress = 20 + (progress * 0.7)

                if self.progress_callback:
                    self.progress_callback(int(total_progress), status)

            # 先下载音频
            audio_success = await self.download_file(
                audiore.url,
                f"{filename_temp}.mp3",
                self.video.headers,
                self.video.cookies,
                "音频下载",
                lambda p, s: progress_wrapper(p, s, "audio")
            )

            if not audio_success:
                raise Exception("音频下载失败")

            # 下载视频
            video_success = await self.download_file(
                videore.url,
                f"{filename_temp}.mp4",
                self.video.headers,
                self.video.cookies,
                "视频下载",
                lambda p, s: progress_wrapper(p, s, "video")
            )

            if not video_success:
                raise Exception("视频下载失败")

            return True

        except Exception as e:
            print(f"下载失败: {str(e)}")
            return False

    def merge_videos(self, filename_temp, filename_new):
        """
        合并视频和音频文件
        """
        try:
            import subprocess
            video_path = f"{filename_temp}.mp4"
            audio_path = f"{filename_temp}.mp3"

            if not os.path.exists(video_path) or not os.path.exists(audio_path):
                raise ValueError("视频或音频文件丢失")

            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-y',
                f"{filename_new}.mp4"
            ]

            # 准备subprocess参数
            kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE
            }
            if platform.system() == 'Windows':
                kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

            process = subprocess.Popen(cmd, **kwargs)
            stdout, stderr = process.communicate()

            if process.returncode != 0:
                raise Exception(f"FFmpeg失败: {stderr.decode()}")

            # 清理临时文件
            try:
                os.remove(video_path)
                os.remove(audio_path)
            except Exception as e:
                print(f"清理临时文件失败: {str(e)}")

            return True

        except Exception as e:
            print(f"合并失败: {str(e)}")
            return False

        except Exception as e:
            print(f"合并失败: {str(e)}")
            return False

    def save(self, directory, videore, audiore):
        """优化后的异步保存视频和音频文件"""
        filename_temp = os.path.join(directory, str(time.time()))
        max_retries = 5  # 增加重试次数
        base_chunk_size = 1024 * 1024  # 1MB 基础块大小
        max_concurrent_downloads = 8  # 限制并发数
        download_timeout = 30  # 增加超时时间

        async def download_file(url, filename, headers, cookies, description):
            total_size = 0
            downloaded = [0]
            part_files = []
            semaphore = asyncio.Semaphore(max_concurrent_downloads)  # 控制并发数

            async def get_content_length():
                async with aiohttp.ClientSession() as session:
                    async with session.head(url, headers=headers, cookies=cookies) as response:
                        return int(response.headers.get('content-length', 0))

            async def download_chunk(start, end, chunk_index):
                part_file = f"{filename}.part{chunk_index}"
                part_files.append(part_file)

                async with semaphore:  # 使用信号量控制并发
                    for retry in range(max_retries):
                        try:
                            chunk_headers = headers.copy()
                            chunk_headers['Range'] = f'bytes={start}-{end}'

                            timeout = aiohttp.ClientTimeout(total=download_timeout * (retry + 1))
                            async with aiohttp.ClientSession(timeout=timeout) as session:
                                async with session.get(url, headers=chunk_headers, cookies=cookies) as response:
                                    if response.status != 206:
                                        raise Exception(f"服务器不支持断点续传: {response.status}")

                                    # 使用临时文件写入数据
                                    async with aiofiles.open(part_file, 'wb') as f:
                                        async for data in response.content.iter_chunked(base_chunk_size):
                                            if data:
                                                await f.write(data)
                                                downloaded[0] += len(data)
                                                # 更新进度
                                                if total_size:
                                                    percentage = min(100, downloaded[0] * 100 / total_size)
                                                    print(f"\r{description}: {percentage:.1f}%", end="", flush=True)
                                                # 定期释放控制权
                                                await asyncio.sleep(0.001)
                                    return True

                        except Exception as e:
                            if retry < max_retries - 1:
                                wait_time = (retry + 1) * 2  # 指数退避
                                print(f"\n下载块 {chunk_index} 失败: {str(e)}, {wait_time}秒后重试...")
                                await asyncio.sleep(wait_time)
                            else:
                                print(f"\n下载块 {chunk_index} 最终失败: {str(e)}")
                                raise

            try:
                # 获取文件大小
                total_size = await get_content_length()
                if total_size == 0:
                    raise Exception("无法获取文件大小")

                # 根据文件大小动态调整分块
                chunk_size = max(total_size // 32, 5 * 1024 * 1024)  # 最小5MB
                chunk_count = (total_size + chunk_size - 1) // chunk_size

                # 创建下载任务
                tasks = []
                for i in range(chunk_count):
                    start = i * chunk_size
                    end = min(start + chunk_size - 1, total_size - 1)
                    tasks.append(download_chunk(start, end, i))

                # 执行所有下载任务
                await asyncio.gather(*tasks)

                # 合并文件块
                async with aiofiles.open(filename, 'wb') as outfile:
                    for i in range(chunk_count):
                        part_file = f"{filename}.part{i}"
                        if os.path.exists(part_file):
                            async with aiofiles.open(part_file, 'rb') as infile:
                                while True:
                                    chunk = await infile.read(base_chunk_size)
                                    if not chunk:
                                        break
                                    await outfile.write(chunk)
                                await asyncio.sleep(0.001)  # 避免阻塞

                return True

            except Exception as e:
                print(f"\n下载失败: {str(e)}")
                return False

            finally:
                # 清理分块文件
                for part_file in part_files:
                    try:
                        if os.path.exists(part_file):
                            os.remove(part_file)
                    except Exception as e:
                        print(f"清理分块文件失败: {str(e)}")

        async def download_both():
            tasks = []
            # 视频下载任务
            tasks.append(download_file(
                videore.url,
                f"{filename_temp}.mp4",
                self.video.headers,
                self.video.cookies,
                "视频下载"
            ))
            # 音频下载任务
            tasks.append(download_file(
                audiore.url,
                f"{filename_temp}.mp3",
                self.video.headers,
                self.video.cookies,
                "音频下载"
            ))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            return all(isinstance(r, bool) and r for r in results)

        # 使用线程池执行异步任务
        with ThreadPoolExecutor(max_workers=2) as executor:
            future = executor.submit(lambda: asyncio.run(download_both()))
            try:
                success = future.result()
                if not success:
                    self.cleanup_file_parts(filename_temp)
                    raise Exception("下载过程中发生错误")
                return filename_temp
            except Exception as e:
                self.cleanup_file_parts(filename_temp)
                raise Exception(f"下载失败: {str(e)}")

    # 原始代码的辅助方法
    def remove(self, filename_temp):
        try:
            os.remove(f"{filename_temp}.mp4")
            os.remove(f"{filename_temp}.mp3")
        except:
            pass

    def cleanup_file_parts(self, filename_temp):
        """清理所有相关的临时文件，包括分块文件"""
        # 删除主文件
        for ext in [".mp4", ".mp3"]:
            try:
                if os.path.exists(filename_temp + ext):
                    os.remove(filename_temp + ext)
            except Exception as e:
                print(f"删除{ext}文件时出错: {str(e)}")

        # 删除所有分块文件
        base_dir = os.path.dirname(filename_temp)
        base_name = os.path.basename(filename_temp)
        try:
            for file in os.listdir(base_dir):
                if file.startswith(base_name) and ".part" in file:
                    try:
                        os.remove(os.path.join(base_dir, file))
                    except Exception as e:
                        print(f"删除分块文件{file}时出错: {str(e)}")
        except Exception as e:
            print(f"清理分块文件时出错: {str(e)}")

    def get_bit(self, videore, audiore):
        return int(videore.headers.get('Content-Length')) + int(audiore.headers.get('Content-Length'))

    def size(self, bit):
        value = int(bit)
        units = ["B", "KB", "MB", "GB", "TB", "PB"]
        size = 1024.0
        for i in range(len(units)):
            if (value / size) < 1:
                return "%.2f%s" % (value, units[i])
            value = value / size

    def is_directory_exist(self, directory):
        return os.path.exists(directory)

    def title_filterate(self, title):
        return re.sub(r"\/|\,|\:|\*|\?|\<|\>|\\|\&|$|$|\.\.|\||\'|\"", "", title)

    def inspect_bvid(self, bvid):
        if bool(re.match(r'^BV[a-zA-Z0-9]{10}$', bvid)):
            return self.video.get_info(bvid) is not False
        return False

    def get_title(self, bvid):
        data = self.video.get_info(bvid)
        title = data['data']['title']
        return self.title_filterate(title)

    def get_title_collection(self, bvid, pages):
        data = self.video.get_info(bvid)
        title = data['data']['pages'][pages - 1]['part']
        return 'P' + str(pages) + ' ' + self.title_filterate(title)


class Video:
    def __init__(self):
        self.api_info = 'https://api.bilibili.com/x/web-interface/view?bvid={}'
        self.api_url = 'https://api.bilibili.com/x/player/wbi/playurl?bvid={}&cid={}&fnval=4048'
        self.headers = {
            "referer": "https://www.bilibili.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/108.0.0.0 Safari/537.36 "
        }
        # 初始化 cookies
        self.cookies = {}

    def get_info(self, bvid):
        """ 获取视频信息 """
        url = self.api_info.format(bvid)
        response = requests.get(url=url, headers=self.headers)
        if response.status_code == 200:
            if response.json()['code'] == 0:
                return response.json()
            else:
                return False
        else:
            return False

    def get_cid(self, bvid, pages):
        """ 获取视频cid """
        url = self.api_info.format(bvid)
        response = requests.get(url=url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 0:
                cid = data['data']['pages'][pages - 1]['cid']
                return cid
            else:
                return False
        else:
            return False

    def get_quality(self, bvid, cid):
        """ 获取视频质量列表 """
        url = self.api_url.format(bvid, cid)
        response = requests.get(url=url, headers=self.headers, cookies=self.cookies)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 0:
                quality_dict = set()  # 使用set而不是list来存储
                if 'dash' in data['data']:
                    for i in data['data']['dash']['video']:
                        quality_dict.add(i['id'])
                return sorted(list(quality_dict), reverse=True)  # 转换回列表并降序排序
            else:
                print(f"获取质量列表时出错: {data['message']}")
                return []
        else:
            print(f"请求质量列表时出错: {response.status_code}")
            return []

    def request_url(self, bvid, cid):
        """ 获取视频和音频的url """
        url = self.api_url.format(bvid, cid)
        response = requests.get(url=url, headers=self.headers, cookies=self.cookies)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 0:
                return data['data']
            else:
                print(f"获取视频和音频URL时出错: {data['message']}")
                return None
        else:
            print(f"请求视频和音频URL时出错: {response.status_code}")
            return None

    def get_video(self, bvid, pages=1, quality=80):
        """ 视频下载 """
        cid = self.get_cid(bvid, pages)
        quality_list = self.get_quality(bvid, cid)
        print(f"可用质量参数: {quality_list}")
        if quality not in quality_list:
            raise ValueError(f"无效的质量参数: {quality}")
        data = self.request_url(bvid, cid)
        if data is None:
            raise ValueError("无法获取视频和音频的URL")
        video_url = next(i['baseUrl'] for i in data['dash']['video'] if i['id'] == quality)
        audio_url = data['dash']['audio'][0]['baseUrl']
        print(f"视频 URL: {video_url}")
        print(f"音频 URL: {audio_url}")
        self.videore = requests.get(url=video_url, headers=self.headers, cookies=self.cookies, stream=True)
        self.audiore = requests.get(url=audio_url, headers=self.headers, cookies=self.cookies, stream=True)
        return self.videore, self.audiore
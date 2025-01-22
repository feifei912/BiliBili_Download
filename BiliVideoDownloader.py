import time
import re
import os
import asyncio
import aiohttp
import aiofiles
import requests
from concurrent.futures import ThreadPoolExecutor


class BiliVideoDownloader:
    def __init__(self):
        self.video = Video()
        self.error_download = []

    def set_cookie(self, sess_data):
        self.video.cookies = {"SESSDATA": sess_data}

    def download_video(self, bvid, directory, quality=80, pages=1):
        """下载单个或多个视频"""
        if not self.inspect_bvid(bvid):
            print('无效的BV号')
            return False

        # 确保目录存在
        if not self.is_directory_exist(directory):
            os.makedirs(directory)
            if not self.is_directory_exist(directory):
                print('无效的目录')
                return False

        # 如果是合集，创建目录
        if pages > 1:
            directory = os.path.join(directory, self.get_title(bvid))
            if not os.path.exists(directory):
                os.makedirs(directory)

        # 下载视频
        for page in range(1, pages + 1):
            print(f"\n正在处理视频 {page} 的 {pages}")
            self.download_single_video(bvid, directory, quality, page)

        if self.error_download:
            print(f"BV: {bvid} 下载失败的页面: {self.error_download}")
        else:
            print(f"BV: {bvid} 所有下载已完成")

    def download_single_video(self, bvid, directory, quality, page=1):
        """下载单个视频"""
        try:
            # 获取视频和音频流
            videore, audiore = self.video.get_video(bvid, pages=page, quality=quality)
            total_size = self.get_bit(videore, audiore)
            print(f"BV: {bvid} 页面: {page} 状态: 下载中, 质量: {quality}, 大小: {self.size(total_size)}")

            # 下载并合并
            filename_temp = self.save(directory, videore, audiore)
            print(f"BV: {bvid} 页面: {page} 状态: 正在合并文件...")

            title = self.get_title_collection(bvid, page) if page > 1 else self.get_title(bvid)
            self.merge_videos(filename_temp, os.path.join(directory, title))
            print(f"BV: {bvid} 页面: {page} 状态: 完成")
            return True
        except Exception as e:
            print(f"下载视频时出错: {str(e)}")
            self.error_download.append(page)
            return False

    def merge_videos(self, filename_temp, filename_new):
        """合并视频和音频文件"""
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

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            stdout, stderr = process.communicate()

            if process.returncode != 0:
                self.cleanup_file_parts(filename_temp)
                raise Exception(f"FFmpeg失败: {stderr.decode()}")

            # 清理临时文件
            self.cleanup_file_parts(filename_temp)

        except Exception as e:
            self.cleanup_file_parts(filename_temp)
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

    def set_cookie(self, cookie):
        """ 设置cookie """
        self.cookies = {"SESSDATA": cookie}

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


def main():
    downloader = BiliVideoDownloader()

    # 创建保存目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    directory = os.path.join(parent_dir, "video")

    if not os.path.exists(directory):
        os.makedirs(directory)

    # 获取SESSDATA和BV号
    sess_data = input("输入SESSDATA cookie: ")
    downloader.set_cookie(sess_data)
    bvid = input("输入BV号: ")

    # 先获取可用的视频质量选项
    cid = downloader.video.get_cid(bvid, 1)  # 获取第一个视频的cid
    if cid:
        quality_list = downloader.video.get_quality(bvid, cid)
        print("\n可用的视频质量选项：")
        # 注意：80及以上的质量参数需要B站大会员账号的cookie才能下载
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
            print(f"- {q}: {quality_map.get(q, '未知质量')}")
    else:
        print("获取视频信息失败")
        return

    # 让用户选择质量
    while True:
        try:
            quality = int(input("\n请输入想要下载的视频质量代码: "))
            if quality in quality_list:
                break
            else:
                print("输入的质量代码无效，请从上面的列表中选择")
        except ValueError:
            print("请输入有效的数字")

    # 询问是否为合集
    is_collection = input("是否为合集? (y/n): ").lower() == 'y'
    pages = int(input("输入要下载的视频数量: ")) if is_collection else 1

    # 开始下载
    downloader.download_video(bvid, directory, quality, pages)

if __name__ == '__main__':
    main()
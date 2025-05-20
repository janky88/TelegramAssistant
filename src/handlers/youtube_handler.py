import os
import re
import logging
import yt_dlp
import tempfile
from ..utils.file_utils import sanitize_filename, move_file, ensure_dirs
from ..constants import YOUTUBE_TEMP_DIR, YOUTUBE_DEST_DIR, YOUTUBE_AUDIO_DIR

logger = logging.getLogger(__name__)


class YouTubeHandler:
    def __init__(self, config):
        self.config = config
        self.yt_format = config["youtube_download"].get("format", "bv*+ba/best")
        self.cookies = config["youtube_download"].get("cookies", "")
        self.audio_convert = config.get("youtube_audio_convert", {})

        # 确保目录存在
        ensure_dirs(YOUTUBE_TEMP_DIR, YOUTUBE_DEST_DIR, YOUTUBE_AUDIO_DIR)

    def _get_ydl_opts(self, temp_cookie_file=None):
        """获取yt-dlp选项"""
        ydl_opts = {
            "format": self.yt_format,
            "outtmpl": os.path.join(YOUTUBE_TEMP_DIR, "%(title).100s-%(id)s.%(ext)s"),
            "ignoreerrors": True,
            "ignore_no_formats_error": True,
            "restrictfilenames": True,
            "windowsfilenames": True,
            "merge_output_format": "mp4",
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",
                }
            ],
        }

        # 添加音频转换配置
        if self.audio_convert.get("enabled", False):
            audio_format = self.audio_convert.get("format", "mp3")
            logger.info(f"启用YouTube音频转换功能，转换格式: {audio_format}")
            ydl_opts["postprocessors"].append(
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format,
                    "preferredquality": "192",
                }
            )

        # 添加代理配置
        proxy_config = self.config.get("proxy", {})
        if proxy_config.get("enabled"):
            ydl_opts["proxy"] = (
                f"socks5://{proxy_config['host']}:{proxy_config['port']}"
            )

        # 添加cookies配置
        if temp_cookie_file:
            ydl_opts["cookiefile"] = temp_cookie_file

        return ydl_opts

    async def download_video(self, url, status_callback=None):
        """下载YouTube视频（支持单个视频和播放列表）"""
        temp_cookie_file = None
        url = url.replace("m.youtube.com", "www.youtube.com")
        try:
            if self.cookies:
                temp_cookie_file = self._create_temp_cookie_file()

            ydl_opts = self._get_ydl_opts(temp_cookie_file)

            # 判断是否是播放列表
            is_playlist = "list" in url or url.endswith("/videos")

            if is_playlist:
                return await self._handle_playlist(url, ydl_opts, status_callback)
            else:
                return await self._handle_single_video(url, ydl_opts, status_callback)

        except Exception as e:
            logger.error(f"YouTube下载失败: {str(e)}")
            raise
        finally:
            if temp_cookie_file and os.path.exists(temp_cookie_file):
                os.unlink(temp_cookie_file)

    async def _handle_playlist(self, url, ydl_opts, status_callback):
        """处理播放列表下载"""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if status_callback:
                await status_callback("正在获取播放列表信息...")

            info = ydl.extract_info(url, download=False)
            if not info:
                return False, "无法获取播放列表信息"

            total_videos = len(info["entries"])
            success_count = 0
            failed_videos = []
            playlist_title = info.get("title", "未知播放列表")

            if status_callback:
                await status_callback(
                    f"检测到播放列表：{playlist_title}\n"
                    f"共{total_videos}个视频，开始下载..."
                )

            for index, entry in enumerate(info["entries"], 1):
                if not entry:
                    failed_videos.append(f"视频 #{index} 无法访问（可能是私密视频）")
                    if status_callback:
                        await status_callback(
                            f"⚠️ 播放列表 {playlist_title} 中的视频无法访问\n"
                            f"序号: {index}/{total_videos}\n"
                            f"原因: 可能是私密视频"
                        )
                    continue

                try:
                    video_url = entry.get("webpage_url") or entry.get("url")
                    video_title = entry.get("title", "未知标题")

                    if not video_url:
                        failed_videos.append(
                            f"视频 #{index} ({video_title}) URL获取失败"
                        )
                        continue

                    success, result = await self._download_single_video(
                        video_url,
                        ydl_opts,
                        video_title,
                        index,
                        total_videos,
                        status_callback,
                    )

                    if success:
                        success_count += 1
                    else:
                        failed_videos.append(
                            f"视频 #{index} ({video_title}) - {result}"
                        )

                except Exception as e:
                    failed_videos.append(
                        f"视频 #{index} ({video_title}) 下载失败: {str(e)}"
                    )

            # 生成总结信息
            summary = (
                f"📋 播放列表 {playlist_title} 下载完成！\n"
                f"总计：{total_videos}个视频\n"
                f"✅ 成功：{success_count}\n"
                f"❌ 失败：{len(failed_videos)}"
            )
            if failed_videos:
                summary += "\n\n失败视频列表："
                for fail in failed_videos[:10]:
                    summary += f"\n- {fail}"
                if len(failed_videos) > 10:
                    summary += f"\n...等共{len(failed_videos)}个视频失败"

            return True, summary

    async def _handle_single_video(self, url, ydl_opts, status_callback):
        """处理单个视频下载"""
        if status_callback:
            await status_callback("正在获取视频信息...")

        success, result = await self._download_single_video(
            url, ydl_opts, None, None, None, status_callback
        )
        return success, result

    async def _download_single_video(
        self, url, ydl_opts, title=None, index=None, total=None, status_callback=None
    ):
        """下载单个视频的具体实现"""
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if status_callback:
                    status_msg = "开始下载YouTube视频"
                    if title and index and total:
                        status_msg += f"：{title}\n序号: {index}/{total}"
                    await status_callback(status_msg)

                info = ydl.extract_info(url, download=True)
                if not info:
                    return False, "无法获取视频信息"

                return self._process_downloaded_video(info)

        except Exception as e:
            return False, str(e)

    def _create_temp_cookie_file(self):
        """创建临时cookies文件"""
        temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt")
        with temp_file as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# https://curl.haxx.se/rfc/cookie_spec.html\n")
            f.write("# This is a generated file!  Do not edit.\n\n")

            for cookie in self.cookies.split(";"):
                if cookie.strip():
                    name_value = cookie.strip().split("=", 1)
                    if len(name_value) == 2:
                        name, value = name_value
                        f.write(
                            f".youtube.com\tTRUE\t/\tTRUE\t2999999999\t{name.strip()}\t{value.strip()}\n"
                        )

        return temp_file.name

    def _process_downloaded_video(self, info):
        """处理下载完成的视频"""
        video_id = info["id"]
        video_title = info["title"]

        # 处理下载的所有文件(视频和音频)
        downloaded_files = []
        for file in os.listdir(YOUTUBE_TEMP_DIR):
            if video_id in file:
                source_path = os.path.join(YOUTUBE_TEMP_DIR, file)
                file_ext = os.path.splitext(file)[1][1:]  # 获取扩展名（去掉点）

                # 根据文件类型选择保存目录
                is_audio = file_ext.lower() in ["mp3", "m4a", "ogg", "wav", "flac"]
                target_dir = YOUTUBE_AUDIO_DIR if is_audio else YOUTUBE_DEST_DIR

                target_path = os.path.join(
                    target_dir, f"{sanitize_filename(video_title)}.{file_ext}"
                )

                success, result = move_file(source_path, target_path)
                if success:
                    downloaded_files.append(target_path)
                else:
                    logger.error(f"移动文件失败: {result}")

        if downloaded_files:
            # 如果启用了音频转换，并且有对应格式的音频文件，返回音频文件
            if self.audio_convert.get("enabled", False):
                audio_format = self.audio_convert.get("format", "mp3")
                for file_path in downloaded_files:
                    if file_path.endswith(f".{audio_format}"):
                        return True, file_path

            # 否则返回第一个文件（通常是视频文件）
            return True, downloaded_files[0]

        return False, "未找到下载的文件"

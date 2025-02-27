import os
import re
import asyncio
import logging
from datetime import datetime
from bilibili_api import video, Credential
from bilibili_api.exceptions import NetworkException, ResponseCodeException
from ..constants import BILIBILI_TEMP_DIR, BILIBILI_DEST_DIR

logger = logging.getLogger(__name__)


class BilibiliHandler:
    def __init__(self, config):
        """初始化B站处理器"""
        self.config = config
        self.credential = None
        self.cookie = config.get("cookie")

        # 如果配置了完整的cookie字符串，尝试从中提取凭证
        if self.cookie:
            self.set_credentials_from_cookie(self.cookie)

        # 确保目录存在
        os.makedirs(BILIBILI_TEMP_DIR, exist_ok=True)
        os.makedirs(BILIBILI_DEST_DIR, exist_ok=True)

    def extract_bvid(self, url):
        """从URL中提取BV号"""
        # 匹配BV号
        bv_pattern = r"BV\w{10}"
        match = re.search(bv_pattern, url)
        if match:
            return match.group(0)

        # 匹配短链接
        if "b23.tv" in url:
            try:
                import httpx

                response = httpx.head(url, follow_redirects=True)
                return self.extract_bvid(str(response.url))
            except Exception as e:
                logger.error(f"解析短链接失败: {str(e)}")

        return None

    async def download_video(self, url):
        """下载B站视频"""
        try:
            # 提取BV号
            bvid = self.extract_bvid(url)
            if not bvid:
                raise ValueError("无法从URL中提取BV号")

            # 创建视频对象
            v = video.Video(bvid=bvid, credential=self.credential)

            # 获取视频信息
            info = await v.get_info()
            title = info["title"]
            owner = info["owner"]["name"]

            # 生成安全的文件名
            safe_title = re.sub(r'[\\/:*?"<>|]', "_", title)
            filename = f"{safe_title}"

            # 下载视频
            logger.info(f"开始下载视频: {title}")
            temp_video_path = os.path.join(BILIBILI_TEMP_DIR, f"{filename}_video.mp4")
            temp_audio_path = os.path.join(BILIBILI_TEMP_DIR, f"{filename}_audio.mp4")
            final_path = os.path.join(BILIBILI_DEST_DIR, f"{filename}.mp4")

            # 获取视频流
            video_url = await v.get_download_url(0)

            # 下载视频和音频
            await self._download_stream(
                video_url["dash"]["video"][0]["baseUrl"], temp_video_path
            )
            await self._download_stream(
                video_url["dash"]["audio"][0]["baseUrl"], temp_audio_path
            )
            if os.path.exists(final_path):
                os.remove(final_path)
            # 合并视频和音频
            await self._merge_video_audio(temp_video_path, temp_audio_path, final_path)

            # 清理临时文件
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

            return {
                "type": "video",
                "path": final_path,
                "filename": os.path.basename(final_path),
                "title": title,
                "author": owner,
            }

        except (NetworkException, ResponseCodeException) as e:
            logger.error(f"B站API错误: {str(e)}")
            raise Exception(f"B站API错误: {str(e)}")
        except Exception as e:
            logger.error(f"下载B站视频失败: {str(e)}")
            raise Exception(f"下载B站视频失败: {str(e)}")

    async def _download_stream(self, url, path):
        """下载流媒体"""
        import httpx

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.bilibili.com",
        }

        if self.credential:
            headers["Cookie"] = (
                f"SESSDATA={self.credential.sessdata}; bili_jct={self.credential.bili_jct}; buvid3={self.credential.buvid3}"
            )

        async with httpx.AsyncClient() as client:
            async with client.stream("GET", url, headers=headers) as response:
                response.raise_for_status()

                with open(path, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        f.write(chunk)

    async def _merge_video_audio(self, video_path, audio_path, output_path):
        """合并视频和音频"""
        try:
            import subprocess

            cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-i",
                audio_path,
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-strict",
                "experimental",
                output_path,
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"合并视频失败: {stderr.decode()}")
                raise Exception("合并视频失败")

        except Exception as e:
            logger.error(f"合并视频和音频失败: {str(e)}")
            raise Exception(f"合并视频和音频失败: {str(e)}")

    def parse_cookie(self, cookie_str):
        """解析B站Cookie字符串，提取关键凭证信息"""
        cookie_dict = {}

        # 将cookie字符串拆分为键值对
        if cookie_str:
            pairs = cookie_str.split(";")
            for pair in pairs:
                pair = pair.strip()
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    cookie_dict[key] = value

        # 提取关键凭证
        sessdata = cookie_dict.get("SESSDATA")
        bili_jct = cookie_dict.get("bili_jct")
        buvid3 = cookie_dict.get("buvid3")

        # 提取用户ID
        dede_user_id = cookie_dict.get("DedeUserID")

        result = {
            "sessdata": sessdata,
            "bili_jct": bili_jct,
            "buvid3": buvid3,
            "user_id": dede_user_id,
        }

        # 检查是否成功提取了所有必要的凭证
        credentials_valid = all([sessdata, bili_jct, buvid3])

        return {
            "credentials_valid": credentials_valid,
            "credentials": result,
            "raw_cookies": cookie_dict,
        }

    def set_credentials_from_cookie(self, cookie_str):
        """从Cookie字符串中设置凭证"""
        parsed = self.parse_cookie(cookie_str)
        if parsed["credentials_valid"]:
            creds = parsed["credentials"]
            self.credential = Credential(
                sessdata=creds["sessdata"],
                bili_jct=creds["bili_jct"],
                buvid3=creds["buvid3"],
            )
            return True
        return False

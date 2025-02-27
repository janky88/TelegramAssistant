import os
import shutil
import logging
from f2.apps.douyin.handler import DouyinHandler
from src.constants import DOUYIN_DEST_DIR, DOUYIN_TEMP_DIR
from f2.apps.douyin.utils import AwemeIdFetcher

logger = logging.getLogger(__name__)


class CustomDouyinHandler:
    def __init__(self, cookie):
        self.cookie = cookie
        self.download_path = DOUYIN_TEMP_DIR
        os.makedirs(self.download_path, exist_ok=True)

    def get_download_config(self, url):
        """生成下载配置"""
        return {
            "headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
                "Referer": "https://www.douyin.com/",
            },
            "cookie": self.cookie,
            "proxies": {"http://": None, "https://": None},
            "url": url,
            "path": self.download_path,
            "naming": "{desc}_{create}_{nickname}",
            "mode": "one",
        }

    async def download_video(self, url):
        """下载抖音视频"""
        try:
            config = self.get_download_config(url)
            video = await DouyinHandler(config).handle_one_video()
            aweme_id = await AwemeIdFetcher.get_aweme_id(url)
            video = await DouyinHandler(config).fetch_one_video(aweme_id)
            return self.move_video(video._to_dict())
        except Exception as e:
            raise Exception(f"下载抖音视频失败: {str(e)}")

    def move_video(self, video):
        """移动视频"""
        try:
            desc = video.get("desc", "")
            create = video.get("create_time", "")
            nickname = video.get("nickname", "")
            filename = f"{desc}_{create}_{nickname}.mp4"
            for root, dirs, files in os.walk(self.download_path):
                for file in files:
                    if desc and file[:5] == desc[:5] and nickname and nickname in file:
                        shutil.move(
                            os.path.join(root, file),
                            os.path.join(DOUYIN_DEST_DIR, filename),
                        )
                        try:
                            shutil.rmtree(root)
                        except Exception as e:
                            pass
                        video["dest_path"] = os.path.join(DOUYIN_DEST_DIR, filename)
                        return video
            return None
        except Exception as e:
            logger.error(f"移动视频失败: {str(e)}")
            return None

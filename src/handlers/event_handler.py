import re
import logging
from telethon import events
from .telegram_handler import TelegramHandler
from .youtube_handler import YouTubeHandler
from .douyin_handler import CustomDouyinHandler
from .bilibili_handler import BilibiliHandler

logger = logging.getLogger(__name__)


class EventHandler:
    def __init__(self, config):
        self.config = config
        self.telegram_handler = TelegramHandler(config)
        self.youtube_handler = YouTubeHandler(config)
        self.douyin_handler = CustomDouyinHandler(
            config.get("douyin", {}).get("cookie")
        )
        self.bilibili_handler = BilibiliHandler(config.get("bilibili", {}))

    def register_handlers(self, client):
        """注册所有事件处理器"""

        @client.on(events.NewMessage(pattern="/start"))
        async def start(event):
            """处理 /start 命令"""
            await event.reply("你好！请转发视频给我，我会自动下载到指定文件夹。")

        @client.on(events.NewMessage)
        async def handle_message(event):
            """处理新消息"""
            try:

                message_text = event.message.text if event.message.text else ""

                # 检查是否是YouTube链接
                youtube_pattern = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.*"
                douyin_pattern = r"https://v\.douyin\.com/.*?/"
                bilibili_pattern = r"https://www\.bilibili\.com/video/.*?"
                is_youtube = bool(re.match(youtube_pattern, message_text))
                is_douyin = bool(re.search(douyin_pattern, message_text))
                is_bilibili = (
                    "bilibili.com" in event.message.text
                    or "b23.tv" in event.message.text
                )
                if is_youtube:
                    await self._handle_youtube_message(event)
                elif is_douyin:
                    await self._handle_douyin_message(event)
                elif is_bilibili:
                    await self.handle_bilibili_message(event)
                elif event.message.media:
                    await self._handle_telegram_media(event)

            except Exception as e:
                logger.error(f"处理消息时出错: {str(e)}")
                await event.reply(f"处理消息时出错: {str(e)}")

    async def _handle_douyin_message(self, event):
        try:
            match = re.findall(r"https?://v\.douyin\.com/.*?/", event.message.text)
            if match:
                await event.reply(f"开始下载抖音视频: {match[0]}")
                url = match[0]
                video = await self.douyin_handler.download_video(url)
                if video:
                    await event.reply(
                        f"✅ 抖音视频下载完成！\n"
                        f"标题: {video.get('desc')}\n"
                        f"保存位置: {video.get('dest_path')}"
                    )
                else:
                    await event.reply("无法下载该抖音视频，请检查链接是否有效。")
            else:
                await event.reply("无法下载该抖音视频，请检查链接是否有效。")
        except Exception as e:
            await event.reply(f"下载抖音视频时出错: {str(e)}")

    async def _handle_youtube_message(self, event):
        """处理YouTube链接消息"""
        status_message = await event.reply("开始解析YouTube下载链接...")
        try:
            success, result = await self.youtube_handler.download_video(
                event.message.text,
                lambda msg: status_message.edit(msg) if status_message else None,
            )

            if success:
                await event.reply(f"✅ YouTube视频下载完成！\n" f"保存位置: {result}")
            else:
                await event.reply(f"❌ YouTube视频下载失败！\n" f"错误: {result}")
        except Exception as e:
            error_msg = str(e)
            if "Sign in to confirm you're not a bot" in error_msg:
                await event.reply(
                    "YouTube下载失败: 需要验证。\n"
                    "请检查配置文件中的 youtube_download.cookies 是否正确设置。"
                )
            else:
                await event.reply(f"YouTube下载失败: {error_msg}")

    async def _handle_telegram_media(self, event):
        """处理Telegram媒体消息"""
        status_message = await event.reply("开始下载媒体文件...")
        try:
            success, result = await self.telegram_handler.process_media(event)

            if success:
                await event.reply(
                    f"✅ {result['type']} 文件下载完成！\n"
                    f"文件名: {result['filename']}\n"
                    f"保存位置: {result['path']}"
                )
            else:
                await event.reply(f"❌ 下载失败: {result}")
        except Exception as e:
            await event.reply(f"处理媒体文件时出错: {str(e)}")

    async def handle_bilibili_message(self, message):
        """处理消息"""
        try:
            await message.reply("正在下载B站视频，请稍候...")
            url = re.findall(
                r"https://www\.bilibili\.com/video/.*|https://b23\.tv/.*", message.text
            )
            if url:
                video = await self.bilibili_handler.download_video(url[0])
                if video:
                    await message.reply(
                        f"✅ B站视频下载完成！\n"
                        f"标题: {video.get('title')}\n"
                        f"保存位置: {video.get('path')}"
                    )
                    return True
            else:
                await message.reply("下载B站视频失败,请检查链接是否有效")
                return False

        except Exception as e:
            await message.reply(f"处理B站视频失败: {str(e)}")
            return False

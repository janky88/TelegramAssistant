import re
import logging
from telethon import events
from .telegram_handler import TelegramHandler
from .youtube_handler import YouTubeHandler

logger = logging.getLogger(__name__)


class EventHandler:
    def __init__(self, config):
        self.config = config
        self.telegram_handler = TelegramHandler()
        self.youtube_handler = YouTubeHandler(config)

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
                is_youtube = bool(re.match(youtube_pattern, message_text))

                if is_youtube:
                    await self._handle_youtube_message(event)
                elif event.message.media:
                    await self._handle_telegram_media(event)

            except Exception as e:
                logger.error(f"处理消息时出错: {str(e)}")
                await event.reply(f"处理消息时出错: {str(e)}")

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

import os

# 获取程序所在目录的绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")

# 临时目录
TEMP_DIR = os.path.join(BASE_DIR, "temp")
TELEGRAM_TEMP_DIR = os.path.join(TEMP_DIR, "telegram")
YOUTUBE_TEMP_DIR = os.path.join(TEMP_DIR, "youtube")

# Telegram媒体文件目录
TELEGRAM_DEST_DIR = os.path.join(BASE_DIR, "downloads/telegram")
TELEGRAM_VIDEOS_DIR = os.path.join(TELEGRAM_DEST_DIR, "videos")
TELEGRAM_AUDIOS_DIR = os.path.join(TELEGRAM_DEST_DIR, "audios")
TELEGRAM_PHOTOS_DIR = os.path.join(TELEGRAM_DEST_DIR, "photos")
TELEGRAM_OTHERS_DIR = os.path.join(TELEGRAM_DEST_DIR, "others")

# YouTube目录
YOUTUBE_DEST_DIR = os.path.join(BASE_DIR, "downloads/youtube")

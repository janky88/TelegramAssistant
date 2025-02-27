import os
import yaml
import logging
from ..constants import CONFIG_DIR

logger = logging.getLogger(__name__)


def load_config():
    """加载配置文件"""
    config_file = os.path.join(CONFIG_DIR, "config.yaml")
    default_config = {
        "api_id": "",
        "api_hash": "",
        "user_account": {
            "enabled": False,
            "phone": "",
            "session_name": "user_session",
        },
        "bot_account": {
            "token": "",
            "session_name": "bot_session",
        },
        "youtube_download": {
            "format": "best",
            "cookies": "",
        },
        "scheduled_messages": [],
        "log_level": "INFO",
        "proxy": {
            "enabled": False,
            "host": "127.0.0.1",
            "port": 7890,
        },
        "douyin": {
            "cookie": "",
        },
    }

    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)

        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as file:
                config = yaml.safe_load(file) or {}
                # 合并默认配置和用户配置
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict) and isinstance(config[key], dict):
                        for sub_key, sub_value in value.items():
                            if sub_key not in config[key]:
                                config[key][sub_key] = sub_value
        else:
            config = default_config
            with open(config_file, "w", encoding="utf-8") as file:
                yaml.dump(config, file, allow_unicode=True, default_flow_style=False)
            raise ValueError("请先配置 config/config.yaml 文件")

        # 验证必要的配置项
        if not config.get("api_id") or not config.get("api_hash"):
            raise ValueError("请在 config.yaml 中配置 api_id 和 api_hash")

        if not config.get("bot_account", {}).get("token"):
            raise ValueError("请在 config.yaml 中配置 bot_account.token")

        return config

    except Exception as e:
        logger.error(f"加载配置文件时出错: {str(e)}")
        raise

# TelegramAssistant - Telegram 助手

这是一个基于 Telethon 的 Telegram 机器人，可以自动下载 Telegram 消息中的视频内容和 YouTube 链接。

## 功能特性

- 支持下载 Telegram 中的视频、音频和图片文件
- 支持下载 YouTube 视频和播放列表
- 支持下载 Bilibili 视频
- 支持下载 抖音 视频
- 支持代理配置
- 支持 Docker 部署
- 支持定时发送消息
- 支持消息转发功能（可按关键词过滤）
- 支持权限控制（可限制特定用户使用下载功能）
- 文件自动分类存储
- 支持 YouTube cookies 配置（用于下载会员内容）

## 系统要求

- Python 3.12+
- Docker（可选，用于容器化部署）

## 安装方法

### 方法 1：直接运行

1. 克隆仓库：

```bash
git clone [repository-url]
cd TelegramAssistant
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 配置文件：

- 编辑 `config.yaml` 填入必要的配置信息：
  - api_id（从 https://my.telegram.org 获取）
  - api_hash
  - bot_account.token（从 @BotFather 获取）

### 方法 2：Docker 部署

1. 使用 docker-compose：

```bash
version: '3'
services:
  telegram_assistant:
    image: shenxianmq/telegram_assistant:latest
    volumes:
      - ./config:/app/config
      - ./downloads/telegram:/app/downloads/telegram
      - ./downloads/youtube:/app/downloads/youtube
      - ./downloads/douyin:/app/downloads/douyin
      - ./downloads/bilibili:/app/downloads/bilibili
      - ./downloads/temp:/app/temp

    restart: unless-stopped
    container_name: telegram_assistant
    environment:
      - TZ=Asia/Shanghai
```

```bash
# 拉取并启动容器

docker-compose up -d
```

```bash
# 进入容器进行初始化配置

docker exec -it telegram_assistant python /app/init.py
```

```bash
# 按提示输入验证码后，重启容器使配置生效

docker restart telegram_assistant
```

或者使用 docker run：

```bash
# 拉取镜像
docker pull shenxianmq/telegram_assistant:latest

# 创建必要的目录
mkdir -p config downloads/telegram downloads/youtube

# 运行容器
docker run -d \
  --name telegram_assistant \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/downloads/telegram:/app/downloads/telegram \
  -v $(pwd)/downloads/youtube:/app/downloads/youtube \
  -v $(pwd)/downloads/bilibili:/app/downloads/bilibili \
  -v $(pwd)/downloads/douyin:/app/downloads/douyin \
  --restart unless-stopped \
  shenxianmq/telegram_assistant:latest

# 进入容器进行初始化配置
docker exec -it telegram_assistant python /app/init.py

# 按提示输入验证码后，重启容器使配置生效
docker restart telegram_assistant
```

注意：在运行 `init.py` 时，需要：

1. 确保已经在 `config/config.yaml` 中填写了正确的 API ID、API Hash 和 Bot Token
2. 按照终端提示输入手机号和验证码
3. 初始化完成后重启容器以应用新的配置

## 配置说明

配置文件位于 `config/config.yaml`，完整的配置项说明：

```yaml
# Telegram API配置（必填）
api_id: "" # 从 https://my.telegram.org 获取的API ID
api_hash: "" # 从 https://my.telegram.org 获取的API Hash

# 用户账号配置（可选，用于需要登录用户账号的情况）
user_account:
  enabled: false # 是否启用用户账号
  phone: "" # 用户手机号（启用时必填）
  session_name: "user_session" # 用户会话名称

# 机器人账号配置（必填）
bot_account:
  token: "" # 从 @BotFather 获取的机器人token
  session_name: "bot_session" # 机器人会话名称

# YouTube下载配置
youtube_download:
  format: "bv*+ba/best" # 视频质量，具体参考yt-dlp的格式选择
  cookies: "" # YouTube cookies（可选，用于下载会员内容）
  download_list: false # 是否下载播放列表，设为true才会下载整个列表，否则只下载当前视频

# 定时消息配置，支持多个（可选）
scheduled_messages:
  - chat_id: "" # 目标群组/频道的用户名
    message: "" # 要发送的消息内容
    time: "08:00" # 每天发送消息的时间，24小时制

  - chat_id: "" # 目标群组/频道的用户名
    message: "" # 要发送的消息内容
    time: "08:00" # 每天发送消息的时间，24小时制

# 消息转发配置，支持多个（可选）
transfer_message:
  - source_chat: "" # 源频道/群组ID或用户名（必须是用户账号能访问的）
    target_chat: "" # 目标接收者（可以是用户名、ID或群组/频道ID）
    include_keywords: [] # 关键词列表，留空表示转发所有消息

  - source_chat: "" # 源频道/群组ID或用户名
    target_chat: "" # 目标接收者
    include_keywords: # 只转发包含指定关键词的消息
      - "关键词1"
      - "关键词2"

# 注意：消息转发功能需要启用用户账号（user_account.enabled=true）

# 抖音下载配置
douyin:
  cookie: "" # 抖音 cookies（可选，用于下载抖音视频）

# Bilibili下载配置
bilibili:
  cookie: "" # Bilibili cookies（可选，用于下载Bilibili视频）

# 权限控制配置（可选）
allowed_chat_ids: [] # 允许使用视频下载功能的chat_id列表，留空表示允许所有用户
# 示例：
# allowed_chat_ids:
#   - 123456789        # 个人chat_id

# 日志级别配置
log_level: "INFO" # 可选：DEBUG, INFO, WARNING, ERROR

# 代理配置（可选）
# 注意：仅支持socks5代理，不支持http代理
proxy:
  enabled: false # 是否启用代理
  host: "127.0.0.1" # 代理服务器地址
  port: 7890 # 代理服务器端口
```

### 配置说明：

1. **API 配置**：

   - `api_id` 和 `api_hash`：必填，从 Telegram 开发者页面获取
   - 获取地址：https://my.telegram.org

2. **账号配置**：

   - 支持同时配置用户账号和机器人账号
   - 机器人账号必须配置，用户账号可选
   - 机器人 token 从 @BotFather 获取

3. **YouTube 下载配置**：

   - `format`：视频质量选择
   - `cookies`：用于下载会员内容，需要提供 cookies 字符串
   - `download_list`：是否下载播放列表，设为 true 才会下载整个列表，否则只下载当前视频

4. **定时消息**：

   - 可配置多个定时消息任务
   - 支持指定发送时间和目标聊天

5. **代理设置**：

   - 仅支持 socks5 代理
   - 建议在网络受限地区使用

6. **抖音下载配置**：

   - `cookie`：用于下载抖音视频，需要提供 cookies 字符串

7. **Bilibili 下载配置**：

   - `cookie`：用于下载 Bilibili 视频，需要提供 cookies 字符串

8. **权限控制配置**：
   - `allowed_chat_ids`：限制只有指定的 chat_id 才能使用视频下载功能
   - 留空（`[]`）表示允许所有用户使用
   - 支持个人 chat_id、群组 chat_id 和用户名
   - 如何获取 chat_id：未授权用户尝试使用时会在日志中记录其 chat_id

## 使用方法

1. 启动机器人：

```bash
python main.py
```

2. 在 Telegram 中：

- 发送 `/start` 开始使用
- 转发视频或发送 YouTube 链接给机器人
- 机器人会自动下载并保存到指定目录

## 权限控制

如果你希望限制只有特定用户才能使用视频下载功能，可以配置 `allowed_chat_ids`：

为空则所有人都可以使用

### 配置示例：

```yaml
# 允许所有用户（默认）
allowed_chat_ids: []

# 只允许特定用户
allowed_chat_ids:
  - 123456789        # 你的个人chat_id
```

### 获取 chat_id 的方法：

1. 保持 `allowed_chat_ids` 为空列表
2. 启动机器人后，让需要授权的用户尝试发送视频链接
3. 查看日志，会显示类似：`WARNING - 未授权的chat_id尝试下载YouTube视频: 123456789`
4. 将显示的 chat_id 添加到配置文件中
5. 重启机器人使配置生效

### 权限功能说明：

- ✅ 支持的功能：YouTube、抖音、B 站、Telegram 媒体文件下载
- ✅ 未授权用户会收到友好提示："❌ 抱歉，您没有权限使用此功能。"
- ✅ 所有未授权访问尝试都会记录在日志中
- ✅ 支持个人 ID、群组 ID 和用户名格式

## 文件存储结构

```
downloads/
├── telegram/
│   ├── videos/
│   ├── audios/
│   ├── photos/
│   └── others/
├── youtube/
├── douyin/
└── bilibili/
```

## 注意事项

- 请确保配置文件中的 API 密钥和 Token 正确填写
- YouTube 下载功能需要稳定的网络连接
- 建议使用代理以提高下载速度和稳定性
- 抖音和 Bilibili 下载功能需要提供 cookies
- 文件会按类型自动分类存储
- 如需限制使用权限，请在配置文件中设置 `allowed_chat_ids`，未授权用户的 chat_id 会记录在日志中

## 许可证

MIT License

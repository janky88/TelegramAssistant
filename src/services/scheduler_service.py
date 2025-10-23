import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def send_scheduled_message(self, client, chat_id, message):
        """发送定时消息"""
        try:
            await client.send_message(chat_id, message)
            logger.info(f"成功发送定时消息到 {chat_id}")
        except Exception as e:
            logger.error(f"发送定时消息到 {chat_id} 失败: {str(e)}")

    def initialize_tasks(self, client, scheduled_messages):
        """初始化定时任务"""
        if not scheduled_messages:
            logger.info("没有配置定时消息任务")
            return

        for idx, task in enumerate(scheduled_messages):
            try:
                chat_id = task.get("chat_id")
                message = task.get("message")
                schedule_time = task.get("time", "08:00")

                if not chat_id or not message:
                    logger.warning(f"定时任务 #{idx+1} 缺少必要的参数")
                    continue

                try:
                    hour, minute = map(int, schedule_time.split(":"))
                except ValueError:
                    logger.error(f"定时任务 #{idx+1} 的时间格式错误: {schedule_time}")
                    continue

                self.scheduler.add_job(
                    self.send_scheduled_message,
                    CronTrigger(hour=hour, minute=minute),
                    args=[client, chat_id, message],
                    id=f"message_{idx}",
                    replace_existing=True,
                )

                logger.info(
                    f"已添加定时任务 #{idx+1}: 发送到 {chat_id}, 每天 {schedule_time}"
                )

            except Exception as e:
                logger.error(f"添加定时任务 #{idx+1} 失败: {str(e)}")

    def start(self):
        """启动调度器"""
        self.scheduler.start()

    def shutdown(self):
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()

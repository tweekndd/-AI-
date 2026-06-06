"""
失败重试管理服务（V2.0 新增）
提供统一的异步重试机制，支持网站抓取和AI分析的重试
记录重试日志
"""
import asyncio
import logging
from typing import Callable, Awaitable, TypeVar, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("retry_manager")

T = TypeVar("T")


async def retry_async(
    func: Callable[..., Awaitable[T]],
    *args,
    max_retries: int = 3,
    retry_delay: float = 2.0,
    backoff_multiplier: float = 2.0,
    task_name: str = "任务",
    **kwargs,
) -> Optional[T]:
    """
    异步重试装饰器
    自动重试指定次数，每次重试间隔递增
    返回函数结果，如果全部失败返回None
    """
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            result = await func(*args, **kwargs)
            if attempt > 1:
                logger.info(f"{task_name} 第{attempt}次重试成功")
            return result
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait_time = retry_delay * (backoff_multiplier ** (attempt - 1))
                logger.warning(
                    f"{task_name} 第{attempt}次失败: {str(e)[:100]}"
                    f"，{wait_time:.1f}秒后重试..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    f"{task_name} 重试{max_retries}次全部失败: {str(e)[:200]}"
                )

    return None

import logging
import functools
from django.utils import timezone

logger = logging.getLogger('tasks')


def log_view(func):
    """Декоратор для логирования выполнения представлений"""
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        start_time = timezone.now()
        try:
            response = func(request, *args, **kwargs)
            duration = (timezone.now() - start_time).total_seconds()
            logger.info(f"✅ {func.__name__} выполнен за {duration:.3f} сек")
            return response
        except Exception as e:
            logger.exception(f"❌ {func.__name__} ошибка: {str(e)}")
            raise
    return wrapper
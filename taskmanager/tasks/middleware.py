import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve

logger = logging.getLogger('tasks')

class RequestLogMiddleware(MiddlewareMixin):
    """Middleware для логирования всех HTTP запросов"""
    
    def process_request(self, request):
        request.start_time = time.time()
        
        # Логируем информацию о запросе
        logger.debug(f"📨 {request.method} {request.path} - Пользователь: {request.user if request.user.is_authenticated else 'Аноним'}")
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Логируем ответ
            logger.info(
                f"📤 {request.method} {request.path} - {response.status_code} - "
                f"Время: {duration:.3f} сек"
            )
            
            # Логируем ошибки 4xx и 5xx
            if response.status_code >= 400:
                logger.error(
                    f"❌ Ошибка {response.status_code}: {request.method} {request.path} - "
                    f"Пользователь: {request.user if request.user.is_authenticated else 'Аноним'}"
                )
        
        return response
    
    def process_exception(self, request, exception):
        """Логирование необработанных исключений"""
        logger.exception(
            f"💥 Исключение в {request.method} {request.path}: {str(exception)}",
            exc_info=True
        )
        return None
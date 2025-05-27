import sys
import os
import asyncio
import random
import time
import json
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional

# Определяем пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEST_DIR = os.path.dirname(os.path.abspath(__file__))

# Добавляем корневую директорию проекта в путь для импорта
sys.path.append(BASE_DIR)

# Импортируем утилиты для тестирования
from telegram_bot.test.load_tests.utils import TestResults, generate_user_id, generate_mock_dialog_messages, measure_execution_time
# Импортируем функции для визуализации
from telegram_bot.test.load_tests.visualize_results import create_response_time_distribution, create_success_rate_chart, create_percentile_comparison, create_time_series, create_html_report

# Импортируем модули AI-сервиса
from telegram_bot.ai_service import initialize_dialogue, get_llm_response

# Настройка логирования
logger = logging.getLogger("response_time_test")

class ResponseTimeTest:
    """
    Тест для проверки времени отклика при большом количестве запросов
    """
    
    def __init__(
        self,
        total_requests: int = 100,
        batch_size: int = 10,
        ramp_up_seconds: int = 30,
        request_timeout: int = 60,
        auto_visualize: bool = True
    ):
        """
        Инициализация теста
        
        Args:
            total_requests: Общее количество запросов для теста
            batch_size: Размер пакета одновременных запросов
            ramp_up_seconds: Время для постепенного увеличения нагрузки (секунды)
            request_timeout: Таймаут для одного запроса (секунды)
            auto_visualize: Автоматически создавать визуализацию после теста
        """
        self.total_requests = total_requests
        self.batch_size = batch_size
        self.ramp_up_seconds = ramp_up_seconds
        self.request_timeout = request_timeout
        self.auto_visualize = auto_visualize
        
        # Инициализируем хранилище результатов
        self.results = TestResults("response_time")
        self.results.set_test_data("total_requests", total_requests)
        self.results.set_test_data("batch_size", batch_size)
        self.results.set_test_data("ramp_up_seconds", ramp_up_seconds)
        self.results.set_test_data("request_timeout", request_timeout)
        
        # Счетчики для контроля прогресса
        self.completed_requests = 0
        self.failed_requests = 0
    
    async def send_single_request(self, request_id: int) -> Dict[str, Any]:
        """
        Отправляет одиночный запрос к AI-сервису
        
        Args:
            request_id: Идентификатор запроса
            
        Returns:
            Словарь с результатами запроса
        """
        # Генерируем данные для запроса
        user_id = generate_user_id()
        issue_id = str(random.randint(1, 3))
        
        request_stats = {
            "request_id": request_id,
            "user_id": user_id,
            "issue_id": issue_id,
            "start_time": time.time(),
            "end_time": None,
            "response_time": None,
            "status": "pending",
            "error": None
        }
        
        try:
            # Загружаем системные промпты
            system_prompts_path = os.path.join(BASE_DIR, 'ai_service', 'system_prompts.json')
            with open(system_prompts_path, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            
            # Создаем базовый контекст для запроса
            messages = [
                {"role": "system", "content": prompts[issue_id]["system_prompt"]},
                {"role": "assistant", "content": prompts[issue_id]["initial_message"]}
            ]
            
            # Добавляем случайное сообщение пользователя
            user_messages = generate_mock_dialog_messages(issue_id, 1)
            messages.append(user_messages[0])
            
            # Измеряем время отклика
            response, response_time = await measure_execution_time(
                get_llm_response, messages, user_id, issue_id
            )
            
            # Обновляем статистику
            request_stats["response_time"] = response_time
            request_stats["end_time"] = time.time()
            request_stats["status"] = "success" if response else "failed"
            request_stats["error"] = None if response else "Empty response"
            
            # Обновляем общие результаты теста
            self.results.add_response_time(response_time)
            if not response:
                self.results.add_error(f"Empty response for request {request_id}")
                self.failed_requests += 1
            
            self.completed_requests += 1
            
            # Логируем прогресс
            if request_id % max(1, self.total_requests // 10) == 0 or request_id == self.total_requests:
                logger.info(f"Progress: {self.completed_requests}/{self.total_requests} requests completed "
                           f"({self.failed_requests} failed)")
        
        except asyncio.TimeoutError:
            request_stats["status"] = "timeout"
            request_stats["error"] = "Request timed out"
            request_stats["end_time"] = time.time()
            self.results.add_error(f"Timeout for request {request_id}")
            self.failed_requests += 1
            self.completed_requests += 1
        
        except Exception as e:
            request_stats["status"] = "error"
            request_stats["error"] = str(e)
            request_stats["end_time"] = time.time()
            self.results.add_error(f"Error in request {request_id}: {str(e)}")
            self.failed_requests += 1
            self.completed_requests += 1
        
        return request_stats
    
    async def run(self) -> Dict[str, Any]:
        """
        Запускает тест на время отклика
        
        Returns:
            Словарь с результатами теста
        """
        logger.info(f"Запуск теста времени отклика с {self.total_requests} запросами, "
                   f"batch_size={self.batch_size}, ramp_up={self.ramp_up_seconds}с")
        
        start_time = time.time()
        request_stats_list = []
        
        # Вычисляем задержку между пакетами запросов для плавного увеличения нагрузки
        delay_between_batches = self.ramp_up_seconds / (self.total_requests / self.batch_size)
        
        # Разбиваем запросы на пакеты
        for batch_start in range(0, self.total_requests, self.batch_size):
            batch_end = min(batch_start + self.batch_size, self.total_requests)
            batch_size = batch_end - batch_start
            
            # Создаем задачи для текущего пакета
            batch_tasks = []
            for i in range(batch_start, batch_end):
                task = asyncio.create_task(self.send_single_request(i + 1))
                batch_tasks.append(task)
            
            # Запускаем пакет запросов и ждем их завершения
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Обрабатываем результаты пакета
            for result in batch_results:
                if isinstance(result, Exception):
                    self.results.add_error(f"Exception in request: {str(result)}")
                    self.failed_requests += 1
                else:
                    request_stats_list.append(result)
            
            # Делаем паузу перед следующим пакетом (если не последний)
            if batch_end < self.total_requests:
                await asyncio.sleep(delay_between_batches)
        
        end_time = time.time()
        
        # Сохраняем детальную статистику по запросам
        self.results.set_test_data("request_stats", request_stats_list)
        self.results.set_test_data("actual_test_duration", end_time - start_time)
        
        # Вычисляем и сохраняем производительность (запросов в секунду)
        test_duration = max(0.001, end_time - start_time)  # Избегаем деления на 0
        rps = self.total_requests / test_duration
        self.results.set_test_data("requests_per_second", round(rps, 2))
        
        # Сохраняем результаты
        results = self.results.save_results()
        
        # Автоматически создаем визуализацию если включена опция
        if self.auto_visualize:
            self.visualize_results(results)
        
        logger.info(f"Тест завершен. Обработано {self.completed_requests} запросов "
                  f"({self.failed_requests} ошибок) за {test_duration:.2f} секунд")
        logger.info(f"Средняя производительность: {rps:.2f} запросов в секунду")
        
        return results
    
    def visualize_results(self, results):
        """
        Создает визуализацию результатов теста
        
        Args:
            results: Результаты теста
        """
        try:
            # Получаем путь к файлу с результатами
            results_file = os.path.join(self.results.result_dir, "results.json")
            
            # Создаем директорию для графиков
            charts_dir = os.path.join(self.results.result_dir, "charts")
            os.makedirs(charts_dir, exist_ok=True)
            
            # Создаем графики
            output_files = {}
            output_files["Распределение времени отклика"] = create_response_time_distribution(results, results_file, charts_dir)
            output_files["Успешные запросы"] = create_success_rate_chart(results, charts_dir)
            output_files["Перцентили времени отклика"] = create_percentile_comparison(results, charts_dir)
            output_files["Изменение времени отклика"] = create_time_series(results, results_file, charts_dir)
            
            # Создаем HTML-отчет
            html_path = create_html_report(results_file, output_files, self.results.result_dir)
            
            logger.info(f"Визуализация результатов создана: {html_path}")
            print(f"\nHTML-отчет с визуализацией: {html_path}")
        except Exception as e:
            logger.error(f"Ошибка при создании визуализации: {str(e)}")
            print(f"Не удалось создать визуализацию: {str(e)}")

async def main():
    """Точка входа для запуска теста"""
    # Параметры теста (можно настроить)
    params = {
        "total_requests": 100,
        "batch_size": 10,
        "ramp_up_seconds": 30,
        "request_timeout": 60,
        "auto_visualize": True  # Автоматическая визуализация по умолчанию включена
    }
    
    # Создаем и запускаем тест
    test = ResponseTimeTest(**params)
    results = await test.run()
    
    # Выводим краткую статистику
    print("\n=== Результаты теста времени отклика ===")
    print(f"Всего запросов: {results['total_requests']}")
    print(f"Успешных запросов: {results['successful_requests']}")
    print(f"Ошибок: {results['failed_requests']}")
    print(f"Время выполнения: {results['duration_seconds']:.2f} сек")
    print(f"Запросов в секунду: {results['test_data']['requests_per_second']:.2f}")
    print(f"Среднее время ответа: {results['response_time_stats']['avg_ms']:.2f} мс")
    print(f"Медианное время ответа: {results['response_time_stats']['p50_ms']:.2f} мс")
    print(f"90-й процентиль времени ответа: {results['response_time_stats']['p90_ms']:.2f} мс")
    print(f"95-й процентиль времени ответа: {results['response_time_stats']['p95_ms']:.2f} мс")
    print(f"Результаты сохранены в: {test.results.result_dir}")

if __name__ == "__main__":
    asyncio.run(main()) 
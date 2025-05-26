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
logger = logging.getLogger("concurrent_dialogs_test")

class ConcurrentDialogsTest:
    """
    Тест на одновременные диалоги с несколькими пользователями
    """
    
    def __init__(
        self,
        num_users: int = 10,
        messages_per_dialog: int = 5,
        concurrent_requests: int = 5,
        message_delay: float = 1.0,
        test_duration: int = 60,
        auto_visualize: bool = True
    ):
        """
        Инициализация теста
        
        Args:
            num_users: Количество одновременных пользователей
            messages_per_dialog: Сколько сообщений отправляет каждый пользователь
            concurrent_requests: Максимальное количество одновременных запросов
            message_delay: Задержка между сообщениями одного пользователя (секунды)
            test_duration: Максимальная длительность теста в секундах
            auto_visualize: Автоматически создавать визуализацию после теста
        """
        self.num_users = num_users
        self.messages_per_dialog = messages_per_dialog
        self.concurrent_requests = concurrent_requests
        self.message_delay = message_delay
        self.test_duration = test_duration
        self.auto_visualize = auto_visualize
        
        # Инициализируем хранилище результатов
        self.results = TestResults("concurrent_dialogs")
        self.results.set_test_data("num_users", num_users)
        self.results.set_test_data("messages_per_dialog", messages_per_dialog)
        self.results.set_test_data("concurrent_requests", concurrent_requests)
        self.results.set_test_data("message_delay", message_delay)
        self.results.set_test_data("max_test_duration", test_duration)
    
    async def simulate_user_dialog(self, user_id: str, issue_id: str) -> Dict[str, Any]:
        """
        Симулирует диалог одного пользователя с системой
        
        Args:
            user_id: ID пользователя
            issue_id: ID типа проблемы (1, 2 или 3)
            
        Returns:
            Словарь с результатами диалога
        """
        dialog_stats = {
            "user_id": user_id,
            "issue_id": issue_id,
            "start_time": time.time(),
            "end_time": None,
            "response_times": [],
            "errors": [],
            "messages_sent": 0,
            "messages_received": 0
        }
        
        try:
            # Инициализируем диалог
            dialogue_id, init_time = await measure_execution_time(
                initialize_dialogue, issue_id, user_id
            )
            
            dialog_stats["dialogue_id"] = dialogue_id
            dialog_stats["response_times"].append(init_time)
            self.results.add_response_time(init_time)
            
            # Загружаем системные промпты для получения начального сообщения
            system_prompts_path = os.path.join(BASE_DIR, 'ai_service', 'system_prompts.json')
            with open(system_prompts_path, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            
            # Формируем начальный контекст диалога
            messages = [
                {"role": "system", "content": prompts[issue_id]["system_prompt"]},
                {"role": "assistant", "content": prompts[issue_id]["initial_message"]}
            ]
            
            dialog_stats["messages_received"] += 1
            
            # Генерируем диалог с заданным количеством сообщений
            user_messages = generate_mock_dialog_messages(issue_id, self.messages_per_dialog)
            
            # Отправляем сообщения последовательно
            for user_message in user_messages:
                # Добавляем сообщение пользователя
                messages.append(user_message)
                dialog_stats["messages_sent"] += 1
                
                # Получаем ответ от AI
                ai_response, response_time = await measure_execution_time(
                    get_llm_response, messages, user_id, issue_id
                )
                
                dialog_stats["response_times"].append(response_time)
                self.results.add_response_time(response_time)
                
                if ai_response:
                    messages.append({"role": "assistant", "content": ai_response})
                    dialog_stats["messages_received"] += 1
                else:
                    error = f"Не получен ответ от AI для пользователя {user_id}"
                    dialog_stats["errors"].append(error)
                    self.results.add_error(error)
                
                # Добавляем задержку между сообщениями
                await asyncio.sleep(self.message_delay)
        
        except Exception as e:
            error = f"Ошибка в диалоге пользователя {user_id}: {str(e)}"
            dialog_stats["errors"].append(error)
            self.results.add_error(error)
        
        # Фиксируем время окончания диалога
        dialog_stats["end_time"] = time.time()
        dialog_stats["duration"] = dialog_stats["end_time"] - dialog_stats["start_time"]
        
        return dialog_stats
    
    async def run(self) -> Dict[str, Any]:
        """
        Запускает тест на одновременные диалоги
        
        Returns:
            Словарь с результатами теста
        """
        logger.info(f"Запуск теста с {self.num_users} пользователями, "
                   f"{self.messages_per_dialog} сообщений на пользователя")
        
        # Создаем задачи для всех пользователей
        tasks = []
        user_dialogs = {}
        
        for i in range(self.num_users):
            user_id = generate_user_id()
            # Равномерно распределяем типы проблем
            issue_id = str(i % 3 + 1)
            
            # Создаем задачу для диалога пользователя
            task = asyncio.create_task(self.simulate_user_dialog(user_id, issue_id))
            tasks.append(task)
            user_dialogs[user_id] = {"task": task, "issue_id": issue_id}
        
        # Устанавливаем таймаут для всего теста
        try:
            start_time = time.time()
            completed_dialogs = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Собираем статистику по каждому диалогу
            user_stats = []
            for dialog_stats in completed_dialogs:
                if isinstance(dialog_stats, Exception):
                    self.results.add_error(f"Исключение в диалоге: {str(dialog_stats)}")
                else:
                    user_stats.append(dialog_stats)
            
            # Добавляем общую статистику в результаты
            self.results.set_test_data("user_dialogs", user_stats)
            self.results.set_test_data("actual_test_duration", end_time - start_time)
            
            # Сохраняем результаты
            results = self.results.save_results()
            
            # Автоматически создаем визуализацию если включена опция
            if self.auto_visualize:
                self.visualize_results(results)
            
            logger.info(f"Тест завершен. Обработано {len(user_stats)} диалогов за {end_time - start_time:.2f} секунд")
            return results
            
        except asyncio.TimeoutError:
            self.results.add_error(f"Тест превысил максимальную длительность {self.test_duration} секунд")
            results = self.results.save_results()
            
            # Автоматически создаем визуализацию если включена опция
            if self.auto_visualize:
                self.visualize_results(results)
                
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
        "num_users": 10,
        "messages_per_dialog": 5,
        "concurrent_requests": 5,
        "message_delay": 1.0,
        "test_duration": 120,
        "auto_visualize": True  # Автоматическая визуализация по умолчанию включена
    }
    
    # Создаем и запускаем тест
    test = ConcurrentDialogsTest(**params)
    results = await test.run()
    
    # Выводим краткую статистику
    print("\n=== Результаты теста одновременных диалогов ===")
    print(f"Пользователей: {params['num_users']}")
    print(f"Сообщений на пользователя: {params['messages_per_dialog']}")
    print(f"Всего запросов: {results['total_requests']}")
    print(f"Успешных запросов: {results['successful_requests']}")
    print(f"Ошибок: {results['failed_requests']}")
    print(f"Время выполнения: {results['duration_seconds']:.2f} сек")
    print(f"Среднее время ответа: {results['response_time_stats']['avg_ms']:.2f} мс")
    print(f"Медианное время ответа: {results['response_time_stats']['p50_ms']:.2f} мс")
    print(f"90-й процентиль времени ответа: {results['response_time_stats']['p90_ms']:.2f} мс")
    print(f"Результаты сохранены в: {test.results.result_dir}")

if __name__ == "__main__":
    asyncio.run(main()) 
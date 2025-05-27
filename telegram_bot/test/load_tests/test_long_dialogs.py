import sys
import os
import asyncio
import random
import time
import json
import matplotlib.pyplot as plt
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
logger = logging.getLogger("long_dialogs_test")

class LongDialogsTest:
    """
    Тест на длительные диалоги (100+ сообщений)
    """
    
    def __init__(
        self,
        num_dialogs: int = 3,
        messages_per_dialog: int = 100,
        message_delay: float = 0.5,
        save_full_dialogs: bool = True,
        auto_visualize: bool = True
    ):
        """
        Инициализация теста
        
        Args:
            num_dialogs: Количество одновременных длинных диалогов
            messages_per_dialog: Количество сообщений в каждом диалоге
            message_delay: Задержка между сообщениями в диалоге (секунды)
            save_full_dialogs: Сохранять ли полные тексты диалогов
            auto_visualize: Автоматически создавать визуализацию после теста
        """
        self.num_dialogs = num_dialogs
        self.messages_per_dialog = messages_per_dialog
        self.message_delay = message_delay
        self.save_full_dialogs = save_full_dialogs
        self.auto_visualize = auto_visualize
        
        # Инициализируем хранилище результатов
        self.results = TestResults("long_dialogs")
        self.results.set_test_data("num_dialogs", num_dialogs)
        self.results.set_test_data("messages_per_dialog", messages_per_dialog)
        self.results.set_test_data("message_delay", message_delay)
    
    async def run_long_dialog(self, dialog_id: int) -> Dict[str, Any]:
        """
        Запускает один длинный диалог
        
        Args:
            dialog_id: Идентификатор диалога
            
        Returns:
            Словарь с результатами диалога
        """
        user_id = generate_user_id()
        issue_id = str(random.randint(1, 3))
        
        dialog_stats = {
            "dialog_id": dialog_id,
            "user_id": user_id,
            "issue_id": issue_id,
            "start_time": time.time(),
            "end_time": None,
            "response_times": [],
            "token_counts": [],
            "errors": [],
            "messages_sent": 0,
            "messages_received": 0,
            "full_dialog": [] if self.save_full_dialogs else None
        }
        
        try:
            # Инициализируем диалог
            dialogue_id, init_time = await measure_execution_time(
                initialize_dialogue, issue_id, user_id
            )
            
            dialog_stats["dialogue_db_id"] = dialogue_id
            dialog_stats["response_times"].append(init_time)
            self.results.add_response_time(init_time)
            
            # Загружаем системные промпты
            system_prompts_path = os.path.join(BASE_DIR, 'ai_service', 'system_prompts.json')
            with open(system_prompts_path, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            
            # Формируем начальный контекст диалога
            messages = [
                {"role": "system", "content": prompts[issue_id]["system_prompt"]},
                {"role": "assistant", "content": prompts[issue_id]["initial_message"]}
            ]
            
            if self.save_full_dialogs:
                dialog_stats["full_dialog"].extend(messages)
            
            dialog_stats["messages_received"] += 1
            
            # Генерируем большое количество сообщений
            for i in range(self.messages_per_dialog):
                # Создаем и добавляем сообщение пользователя
                user_messages = generate_mock_dialog_messages(issue_id, 1)
                user_message = user_messages[0]
                messages.append(user_message)
                
                if self.save_full_dialogs:
                    dialog_stats["full_dialog"].append(user_message)
                
                dialog_stats["messages_sent"] += 1
                
                # Засекаем время получения ответа от AI
                logger.info(f"Dialog {dialog_id}: Sending message {i+1}/{self.messages_per_dialog}")
                
                try:
                    # Временно ограничиваем контекст последними 20 сообщениями,
                    # чтобы избежать слишком длинного контекста и ошибок
                    # В реальном приложении следует использовать более сложную логику
                    # для управления контекстом длинных диалогов
                    recent_messages = messages[-20:] if len(messages) > 20 else messages
                    
                    # Получаем ответ от AI
                    ai_response, response_time = await measure_execution_time(
                        get_llm_response, recent_messages, user_id, issue_id
                    )
                    
                    dialog_stats["response_times"].append(response_time)
                    self.results.add_response_time(response_time)
                    
                    # Добавляем ответ AI в историю
                    if ai_response:
                        ai_message = {"role": "assistant", "content": ai_response}
                        messages.append(ai_message)
                        
                        if self.save_full_dialogs:
                            dialog_stats["full_dialog"].append(ai_message)
                        
                        dialog_stats["messages_received"] += 1
                        dialog_stats["token_counts"].append(len(ai_response.split()))
                    else:
                        error = f"Не получен ответ от AI в диалоге {dialog_id}, сообщение {i+1}"
                        dialog_stats["errors"].append(error)
                        self.results.add_error(error)
                
                except Exception as e:
                    error = f"Ошибка в диалоге {dialog_id}, сообщение {i+1}: {str(e)}"
                    dialog_stats["errors"].append(error)
                    self.results.add_error(error)
                    
                    # Добавляем заглушку для ответа, чтобы продолжить диалог
                    fallback_message = {"role": "assistant", "content": "Извините, произошла техническая ошибка. Продолжим нашу беседу?"}
                    messages.append(fallback_message)
                    
                    if self.save_full_dialogs:
                        dialog_stats["full_dialog"].append(fallback_message)
                
                # Логируем прогресс
                if (i + 1) % 10 == 0:
                    logger.info(f"Dialog {dialog_id}: {i+1}/{self.messages_per_dialog} messages processed")
                
                # Добавляем задержку между сообщениями
                await asyncio.sleep(self.message_delay)
        
        except Exception as e:
            error = f"Критическая ошибка в диалоге {dialog_id}: {str(e)}"
            dialog_stats["errors"].append(error)
            self.results.add_error(error)
        
        finally:
            # Завершаем диалог и фиксируем статистику
            dialog_stats["end_time"] = time.time()
            dialog_stats["duration"] = dialog_stats["end_time"] - dialog_stats["start_time"]
            
            # Анализируем времена ответа
            if dialog_stats["response_times"]:
                dialog_stats["avg_response_time"] = sum(dialog_stats["response_times"]) / len(dialog_stats["response_times"])
                dialog_stats["min_response_time"] = min(dialog_stats["response_times"])
                dialog_stats["max_response_time"] = max(dialog_stats["response_times"])
            
            # Сохраняем статистику по токенам
            if dialog_stats["token_counts"]:
                dialog_stats["avg_tokens"] = sum(dialog_stats["token_counts"]) / len(dialog_stats["token_counts"])
                dialog_stats["min_tokens"] = min(dialog_stats["token_counts"])
                dialog_stats["max_tokens"] = max(dialog_stats["token_counts"])
            
            logger.info(f"Dialog {dialog_id} completed with {dialog_stats['messages_sent']} user messages and "
                       f"{dialog_stats['messages_received']} AI responses")
        
        return dialog_stats
    
    def create_response_time_graph(self, dialog_stats: List[Dict[str, Any]]) -> str:
        """
        Создает график изменения времени отклика в ходе длинного диалога
        
        Args:
            dialog_stats: Список статистик по диалогам
            
        Returns:
            Путь к сохраненному графику
        """
        # Создаем подкаталог для графиков
        graphs_dir = os.path.join(self.results.result_dir, "graphs")
        os.makedirs(graphs_dir, exist_ok=True)
        
        # Подготавливаем данные для графика
        plt.figure(figsize=(12, 6))
        
        for stats in dialog_stats:
            dialog_id = stats["dialog_id"]
            response_times = stats["response_times"]
            x = list(range(1, len(response_times) + 1))
            plt.plot(x, response_times, label=f"Dialog {dialog_id}")
        
        plt.title("Время отклика в ходе длинного диалога")
        plt.xlabel("Номер сообщения")
        plt.ylabel("Время отклика (мс)")
        plt.grid(True)
        plt.legend()
        
        # Сохраняем график
        graph_path = os.path.join(graphs_dir, "response_times.png")
        plt.savefig(graph_path)
        plt.close()
        
        return graph_path
    
    async def run(self) -> Dict[str, Any]:
        """
        Запускает тест на длинные диалоги
        
        Returns:
            Словарь с результатами теста
        """
        logger.info(f"Запуск теста длинных диалогов с {self.num_dialogs} диалогами, "
                   f"{self.messages_per_dialog} сообщений в каждом")
        
        # Создаем задачи для всех диалогов
        tasks = []
        for i in range(self.num_dialogs):
            task = asyncio.create_task(self.run_long_dialog(i + 1))
            tasks.append(task)
        
        # Запускаем все диалоги одновременно
        try:
            start_time = time.time()
            dialogs_results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Обрабатываем результаты
            dialog_stats = []
            for result in dialogs_results:
                if isinstance(result, Exception):
                    self.results.add_error(f"Exception in dialog: {str(result)}")
                else:
                    dialog_stats.append(result)
            
            # Сохраняем статистику по диалогам
            self.results.set_test_data("dialog_stats", dialog_stats)
            self.results.set_test_data("actual_test_duration", end_time - start_time)
            
            # Создаем графики, если есть хотя бы один успешный диалог
            if dialog_stats:
                try:
                    graph_path = self.create_response_time_graph(dialog_stats)
                    self.results.set_test_data("graph_path", graph_path)
                except Exception as e:
                    logger.error(f"Error creating graph: {str(e)}")
            
            # Сохраняем полные тексты диалогов в отдельные файлы
            if self.save_full_dialogs:
                dialogs_dir = os.path.join(self.results.result_dir, "full_dialogs")
                os.makedirs(dialogs_dir, exist_ok=True)
                
                for dialog in dialog_stats:
                    if "full_dialog" in dialog and dialog["full_dialog"]:
                        dialog_path = os.path.join(dialogs_dir, f"dialog_{dialog['dialog_id']}.json")
                        with open(dialog_path, 'w', encoding='utf-8') as f:
                            json.dump(dialog["full_dialog"], f, ensure_ascii=False, indent=2)
                        
                        # Удаляем полные тексты из результатов для экономии места
                        dialog.pop("full_dialog", None)
            
            # Сохраняем результаты
            results = self.results.save_results()
            
            # Автоматически создаем визуализацию если включена опция
            if self.auto_visualize:
                self.visualize_results(results)
            
            logger.info(f"Тест завершен. Обработано {len(dialog_stats)} диалогов за {end_time - start_time:.2f} секунд")
            return results
            
        except Exception as e:
            self.results.add_error(f"Critical error in test: {str(e)}")
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
            
            # Добавляем график изменения времени отклика для диалогов
            graphs_dir = os.path.join(self.results.result_dir, "graphs")
            if os.path.exists(graphs_dir):
                graph_path = os.path.join(graphs_dir, "response_times.png")
                if os.path.exists(graph_path):
                    output_files["Время отклика по диалогам"] = graph_path
            
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
        "num_dialogs": 3,
        "messages_per_dialog": 100,
        "message_delay": 0.5,
        "save_full_dialogs": True,
        "auto_visualize": True  # Автоматическая визуализация по умолчанию включена
    }
    
    # Создаем и запускаем тест
    test = LongDialogsTest(**params)
    results = await test.run()
    
    # Выводим краткую статистику
    print("\n=== Результаты теста длинных диалогов ===")
    print(f"Количество диалогов: {params['num_dialogs']}")
    print(f"Сообщений в диалоге: {params['messages_per_dialog']}")
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
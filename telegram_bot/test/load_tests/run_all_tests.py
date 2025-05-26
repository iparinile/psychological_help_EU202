import sys
import os
import asyncio
import argparse
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Определяем пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEST_DIR = os.path.dirname(os.path.abspath(__file__))

# Добавляем корневую директорию проекта в путь для импорта
sys.path.append(BASE_DIR)

# Импортируем тесты
from telegram_bot.test.load_tests.test_concurrent_dialogs import ConcurrentDialogsTest
from telegram_bot.test.load_tests.test_response_time import ResponseTimeTest
from telegram_bot.test.load_tests.test_long_dialogs import LongDialogsTest

# Настройка логирования
os.makedirs(os.path.join(TEST_DIR, "result_tests"), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(TEST_DIR, "result_tests", "all_tests.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("run_all_tests")

async def run_concurrent_dialogs_test(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Запускает тест одновременных диалогов с заданными параметрами
    
    Args:
        args: Аргументы командной строки
        
    Returns:
        Результаты теста
    """
    logger.info("Starting concurrent dialogs test")
    
    params = {
        "num_users": args.concurrent_users,
        "messages_per_dialog": args.concurrent_messages,
        "concurrent_requests": args.concurrent_requests,
        "message_delay": args.concurrent_delay,
        "test_duration": args.concurrent_duration,
        "auto_visualize": not args.no_visualize
    }
    
    test = ConcurrentDialogsTest(**params)
    results = await test.run()
    
    logger.info(f"Concurrent dialogs test completed. Results saved to {test.results.result_dir}")
    return results

async def run_response_time_test(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Запускает тест времени отклика с заданными параметрами
    
    Args:
        args: Аргументы командной строки
        
    Returns:
        Результаты теста
    """
    logger.info("Starting response time test")
    
    params = {
        "total_requests": args.response_requests,
        "batch_size": args.response_batch,
        "ramp_up_seconds": args.response_ramp_up,
        "request_timeout": args.response_timeout,
        "auto_visualize": not args.no_visualize
    }
    
    test = ResponseTimeTest(**params)
    results = await test.run()
    
    logger.info(f"Response time test completed. Results saved to {test.results.result_dir}")
    return results

async def run_long_dialogs_test(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Запускает тест длительных диалогов с заданными параметрами
    
    Args:
        args: Аргументы командной строки
        
    Returns:
        Результаты теста
    """
    logger.info("Starting long dialogs test")
    
    params = {
        "num_dialogs": args.long_dialogs,
        "messages_per_dialog": args.long_messages,
        "message_delay": args.long_delay,
        "save_full_dialogs": args.long_save_full,
        "auto_visualize": not args.no_visualize
    }
    
    test = LongDialogsTest(**params)
    results = await test.run()
    
    logger.info(f"Long dialogs test completed. Results saved to {test.results.result_dir}")
    return results

async def run_all_tests(args: argparse.Namespace) -> List[Dict[str, Any]]:
    """
    Запускает все выбранные тесты последовательно
    
    Args:
        args: Аргументы командной строки
        
    Returns:
        Список результатов всех тестов
    """
    logger.info("Starting all load tests")
    start_time = time.time()
    
    results = []
    
    # Определяем, какие тесты запускать
    tests_to_run = []
    
    if args.all or args.concurrent:
        tests_to_run.append(("concurrent_dialogs", run_concurrent_dialogs_test))
    
    if args.all or args.response:
        tests_to_run.append(("response_time", run_response_time_test))
    
    if args.all or args.long:
        tests_to_run.append(("long_dialogs", run_long_dialogs_test))
    
    # Запускаем тесты последовательно
    for test_name, test_func in tests_to_run:
        print(f"\n=== Запуск теста: {test_name} ===")
        try:
            test_results = await test_func(args)
            results.append(test_results)
            print(f"=== Тест {test_name} завершен успешно ===")
        except Exception as e:
            print(f"=== Ошибка при выполнении теста {test_name}: {str(e)} ===")
    
    end_time = time.time()
    
    # Сохраняем общие результаты
    summary = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_duration": round(end_time - start_time, 2),
        "tests_run": [test_name for test_name, _ in tests_to_run],
        "results_summary": {}
    }
    
    # Проверяем, что results содержит словари, а не кортежи
    for i, result in enumerate(results):
        test_name = tests_to_run[i][0]
        summary["results_summary"][test_name] = {
            "total_requests": result["total_requests"],
            "successful_requests": result["successful_requests"],
            "failed_requests": result["failed_requests"],
            "avg_response_time_ms": result["response_time_stats"]["avg_ms"],
            "p95_response_time_ms": result["response_time_stats"]["p95_ms"]
        }
    
    # Сохраняем общий отчет
    results_dir = os.path.join(TEST_DIR, "result_tests")
    summary_path = os.path.join(results_dir, f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    logger.info(f"All tests completed in {end_time - start_time:.2f} seconds")
    logger.info(f"Summary saved to {summary_path}")
    
    return results

def parse_args() -> argparse.Namespace:
    """
    Парсит аргументы командной строки
    
    Returns:
        Распарсенные аргументы
    """
    parser = argparse.ArgumentParser(description="Запуск нагрузочных тестов для чат-бота")
    
    # Аргументы для выбора тестов
    test_group = parser.add_argument_group("Выбор тестов")
    test_group.add_argument("--all", action="store_true", help="Запустить все тесты")
    test_group.add_argument("--concurrent", action="store_true", help="Запустить тест одновременных диалогов")
    test_group.add_argument("--response", action="store_true", help="Запустить тест времени отклика")
    test_group.add_argument("--long", action="store_true", help="Запустить тест длительных диалогов")
    
    # Аргументы для теста одновременных диалогов
    concurrent_group = parser.add_argument_group("Параметры теста одновременных диалогов")
    concurrent_group.add_argument("--concurrent-users", type=int, default=10, help="Количество одновременных пользователей")
    concurrent_group.add_argument("--concurrent-messages", type=int, default=5, help="Количество сообщений в каждом диалоге")
    concurrent_group.add_argument("--concurrent-requests", type=int, default=5, help="Максимальное количество одновременных запросов")
    concurrent_group.add_argument("--concurrent-delay", type=float, default=1.0, help="Задержка между сообщениями одного пользователя (секунды)")
    concurrent_group.add_argument("--concurrent-duration", type=int, default=120, help="Максимальная длительность теста (секунды)")
    
    # Аргументы для теста времени отклика
    response_group = parser.add_argument_group("Параметры теста времени отклика")
    response_group.add_argument("--response-requests", type=int, default=100, help="Общее количество запросов")
    response_group.add_argument("--response-batch", type=int, default=10, help="Размер пакета одновременных запросов")
    response_group.add_argument("--response-ramp-up", type=int, default=30, help="Время для постепенного увеличения нагрузки (секунды)")
    response_group.add_argument("--response-timeout", type=int, default=60, help="Таймаут для одного запроса (секунды)")
    
    # Аргументы для теста длительных диалогов
    long_group = parser.add_argument_group("Параметры теста длительных диалогов")
    long_group.add_argument("--long-dialogs", type=int, default=3, help="Количество одновременных длинных диалогов")
    long_group.add_argument("--long-messages", type=int, default=100, help="Количество сообщений в каждом диалоге")
    long_group.add_argument("--long-delay", type=float, default=0.5, help="Задержка между сообщениями (секунды)")
    long_group.add_argument("--long-save-full", action="store_true", help="Сохранять полные тексты диалогов")
    
    # Общие аргументы
    general_group = parser.add_argument_group("Общие параметры")
    general_group.add_argument("--no-visualize", action="store_true", help="Отключить автоматическую визуализацию результатов")
    
    args = parser.parse_args()
    
    # Если не выбрано ни одного теста, запускаем все
    if not (args.all or args.concurrent or args.response or args.long):
        args.all = True
    
    return args

async def main():
    """Точка входа для запуска всех тестов"""
    args = parse_args()
    
    print("\n=== Запуск нагрузочных тестов для чат-бота ===")
    
    results = await run_all_tests(args)
    
    print(f"\n=== Все тесты завершены. Выполнено {len(results)} тестов ===")

if __name__ == "__main__":
    asyncio.run(main()) 
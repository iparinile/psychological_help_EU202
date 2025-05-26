import json
import time
import os
import logging
import asyncio
import csv
import random
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Настройка логирования
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEST_DIR = os.path.dirname(os.path.abspath(__file__))

# Создаем директорию для логов, если она не существует
os.makedirs(os.path.join(TEST_DIR, "result_tests"), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(TEST_DIR, "result_tests", "load_test.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("load_test")

# Путь для сохранения результатов
RESULTS_DIR = os.path.join(TEST_DIR, "result_tests")

class TestResults:
    """Класс для хранения результатов тестов"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = time.time()
        self.end_time = None
        self.response_times = []
        self.errors = []
        self.test_data = {}
        
        # Создаем подкаталог для результатов конкретного теста
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.result_dir = os.path.join(RESULTS_DIR, f"{test_name}_{self.timestamp}")
        os.makedirs(self.result_dir, exist_ok=True)
    
    def add_response_time(self, response_time: float):
        """Добавить время ответа в миллисекундах"""
        self.response_times.append(response_time)
    
    def add_error(self, error: str):
        """Добавить информацию об ошибке"""
        self.errors.append(error)
        logger.error(f"Test error: {error}")
    
    def set_test_data(self, key: str, value: Any):
        """Добавить произвольные данные о тесте"""
        self.test_data[key] = value
    
    def complete(self):
        """Завершить тест и зафиксировать время окончания"""
        self.end_time = time.time()
    
    def save_results(self):
        """Сохранить результаты тестирования в JSON"""
        self.complete()
        
        # Вычисляем метрики
        response_times = self.response_times
        results = {
            "test_name": self.test_name,
            "timestamp": self.timestamp,
            "duration_seconds": round(self.end_time - self.start_time, 2),
            "total_requests": len(response_times),
            "successful_requests": len(response_times) - len(self.errors),
            "failed_requests": len(self.errors),
            "response_time_stats": {
                "min_ms": round(min(response_times, default=0), 2),
                "max_ms": round(max(response_times, default=0), 2),
                "avg_ms": round(sum(response_times) / len(response_times) if response_times else 0, 2),
                "p50_ms": round(calculate_percentile(response_times, 50), 2),
                "p90_ms": round(calculate_percentile(response_times, 90), 2),
                "p95_ms": round(calculate_percentile(response_times, 95), 2),
                "p99_ms": round(calculate_percentile(response_times, 99), 2)
            },
            "errors": self.errors,
            "test_data": self.test_data
        }
        
        # Сохраняем основной JSON-отчет
        json_path = os.path.join(self.result_dir, "results.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Сохраняем детальные времена ответа в CSV для дальнейшего анализа
        csv_path = os.path.join(self.result_dir, "response_times.csv")
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["request_number", "response_time_ms"])
            for i, rt in enumerate(self.response_times, 1):
                writer.writerow([i, round(rt, 2)])
        
        logger.info(f"Test results saved to {self.result_dir}")
        return results

def calculate_percentile(data: List[float], percentile: int) -> float:
    """Вычислить процентиль из списка значений"""
    if not data:
        return 0
    
    sorted_data = sorted(data)
    index = (len(sorted_data) - 1) * percentile / 100
    
    if index.is_integer():
        return sorted_data[int(index)]
    else:
        lower_index = int(index)
        upper_index = lower_index + 1
        lower_value = sorted_data[lower_index]
        upper_value = sorted_data[upper_index]
        return lower_value + (upper_value - lower_value) * (index - lower_index)

def generate_user_id() -> str:
    """Генерирует уникальный ID пользователя для тестирования"""
    return f"test_user_{int(time.time())}_{random.randint(1000, 9999)}"

def generate_mock_dialog_messages(issue_id: str, message_count: int = 5) -> List[Dict[str, str]]:
    """
    Генерирует последовательность сообщений для тестового диалога
    
    Args:
        issue_id: ID типа проблемы ('1', '2', '3')
        message_count: Количество пар сообщений (вопрос-ответ)
        
    Returns:
        Список сообщений для тестирования
    """
    messages = []
    
    # Базовые шаблоны вопросов для разных типов проблем
    templates = {
        "1": [  # Депрессия
            "Я чувствую себя подавленным последнее время.",
            "Мне сложно находить радость в обычных вещах.",
            "Я постоянно чувствую усталость и апатию.",
            "Мне кажется, что ничего хорошего в будущем не ждет.",
            "Мне сложно сосредоточиться на работе.",
            "Я стал плохо спать по ночам.",
            "Я часто думаю о смысле жизни.",
            "Мне сложно заставить себя что-то делать."
        ],
        "2": [  # Проблемы на работе
            "Я чувствую выгорание на работе.",
            "Мой начальник постоянно меня критикует.",
            "Мне кажется, что моя работа бессмысленна.",
            "Я не справляюсь с нагрузкой на работе.",
            "Коллеги не ценят мой вклад в проекты.",
            "Я не вижу перспектив роста в компании.",
            "Я часто беру работу на дом и не отдыхаю.",
            "Мне сложно отказывать, когда просят о дополнительных задачах."
        ],
        "3": [  # Проблемы в отношениях
            "Мы с партнером постоянно ссоримся.",
            "Я чувствую, что партнер меня не понимает.",
            "Я не уверен(а), что наши отношения имеют будущее.",
            "Мы отдалились друг от друга в последнее время.",
            "Я не могу доверять своему партнеру после измены.",
            "Мы перестали разговаривать о важных вещах.",
            "Я чувствую, что отношения меня истощают.",
            "Мы по-разному смотрим на будущее."
        ]
    }
    
    # Выбираем шаблоны для указанного типа проблемы
    issue_templates = templates.get(issue_id, templates["1"])
    
    # Генерируем диалог
    for i in range(message_count):
        # Сообщение пользователя
        user_message = random.choice(issue_templates)
        if i > 0:
            # Добавляем немного разнообразия в сообщения
            if random.random() > 0.5:
                user_message += f" {random.choice(['Что мне делать?', 'Как с этим справиться?', 'Это нормально?', 'Почему так происходит?'])}"
        
        messages.append({"role": "user", "content": user_message})
        
        # Не добавляем ответ ассистента в последнем шаге
        if i < message_count - 1:
            # Заглушка для ответа ассистента (в реальном тесте будет заменена на ответ от модели)
            messages.append({"role": "assistant", "content": f"Ответ психолога на сообщение {i+1}"})
    
    return messages

async def measure_execution_time(func, *args, **kwargs) -> Tuple[Any, float]:
    """Измеряет время выполнения асинхронной функции в миллисекундах"""
    start_time = time.time()
    try:
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
        return result, (time.time() - start_time) * 1000
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        logger.error(f"Error in function {func.__name__}: {str(e)}")
        return None, execution_time 
# Тесты для Telegram-бота психологической поддержки

В этой директории содержатся тесты для проверки работоспособности и производительности бота.

## Структура директории

```
test/
├── README.md              # Этот файл
└── load_tests/            # Нагрузочные тесты
    ├── run_all_tests.py   # Скрипт для запуска всех нагрузочных тестов
    ├── test_concurrent_dialogs.py  # Тест одновременных диалогов
    ├── test_response_time.py       # Тест времени отклика
    ├── test_long_dialogs.py        # Тест длительных диалогов
    ├── utils.py                    # Общие утилиты для тестирования
    ├── visualize_results.py        # Скрипт для визуализации результатов
    └── result_tests/               # Директория с результатами тестов
```

## Нагрузочное тестирование

В директории `load_tests` содержатся скрипты для нагрузочного тестирования системы чат-бота психологической поддержки. Тесты симулируют реальную нагрузку на API и измеряют производительность системы в различных сценариях.

### Требования

Для запуска тестов установите все зависимости из корневого файла requirements.txt:

```bash
pip install -r requirements.txt
```

### Типы тестов

1. **Тест одновременных диалогов** (test_concurrent_dialogs.py)
   - Симулирует несколько пользователей, одновременно ведущих диалоги с ботом
   - Проверяет работу бота при параллельной обработке запросов
   - **Параметры теста:**
     - `num_users` - количество одновременных пользователей
     - `messages_per_dialog` - количество сообщений в каждом диалоге
     - `concurrent_requests` - максимальное количество одновременных запросов
     - `message_delay` - задержка между сообщениями одного пользователя (секунды)
     - `test_duration` - максимальная длительность теста (секунды)

2. **Тест времени отклика** (test_response_time.py)
   - Отправляет большое количество одиночных запросов
   - Измеряет время отклика и строит его распределение
   - **Параметры теста:**
     - `total_requests` - общее количество запросов
     - `batch_size` - размер пакета одновременных запросов
     - `ramp_up_seconds` - время для постепенного увеличения нагрузки (секунды)
     - `request_timeout` - таймаут для одного запроса (секунды)

3. **Тест длительных диалогов** (test_long_dialogs.py)
   - Симулирует длительные диалоги (100+ сообщений)
   - Проверяет деградацию производительности в длительных сессиях
   - **Параметры теста:**
     - `num_dialogs` - количество одновременных длинных диалогов
     - `messages_per_dialog` - количество сообщений в каждом диалоге
     - `message_delay` - задержка между сообщениями (секунды)
     - `save_full_dialogs` - сохранять ли полные тексты диалогов

### Запуск тестов

Для запуска всех тестов:

```bash
python -m telegram_bot.test.load_tests.run_all_tests --all
```

Для запуска отдельных тестов:

```bash
# Только тест одновременных диалогов
python -m telegram_bot.test.load_tests.run_all_tests --concurrent

# Только тест времени отклика
python -m telegram_bot.test.load_tests.run_all_tests --response

# Только тест длительных диалогов
python -m telegram_bot.test.load_tests.run_all_tests --long
```

### Настройка параметров тестов

```bash
# Пример: изменение параметров теста одновременных диалогов
python -m telegram_bot.test.load_tests.run_all_tests --concurrent --concurrent-users 20 --concurrent-messages 10

# Пример: изменение параметров теста времени отклика
python -m telegram_bot.test.load_tests.run_all_tests --response --response-requests 200 --response-batch 20

# Пример: изменение параметров теста длительных диалогов
python -m telegram_bot.test.load_tests.run_all_tests --long --long-dialogs 5 --long-messages 50
```

### Параметры командной строки

```
usage: run_all_tests.py [-h] [--all] [--concurrent] [--response] [--long]
                       [--concurrent-users CONCURRENT_USERS]
                       [--concurrent-messages CONCURRENT_MESSAGES]
                       [--concurrent-requests CONCURRENT_REQUESTS]
                       [--concurrent-delay CONCURRENT_DELAY]
                       [--concurrent-duration CONCURRENT_DURATION]
                       [--response-requests RESPONSE_REQUESTS]
                       [--response-batch RESPONSE_BATCH]
                       [--response-ramp-up RESPONSE_RAMP_UP]
                       [--response-timeout RESPONSE_TIMEOUT]
                       [--long-dialogs LONG_DIALOGS]
                       [--long-messages LONG_MESSAGES]
                       [--long-delay LONG_DELAY]
                       [--long-save-full]
                       [--no-visualize]
```

### Результаты тестов

После выполнения тестов результаты сохраняются в директории `telegram_bot/test/load_tests/result_tests/` в следующих форматах:

1. JSON-файлы с детальной информацией о тестах
2. CSV-файлы с временами отклика для каждого запроса
3. Графики времени отклика (для теста длительных диалогов)
4. Полные тексты диалогов (если включена соответствующая опция)
5. HTML-отчёты с графиками

### Визуализация результатов

После завершения каждого теста автоматически создаётся HTML-отчёт с графиками и метриками в директории с результатами теста. Путь к отчёту будет выведен в консоль после завершения теста.

Если вы хотите отключить автоматическую визуализацию, используйте флаг `--no-visualize`:

```bash
# Запуск теста без автоматической визуализации
python -m telegram_bot.test.load_tests.run_all_tests --no-visualize
```

#### Возможности визуализации

- Гистограмма распределения времени отклика
- Круговая диаграмма успешных/неуспешных запросов
- Сравнительная диаграмма перцентилей времени отклика (min, avg, p50, p90, p95, p99, max)
- График изменения времени отклика по ходу теста
- HTML-отчёт с табличными данными и интерактивными графиками

#### Ручная визуализация результатов

Вы также можете отдельно запустить визуализацию для ранее проведённых тестов:

```bash
# Визуализация последних результатов теста
python -m telegram_bot.test.load_tests.visualize_results

# Визуализация результатов конкретного типа теста
python -m telegram_bot.test.load_tests.visualize_results --type concurrent_dialogs
python -m telegram_bot.test.load_tests.visualize_results --type response_time
python -m telegram_bot.test.load_tests.visualize_results --type long_dialogs

# Визуализация результатов из указанного файла
python -m telegram_bot.test.load_tests.visualize_results --results path/to/results.json
```

### Просмотр результатов

Для каждого теста создается отдельная папка с именем вида `test_name_YYYYMMDD_HHMMSS`.

Для открытия HTML-отчета:
```bash
# Windows
start telegram_bot\test\load_tests\result_tests\<test_name>_<timestamp>\report.html
```

### Интерпретация результатов

Основные метрики для анализа:

- **Среднее время отклика** - среднее время, которое требуется системе для ответа на запрос
- **Медианное время отклика (P50)** - время, за которое обрабатывается 50% запросов
- **P90, P95, P99 времени отклика** - время, за которое обрабатывается 90%, 95% и 99% запросов соответственно
- **Количество успешных/неуспешных запросов** - сколько запросов было обработано успешно/с ошибками
- **Запросов в секунду (RPS)** - количество запросов, которое система может обработать за секунду

### Примеры использования

#### Тестирование с увеличенным количеством пользователей

```bash
python -m telegram_bot.test.load_tests.run_all_tests --concurrent --concurrent-users 50 --concurrent-messages 10
```

#### Тестирование отклика при высокой нагрузке

```bash
python -m telegram_bot.test.load_tests.run_all_tests --response --response-requests 500 --response-batch 50
```

#### Тестирование очень длинных диалогов

```bash
python -m telegram_bot.test.load_tests.run_all_tests --long --long-messages 200 --long-save-full
```

### Примечания 

- Тесты создают значительную нагрузку на систему. Запускайте их в тестовой среде.
- Учитывайте ограничения API и внешних сервисов (например, OpenRouter) при настройке параметров.
- Для длительных тестов используйте меньшее количество одновременных диалогов.
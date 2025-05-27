# Модульные тесты проекта психологической помощи

Этот каталог содержит модульные тесты для основных компонентов системы психологической помощи.

## 📊 Что тестируется

- **База данных** (7 тестов) - функции работы с SQLite базой данных
- **Диалоги** (5 тестов) - инициализация диалогов и работа с LLM  
- **Рекомендации книг** (5 тестов) - генерация и форматирование рекомендаций

**Всего: 17 модульных тестов**

## Быстрый старт

> 💡 **Для Windows используйте `py`**

### Основные команды

```bash
# Запуск всех тестов с HTML-отчетом (рекомендуется)
py -m telegram_bot.test.modul_test.tests.test_runner

# Отдельные модули с подробным выводом
py -m unittest telegram_bot.test.modul_test.tests.test_database -v
py -m unittest telegram_bot.test.modul_test.tests.test_dialogue -v  
py -m unittest telegram_bot.test.modul_test.tests.test_books -v

# Конкретный тест
py -m unittest telegram_bot.test.modul_test.tests.test_database.TestDatabase.test_log_dialogue
```

## 📋 HTML-отчеты

Автоматически генерируются в папке `modul_test/tests/reports/`:

- **`latest_report.html`** - последний отчет (удобная ссылка)
- **`index.html`** - история всех запусков  
- **`test_report_YYYYMMDD_HHMMSS.html`** - отчеты с временными метками

Отчеты содержат детальную статистику, группировку по модулям и информацию об ошибках.

## ⚙️ Требования

- **Python 3.8+**
- **Зависимости**: все пакеты из `requirements.txt`
- **Конфигурация**: `config.json` для AI-сервиса (для полных тестов)

> **Windows**: используйте команду `py`


## Пример успешного запуска

После выполнения `py -m telegram_bot.test.modul_test.tests.test_runner` вы увидите:

```
Результаты тестирования:
Всего тестов: 17
Успешно: 17
Неудачно: 0
Ошибки: 0

Отчет доступен по пути: C:\...\telegram_bot\test\modul_test\tests\reports\latest_report.html
```

## 📚 Подробная документация

Детальное описание тестов и дополнительные команды: **`modul_test/tests/README.md`**

---

> 💡 **Есть также нагрузочные тесты** в папке `load_tests/` - это отдельная система для тестирования производительности. 
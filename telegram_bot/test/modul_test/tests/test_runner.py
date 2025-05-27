import unittest
import sys
import os
from datetime import datetime

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from telegram_bot.test.modul_test.tests.test_database import TestDatabase
from telegram_bot.test.modul_test.tests.test_dialogue import TestDialogue
from telegram_bot.test.modul_test.tests.test_books import TestBooks
from telegram_bot.test.modul_test.tests.test_reporter import HTMLTestRunner

if __name__ == '__main__':
    # Директория для отчетов
    report_dir = os.path.join(os.path.dirname(__file__), 'reports')
    
    # Создаем директорию для отчетов, если её нет
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    # Создаем загрузчик тестов
    loader = unittest.TestLoader()
    
    # Создаем набор тестов
    test_suite = unittest.TestSuite()
    
    # Добавляем тесты из каждого класса
    test_suite.addTests(loader.loadTestsFromTestCase(TestDatabase))
    test_suite.addTests(loader.loadTestsFromTestCase(TestDialogue))
    test_suite.addTests(loader.loadTestsFromTestCase(TestBooks))
    
    # Создаем и настраиваем раннер с HTML-отчетом
    runner = HTMLTestRunner(
        report_dir=report_dir,
        verbosity=2
    )
    
    # Запускаем тесты
    result = runner.run(test_suite)
    
    # Выводим информацию о результатах
    print(f"\nРезультаты тестирования:")
    print(f"Всего тестов: {result.testsRun}")
    print(f"Успешно: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Неудачно: {len(result.failures)}")
    print(f"Ошибки: {len(result.errors)}")
    
    # Выводим путь к последнему отчету
    latest_report_path = os.path.join(report_dir, "latest_report.html")
    print(f"\nОтчет доступен по пути: {os.path.abspath(latest_report_path)}")
    
    # Обновляем индекс отчетов
    index_path = os.path.join(report_dir, "index.html")
    
    # Получаем список всех отчетов
    report_files = [f for f in os.listdir(report_dir) if f.startswith("test_report_") and f.endswith(".html")]
    report_files.sort(reverse=True)  # Сортируем по убыванию (новые в начале)
    
    # Создаем индексный файл со списком всех отчетов
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>История отчетов о тестировании</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        a { color: #0275d8; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>История отчетов о тестировании</h1>
    <p>Ниже представлен список всех отчетов о тестировании, начиная с самых новых.</p>
    <p><a href="latest_report.html">Последний отчет</a></p>
    <table>
        <tr>
            <th>Дата и время</th>
            <th>Отчет</th>
        </tr>
""")
        
        # Добавляем строки для каждого отчета
        for report_file in report_files:
            # Извлекаем временную метку из имени файла
            timestamp = report_file.replace("test_report_", "").replace(".html", "")
            try:
                # Преобразуем в читаемый формат даты и времени
                date_time = datetime.strptime(timestamp, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                date_time = timestamp
            
            f.write(f"""        <tr>
            <td>{date_time}</td>
            <td><a href="{report_file}">{report_file}</a></td>
        </tr>
""")
        
        f.write("""    </table>
</body>
</html>
""")
    
    print(f"История отчетов доступна по пути: {os.path.abspath(index_path)}")
    
    # Выходим с кодом ошибки, если были неудачные тесты
    sys.exit(not result.wasSuccessful()) 
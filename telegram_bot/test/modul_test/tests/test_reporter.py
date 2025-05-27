import unittest
import datetime
import os
import time
import traceback
from html import escape

class HTMLTestReporter:
    """Генератор HTML-отчетов о результатах тестирования"""
    
    def __init__(self, report_dir='telegram_bot/test/modul_test/tests/reports'):
        """Инициализация генератора отчетов
        
        Args:
            report_dir (str): Директория для сохранения отчетов
        """
        self.report_dir = report_dir
        self.start_time = None
        self.stop_time = None
        self.success_count = 0
        self.failure_count = 0
        self.error_count = 0
        self.skip_count = 0
        self.all_tests = []
        self.failed_tests = []
        self.errors = []
        self.skipped = []
        
        # Создаем директорию для отчетов, если её нет
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
    
    def start_test_run(self):
        """Начало запуска тестов"""
        self.start_time = datetime.datetime.now()
    
    def stop_test_run(self):
        """Окончание запуска тестов"""
        self.stop_time = datetime.datetime.now()
    
    def add_success(self, test):
        """Добавление успешного теста
        
        Args:
            test (unittest.TestCase): Тестовый случай
        """
        self.success_count += 1
        self.all_tests.append((test, 'success', None))
    
    def add_failure(self, test, err):
        """Добавление неудачного теста
        
        Args:
            test (unittest.TestCase): Тестовый случай
            err (tuple): Информация об ошибке (тип, значение, трейсбек)
        """
        self.failure_count += 1
        self.failed_tests.append((test, err))
        self.all_tests.append((test, 'failure', err))
    
    def add_error(self, test, err):
        """Добавление теста с ошибкой
        
        Args:
            test (unittest.TestCase): Тестовый случай
            err (tuple): Информация об ошибке (тип, значение, трейсбек)
        """
        self.error_count += 1
        self.errors.append((test, err))
        self.all_tests.append((test, 'error', err))
    
    def add_skip(self, test, reason):
        """Добавление пропущенного теста
        
        Args:
            test (unittest.TestCase): Тестовый случай
            reason (str): Причина пропуска
        """
        self.skip_count += 1
        self.skipped.append((test, reason))
        self.all_tests.append((test, 'skip', reason))
    
    def get_test_name(self, test):
        """Получение имени теста
        
        Args:
            test (unittest.TestCase): Тестовый случай
            
        Returns:
            str: Имя теста
        """
        return f"{test.__class__.__module__}.{test.__class__.__name__}.{test._testMethodName}"
    
    def get_test_doc(self, test):
        """Получение документации теста
        
        Args:
            test (unittest.TestCase): Тестовый случай
            
        Returns:
            str: Документация теста
        """
        doc = test._testMethodDoc
        if doc:
            return escape(doc)
        return "Нет описания"
    
    def get_total_tests(self):
        """Получение общего количества тестов
        
        Returns:
            int: Общее количество тестов
        """
        return self.success_count + self.failure_count + self.error_count + self.skip_count
    
    def get_status_counts(self):
        """Получение количества тестов по статусам
        
        Returns:
            dict: Словарь с количеством тестов по статусам
        """
        return {
            'success': self.success_count,
            'failure': self.failure_count,
            'error': self.error_count,
            'skip': self.skip_count,
            'total': self.get_total_tests()
        }
    
    def get_duration(self):
        """Получение длительности выполнения тестов
        
        Returns:
            float: Длительность в секундах
        """
        if self.start_time and self.stop_time:
            return (self.stop_time - self.start_time).total_seconds()
        return 0
    
    def generate_report(self):
        """Генерация HTML-отчета
        
        Returns:
            str: Путь к сгенерированному отчету
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(self.report_dir, f"test_report_{timestamp}.html")
        
        # Генерация HTML-отчета
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(self._generate_html_report())
        
        # Создаем/обновляем файл последнего отчета
        latest_report_path = os.path.join(self.report_dir, "latest_report.html")
        with open(latest_report_path, 'w', encoding='utf-8') as f:
            f.write(self._generate_html_report())
        
        return report_path
    
    def _generate_html_report(self):
        """Генерация HTML-кода отчета
        
        Returns:
            str: HTML-код отчета
        """
        status_counts = self.get_status_counts()
        
        # Вычисляем процент успешных тестов
        total = status_counts['total']
        success_percent = 0
        if total > 0:
            success_percent = round(status_counts['success'] / total * 100, 2)
        
        # Определяем общий статус тестирования
        status_class = 'success'
        if status_counts['failure'] > 0 or status_counts['error'] > 0:
            status_class = 'danger'
        elif status_counts['skip'] > 0:
            status_class = 'warning'
        
        # Генерируем HTML-код
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Отчет о тестировании</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ margin-bottom: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .success {{ background-color: #dff0d8; }}
        .warning {{ background-color: #fcf8e3; }}
        .danger {{ background-color: #f2dede; }}
        .test-details {{ margin-top: 10px; }}
        .test-case {{ margin-bottom: 5px; padding: 10px; border-radius: 5px; }}
        .error-details {{ font-family: monospace; white-space: pre-wrap; margin-top: 10px; }}
        .timestamp {{ color: #888; font-size: 0.9em; }}
    </style>
</head>
<body>
    <h1>Отчет о тестировании проекта психологической помощи</h1>
    
    <div class="timestamp">
        Начало: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}<br>
        Окончание: {self.stop_time.strftime('%Y-%m-%d %H:%M:%S')}<br>
        Длительность: {self.get_duration():.2f} сек
    </div>
    
    <div class="summary">
        <h2>Сводка</h2>
        <table>
            <tr>
                <th>Всего тестов</th>
                <th>Успешно</th>
                <th>Неудачно</th>
                <th>Ошибки</th>
                <th>Пропущено</th>
                <th>Успешность</th>
            </tr>
            <tr class="{status_class}">
                <td>{status_counts['total']}</td>
                <td>{status_counts['success']}</td>
                <td>{status_counts['failure']}</td>
                <td>{status_counts['error']}</td>
                <td>{status_counts['skip']}</td>
                <td>{success_percent}%</td>
            </tr>
        </table>
    </div>
    
    <div class="test-details">
        <h2>Результаты тестов</h2>
"""
        
        # Группируем тесты по модулям и классам
        grouped_tests = {}
        for test, status, err in self.all_tests:
            module = test.__class__.__module__
            class_name = test.__class__.__name__
            
            if module not in grouped_tests:
                grouped_tests[module] = {}
            
            if class_name not in grouped_tests[module]:
                grouped_tests[module][class_name] = []
            
            grouped_tests[module][class_name].append((test, status, err))
        
        # Добавляем результаты тестов по группам
        for module, classes in grouped_tests.items():
            html += f'<h3>Модуль: {module}</h3>\n'
            
            for class_name, tests in classes.items():
                html += f'<h4>Класс: {class_name}</h4>\n'
                html += '<table>\n'
                html += '<tr><th>Тест</th><th>Описание</th><th>Статус</th><th>Детали</th></tr>\n'
                
                for test, status, err in tests:
                    status_text = {
                        'success': 'Успешно',
                        'failure': 'Неудачно',
                        'error': 'Ошибка',
                        'skip': 'Пропущено'
                    }.get(status, status)
                    
                    html += f'<tr class="{status}">\n'
                    html += f'<td>{test._testMethodName}</td>\n'
                    html += f'<td>{self.get_test_doc(test)}</td>\n'
                    html += f'<td>{status_text}</td>\n'
                    
                    # Добавляем детали ошибки, если есть
                    if status in ['failure', 'error']:
                        err_type, err_value, _ = err
                        html += f'<td>{escape(str(err_type.__name__))}: {escape(str(err_value))}</td>\n'
                    elif status == 'skip':
                        html += f'<td>{escape(str(err))}</td>\n'
                    else:
                        html += '<td></td>\n'
                    
                    html += '</tr>\n'
                
                html += '</table>\n'
        
        # Добавляем детали ошибок и неудач, если есть
        if self.failed_tests or self.errors:
            html += '<h2>Детали ошибок и неудач</h2>\n'
            
            # Неудачные тесты
            if self.failed_tests:
                html += '<h3>Неудачные тесты</h3>\n'
                for test, err in self.failed_tests:
                    err_type, err_value, err_tb = err
                    tb_str = ''.join(traceback.format_tb(err_tb))
                    
                    html += f'<div class="test-case danger">\n'
                    html += f'<h4>{self.get_test_name(test)}</h4>\n'
                    html += f'<p>{self.get_test_doc(test)}</p>\n'
                    html += f'<p><strong>{escape(str(err_type.__name__))}</strong>: {escape(str(err_value))}</p>\n'
                    html += f'<div class="error-details">{escape(tb_str)}</div>\n'
                    html += '</div>\n'
            
            # Тесты с ошибками
            if self.errors:
                html += '<h3>Тесты с ошибками</h3>\n'
                for test, err in self.errors:
                    err_type, err_value, err_tb = err
                    tb_str = ''.join(traceback.format_tb(err_tb))
                    
                    html += f'<div class="test-case danger">\n'
                    html += f'<h4>{self.get_test_name(test)}</h4>\n'
                    html += f'<p>{self.get_test_doc(test)}</p>\n'
                    html += f'<p><strong>{escape(str(err_type.__name__))}</strong>: {escape(str(err_value))}</p>\n'
                    html += f'<div class="error-details">{escape(tb_str)}</div>\n'
                    html += '</div>\n'
        
        html += """
    </div>
</body>
</html>
"""
        
        return html


class HTMLTestRunner(unittest.TextTestRunner):
    """Запускатель тестов с генерацией HTML-отчета"""
    
    def __init__(self, report_dir='telegram_bot/test/modul_test/tests/reports', **kwargs):
        """Инициализация запускателя тестов
        
        Args:
            report_dir (str): Директория для сохранения отчетов
            **kwargs: Дополнительные параметры для TextTestRunner
        """
        super().__init__(**kwargs)
        self.report_dir = report_dir
        self.reporter = HTMLTestReporter(report_dir)
    
    def run(self, test):
        """Запуск тестов и генерация отчета
        
        Args:
            test (unittest.TestSuite): Набор тестов
            
        Returns:
            unittest.TestResult: Результат выполнения тестов
        """
        result = _HTMLTestResult(self.reporter, self.descriptions, self.verbosity)
        self.reporter.start_test_run()
        
        startTime = time.time()
        test(result)
        stopTime = time.time()
        timeTaken = stopTime - startTime
        
        self.reporter.stop_test_run()
        report_path = self.reporter.generate_report()
        
        if self.verbosity > 0:
            result.printErrors()
            print(f"Ran {result.testsRun} tests in {timeTaken:.3f}s")
            print(f"HTML report generated: {report_path}")
        
        print(f"HTML report available at: {os.path.abspath(report_path)}")
        return result


class _HTMLTestResult(unittest.TestResult):
    """Результат выполнения тестов с передачей информации в HTML-отчет"""
    
    def __init__(self, reporter, descriptions, verbosity):
        """Инициализация объекта результата тестов
        
        Args:
            reporter (HTMLTestReporter): Генератор отчетов
            descriptions (bool): Флаг включения описаний
            verbosity (int): Уровень подробности вывода
        """
        super().__init__(descriptions, verbosity)
        self.reporter = reporter
        self.descriptions = descriptions
        self.verbosity = verbosity
    
    def startTest(self, test):
        """Начало выполнения теста
        
        Args:
            test (unittest.TestCase): Тестовый случай
        """
        super().startTest(test)
        if self.verbosity > 1:
            print(f"Running: {self.reporter.get_test_name(test)}")
    
    def addSuccess(self, test):
        """Добавление успешного теста
        
        Args:
            test (unittest.TestCase): Тестовый случай
        """
        super().addSuccess(test)
        self.reporter.add_success(test)
        if self.verbosity > 1:
            print(f"Success: {self.reporter.get_test_name(test)}")
    
    def addFailure(self, test, err):
        """Добавление неудачного теста
        
        Args:
            test (unittest.TestCase): Тестовый случай
            err (tuple): Информация об ошибке
        """
        super().addFailure(test, err)
        self.reporter.add_failure(test, err)
        if self.verbosity > 1:
            print(f"Failure: {self.reporter.get_test_name(test)}")
    
    def addError(self, test, err):
        """Добавление теста с ошибкой
        
        Args:
            test (unittest.TestCase): Тестовый случай
            err (tuple): Информация об ошибке
        """
        super().addError(test, err)
        self.reporter.add_error(test, err)
        if self.verbosity > 1:
            print(f"Error: {self.reporter.get_test_name(test)}")
    
    def addSkip(self, test, reason):
        """Добавление пропущенного теста
        
        Args:
            test (unittest.TestCase): Тестовый случай
            reason (str): Причина пропуска
        """
        super().addSkip(test, reason)
        self.reporter.add_skip(test, reason)
        if self.verbosity > 1:
            print(f"Skip: {self.reporter.get_test_name(test)} (Reason: {reason})") 
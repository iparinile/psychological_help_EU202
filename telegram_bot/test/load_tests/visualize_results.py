import os
import json
import sys
import argparse
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Определяем пути
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEST_DIR = os.path.dirname(os.path.abspath(__file__))

def load_results(results_path):
    """Загружает результаты тестов из JSON-файла"""
    with open(results_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_response_time_distribution(results, results_file, output_dir):
    """Создаёт график распределения времени отклика"""
    fig, ax = plt.figure(figsize=(10, 6)), plt.axes()
    
    # Загружаем данные о времени отклика
    csv_file = os.path.join(os.path.dirname(results_file), "response_times.csv")
    if os.path.exists(csv_file):
        import csv
        response_times = []
        with open(csv_file, 'r', newline='') as f:
            reader = csv.reader(f)
            next(reader)  # Пропускаем заголовок
            for row in reader:
                response_times.append(float(row[1]))
    else:
        # Если нет CSV-файла с подробной информацией, используем статистику из результатов
        response_times = []
        if 'test_data' in results and 'user_dialogs' in results['test_data']:
            for dialog in results['test_data']['user_dialogs']:
                if 'response_times' in dialog:
                    response_times.extend(dialog['response_times'])
    
    if not response_times:
        print("Нет данных о времени отклика для построения графика")
        return None
    
    # Создаём гистограмму
    ax.hist(response_times, bins=20, alpha=0.7, color='skyblue')
    ax.set_xlabel('Время отклика (мс)')
    ax.set_ylabel('Количество запросов')
    ax.set_title('Распределение времени отклика')
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Добавляем вертикальные линии для важных метрик
    percentiles = [
        ('Среднее', results['response_time_stats']['avg_ms'], 'r--'),
        ('Медиана (P50)', results['response_time_stats']['p50_ms'], 'g--'),
        ('P90', results['response_time_stats']['p90_ms'], 'b--'),
        ('P95', results['response_time_stats']['p95_ms'], 'm--'),
    ]
    
    for label, value, style in percentiles:
        ax.axvline(x=value, linestyle=style[1], color=style[0], label=f'{label}: {value:.2f} мс')
    
    ax.legend()
    
    # Сохраняем график
    output_path = os.path.join(output_dir, 'response_time_distribution.png')
    plt.savefig(output_path)
    plt.close()
    return output_path

def create_success_rate_chart(results, output_dir):
    """Создаёт круговую диаграмму успешных/неуспешных запросов"""
    fig, ax = plt.figure(figsize=(8, 8)), plt.axes()
    
    # Данные для диаграммы
    labels = ['Успешные запросы', 'Ошибки']
    sizes = [results['successful_requests'], results['failed_requests']]
    colors = ['#4CAF50', '#F44336']
    explode = (0.1, 0)  # Выделяем первый сегмент
    
    # Создаём круговую диаграмму
    ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
           shadow=True, startangle=90)
    ax.axis('equal')  # Круг вместо эллипса
    ax.set_title('Процент успешных запросов')
    
    # Сохраняем график
    output_path = os.path.join(output_dir, 'success_rate.png')
    plt.savefig(output_path)
    plt.close()
    return output_path

def create_percentile_comparison(results, output_dir):
    """Создаёт столбчатую диаграмму с перцентилями времени отклика"""
    fig, ax = plt.figure(figsize=(10, 6)), plt.axes()
    
    # Данные для диаграммы
    metrics = ['Минимум', 'Среднее', 'Медиана (P50)', 'P90', 'P95', 'P99', 'Максимум']
    values = [
        results['response_time_stats']['min_ms'],
        results['response_time_stats']['avg_ms'],
        results['response_time_stats']['p50_ms'],
        results['response_time_stats']['p90_ms'],
        results['response_time_stats']['p95_ms'],
        results['response_time_stats']['p99_ms'],
        results['response_time_stats']['max_ms']
    ]
    
    # Создаём столбчатую диаграмму
    bars = ax.bar(metrics, values, color='#2196F3')
    ax.set_ylabel('Время отклика (мс)')
    ax.set_title('Перцентили времени отклика')
    ax.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    # Добавляем значения над столбцами
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{height:.1f}', ha='center', va='bottom')
    
    # Поворачиваем подписи на оси X для лучшей читаемости
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Сохраняем график
    output_path = os.path.join(output_dir, 'percentile_comparison.png')
    plt.savefig(output_path)
    plt.close()
    return output_path

def create_time_series(results, results_file, output_dir):
    """Создаёт график изменения времени отклика по запросам"""
    # Проверяем наличие детальных данных
    csv_file = os.path.join(os.path.dirname(results_file), "response_times.csv")
    if not os.path.exists(csv_file):
        print("Файл с детальными данными не найден, график времени не создан")
        return None
    
    fig, ax = plt.figure(figsize=(12, 6)), plt.axes()
    
    # Загружаем данные
    import csv
    request_numbers = []
    response_times = []
    with open(csv_file, 'r', newline='') as f:
        reader = csv.reader(f)
        next(reader)  # Пропускаем заголовок
        for row in reader:
            request_numbers.append(int(row[0]))
            response_times.append(float(row[1]))
    
    # Строим график
    ax.plot(request_numbers, response_times, 'b-', alpha=0.7)
    ax.set_xlabel('Номер запроса')
    ax.set_ylabel('Время отклика (мс)')
    ax.set_title('Изменение времени отклика')
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Добавляем скользящее среднее
    window_size = min(10, len(response_times))
    if window_size > 1:
        moving_avg = np.convolve(response_times, np.ones(window_size)/window_size, mode='valid')
        ax.plot(request_numbers[window_size-1:], moving_avg, 'r-', 
                label=f'Скользящее среднее (окно {window_size})')
        ax.legend()
    
    # Сохраняем график
    output_path = os.path.join(output_dir, 'response_time_series.png')
    plt.savefig(output_path)
    plt.close()
    return output_path

def create_html_report(results_file, output_files, output_dir):
    """Создаёт HTML-отчёт с графиками и основной информацией"""
    results = load_results(results_file)
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Отчёт по результатам нагрузочного тестирования</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background-color: #2196F3; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .metric-card {{ background-color: #f5f5f5; border-radius: 5px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .metrics {{ display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 30px; }}
        .metric {{ flex: 1; min-width: 200px; background-color: #fff; border-left: 4px solid #2196F3; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .metric h3 {{ margin-top: 0; color: #666; }}
        .metric p {{ font-size: 24px; font-weight: bold; margin: 5px 0; }}
        .charts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(500px, 1fr)); gap: 20px; }}
        .chart {{ background-color: white; border-radius: 5px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .chart img {{ max-width: 100%; height: auto; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
        tr:hover {{ background-color: #f5f5f5; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Отчёт по результатам нагрузочного тестирования</h1>
            <p>Тест: {results['test_name']}</p>
            <p>Дата: {results['timestamp']}</p>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <h3>Всего запросов</h3>
                <p>{results['total_requests']}</p>
            </div>
            <div class="metric">
                <h3>Успешных запросов</h3>
                <p>{results['successful_requests']}</p>
            </div>
            <div class="metric">
                <h3>Ошибок</h3>
                <p>{results['failed_requests']}</p>
            </div>
            <div class="metric">
                <h3>Длительность теста</h3>
                <p>{results['duration_seconds']:.2f} сек</p>
            </div>
        </div>
        
        <div class="metric-card">
            <h2>Статистика времени отклика</h2>
            <table>
                <tr>
                    <th>Метрика</th>
                    <th>Значение (мс)</th>
                </tr>
                <tr>
                    <td>Минимальное время</td>
                    <td>{results['response_time_stats']['min_ms']:.2f}</td>
                </tr>
                <tr>
                    <td>Среднее время</td>
                    <td>{results['response_time_stats']['avg_ms']:.2f}</td>
                </tr>
                <tr>
                    <td>Медианное время (P50)</td>
                    <td>{results['response_time_stats']['p50_ms']:.2f}</td>
                </tr>
                <tr>
                    <td>90-й перцентиль (P90)</td>
                    <td>{results['response_time_stats']['p90_ms']:.2f}</td>
                </tr>
                <tr>
                    <td>95-й перцентиль (P95)</td>
                    <td>{results['response_time_stats']['p95_ms']:.2f}</td>
                </tr>
                <tr>
                    <td>99-й перцентиль (P99)</td>
                    <td>{results['response_time_stats']['p99_ms']:.2f}</td>
                </tr>
                <tr>
                    <td>Максимальное время</td>
                    <td>{results['response_time_stats']['max_ms']:.2f}</td>
                </tr>
            </table>
        </div>
        
        <div class="charts">
"""
    
    # Добавляем графики в отчёт
    for name, path in output_files.items():
        if path:
            # Получаем относительный путь для HTML
            rel_path = os.path.relpath(path, output_dir)
            html_content += f"""
            <div class="chart">
                <h3>{name}</h3>
                <img src="{rel_path}" alt="{name}">
            </div>"""
    
    html_content += """
        </div>
    </div>
</body>
</html>"""
    
    # Сохраняем HTML-отчёт
    html_path = os.path.join(output_dir, 'report.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return html_path

def find_latest_results(test_type=None):
    """Находит самые свежие результаты тестов указанного типа"""
    results_dir = os.path.join(TEST_DIR, "result_tests")
    if not os.path.exists(results_dir):
        print(f"Директория с результатами не найдена: {results_dir}")
        return None
    
    # Список директорий с результатами
    result_dirs = [d for d in os.listdir(results_dir) 
                  if os.path.isdir(os.path.join(results_dir, d)) and d != '.gitignore']
    
    if test_type:
        result_dirs = [d for d in result_dirs if d.startswith(test_type)]
    
    if not result_dirs:
        print(f"Результаты тестов не найдены{' для типа ' + test_type if test_type else ''}")
        return None
    
    # Сортируем по дате в имени (формат: test_name_YYYYMMDD_HHMMSS)
    result_dirs.sort(reverse=True)
    latest_dir = os.path.join(results_dir, result_dirs[0])
    
    results_file = os.path.join(latest_dir, "results.json")
    if not os.path.exists(results_file):
        print(f"Файл с результатами не найден: {results_file}")
        return None
    
    return results_file

def main():
    parser = argparse.ArgumentParser(description="Визуализация результатов нагрузочных тестов")
    parser.add_argument('--results', type=str, help="Путь к JSON-файлу с результатами теста")
    parser.add_argument('--type', type=str, choices=['concurrent_dialogs', 'response_time', 'long_dialogs'],
                       help="Тип теста для визуализации (если не указан файл)")
    args = parser.parse_args()
    
    # Определяем путь к файлу с результатами
    if args.results:
        results_file = args.results
    else:
        results_file = find_latest_results(args.type)
    
    if not results_file:
        print("Не удалось найти файл с результатами тестов")
        return 1
    
    print(f"Визуализация результатов из файла: {results_file}")
    
    # Загружаем результаты
    results = load_results(results_file)
    output_dir = os.path.dirname(results_file)
    
    # Создаём директорию для графиков
    charts_dir = os.path.join(output_dir, "charts")
    os.makedirs(charts_dir, exist_ok=True)
    
    # Создаём графики
    output_files = {}
    output_files["Распределение времени отклика"] = create_response_time_distribution(results, results_file, charts_dir)
    output_files["Успешные запросы"] = create_success_rate_chart(results, charts_dir)
    output_files["Перцентили времени отклика"] = create_percentile_comparison(results, charts_dir)
    output_files["Изменение времени отклика"] = create_time_series(results, results_file, charts_dir)
    
    # Создаём HTML-отчёт
    html_path = create_html_report(results_file, output_files, output_dir)
    
    print(f"HTML-отчёт создан: {html_path}")
    print("Графики сохранены в директории:", charts_dir)
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
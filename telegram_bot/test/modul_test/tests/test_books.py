import unittest
import os
import json
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Добавляем корневую директорию проекта в sys.path для импорта модулей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from telegram_bot.ai_service.ai_books import (
    get_book_recommendations,
    create_recommendation_prompt,
    format_recommendations,
    get_book_recommendations_from_file
)

class TestBooks(unittest.TestCase):
    """Тесты для модуля ai_books.py"""
    
    def setUp(self):
        """Подготовка тестового окружения перед каждым тестом"""
        # Создаем временную директорию для тестовых файлов
        self.test_dir = tempfile.mkdtemp()
        
        # Переопределяем путь к базе данных для тестов
        import telegram_bot.ai_service.database as database_module
        self.original_db_path = database_module.DATABASE_PATH
        database_module.DATABASE_PATH = os.path.join(self.test_dir, 'test_dialogues.db')
        
        # Инициализируем тестовую базу данных
        database_module.init_db()
        
        # Создаем тестовый диалог в формате JSON
        self.test_dialogue_path = os.path.join(self.test_dir, 'test_dialogue.json')
        test_dialogue = [
            {"role": "system", "content": "Ты психолог-консультант"},
            {"role": "user", "content": "Я чувствую себя подавленным"},
            {"role": "assistant", "content": "Расскажите подробнее о своих чувствах"},
            {"role": "user", "content": "Мне сложно находить мотивацию для работы"}
        ]
        with open(self.test_dialogue_path, 'w', encoding='utf-8') as f:
            json.dump(test_dialogue, f)
        
        # Создаем тестовый config.json
        self.config_path = 'telegram_bot/ai_service/config.json'
        self.original_config_path = self.config_path
        
        if not os.path.exists(self.config_path):
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            test_config = {
                "openrouter_api_key": "test_api_key"
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(test_config, f)
        
        # Тестовые рекомендации книг
        self.test_recommendations = {
            "books": [
                {
                    "title": "Чувство собственного достоинства",
                    "author": "Натаниэль Бранден",
                    "description": "Книга о психологии самооценки и её влиянии на все аспекты жизни",
                    "why_relevant": "Поможет справиться с низкой самооценкой при депрессии"
                },
                {
                    "title": "Когнитивно-поведенческая терапия для чайников",
                    "author": "Рона Бранч",
                    "description": "Доступное введение в методы КПТ",
                    "why_relevant": "Предлагает практические инструменты для борьбы с негативными мыслями"
                }
            ],
            "resources": [
                {
                    "title": "Приложение Moodpath",
                    "type": "Мобильное приложение",
                    "description": "Приложение для отслеживания настроения и симптомов депрессии",
                    "link": "https://mymoodpath.com/"
                },
                {
                    "title": "Сайт Психологи.рф",
                    "type": "Онлайн-ресурс",
                    "description": "Платформа для поиска профессиональных психологов",
                    "link": "https://психологи.рф"
                }
            ]
        }
    
    def tearDown(self):
        """Очистка после каждого теста"""
        # Возвращаем оригинальный путь к базе данных
        import telegram_bot.ai_service.database as database_module
        database_module.DATABASE_PATH = self.original_db_path
        
        # Удаляем временную директорию
        shutil.rmtree(self.test_dir)
    
    def test_create_recommendation_prompt(self):
        """Тест создания промпта для рекомендаций"""
        # Подготавливаем тестовые данные
        issue_id = '1'  # Депрессия
        dialogue = [
            {"role": "system", "content": "Ты психолог-консультант"},
            {"role": "user", "content": "Я чувствую себя подавленным"},
            {"role": "assistant", "content": "Расскажите подробнее о своих чувствах"},
            {"role": "user", "content": "Мне сложно находить мотивацию для работы"}
        ]
        
        # Вызываем функцию создания промпта
        prompt = create_recommendation_prompt(issue_id, dialogue)
        
        # Проверяем, что промпт содержит нужную информацию
        self.assertIn("депрессия", prompt)
        self.assertIn("Я чувствую себя подавленным", prompt)
        self.assertIn("Мне сложно находить мотивацию для работы", prompt)
        self.assertIn("JSON формате", prompt)
    
    def test_format_recommendations(self):
        """Тест форматирования рекомендаций в читаемый текст"""
        # Вызываем функцию форматирования
        formatted_text = format_recommendations(self.test_recommendations)
        
        # Проверяем, что текст содержит нужную информацию
        self.assertIn("📚 Рекомендуемые книги:", formatted_text)
        self.assertIn("• Чувство собственного достоинства - Натаниэль Бранден", formatted_text)
        self.assertIn("Книга о психологии самооценки", formatted_text)
        self.assertIn("Поможет справиться с низкой самооценкой", formatted_text)
        
        self.assertIn("🌐 Полезные ресурсы:", formatted_text)
        self.assertIn("• Приложение Moodpath (Мобильное приложение)", formatted_text)
        self.assertIn("• Сайт Психологи.рф (Онлайн-ресурс)", formatted_text)
        self.assertIn("Ссылка: https://mymoodpath.com/", formatted_text)
    
    @patch('telegram_bot.ai_service.ai_books.OpenAI')
    def test_get_book_recommendations(self, mock_openai):
        """Тест получения рекомендаций книг"""
        # Мокаем ответ от OpenAI
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_completion = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = json.dumps(self.test_recommendations)
        
        # Подготавливаем тестовые данные
        dialogue_id = 1
        user_id = 'test_user'
        issue_id = '1'
        dialogue = [
            {"role": "system", "content": "Ты психолог-консультант"},
            {"role": "user", "content": "Я чувствую себя подавленным"}
        ]
        
        # Вызываем функцию получения рекомендаций
        recommendations = get_book_recommendations(dialogue_id, user_id, issue_id, dialogue)
        
        # Проверяем, что OpenAI был вызван
        mock_client.chat.completions.create.assert_called_once()
        
        # Проверяем возвращаемое значение
        self.assertEqual(recommendations, self.test_recommendations)
        self.assertEqual(len(recommendations['books']), 2)
        self.assertEqual(recommendations['books'][0]['title'], "Чувство собственного достоинства")
        
        # Проверяем, что рекомендации были сохранены в базу данных
        import telegram_bot.ai_service.database as db
        user_recommendations = db.get_user_recommendations(user_id)
        self.assertGreater(len(user_recommendations), 0)
        
        # Находим последнюю рекомендацию
        latest_recommendation = max(user_recommendations, key=lambda r: r['id'])
        
        # Проверяем, что рекомендация содержит правильные данные
        self.assertEqual(latest_recommendation['user_id'], user_id)
        self.assertEqual(latest_recommendation['issue_id'], issue_id)
        self.assertEqual(latest_recommendation['dialogue_id'], dialogue_id)
        self.assertEqual(latest_recommendation['recommendations_json']['books'][0]['title'], 
                         self.test_recommendations['books'][0]['title'])
    
    @patch('telegram_bot.ai_service.ai_books.get_book_recommendations')
    def test_get_book_recommendations_from_file(self, mock_get_recommendations):
        """Тест получения рекомендаций книг из файла"""
        # Подготавливаем мок
        mock_get_recommendations.return_value = self.test_recommendations
        
        # Вызываем функцию получения рекомендаций из файла
        formatted_recommendations = get_book_recommendations_from_file(
            self.test_dialogue_path, 1, 'test_user', '1'
        )
        
        # Проверяем, что get_book_recommendations был вызван с правильными аргументами
        mock_get_recommendations.assert_called_once()
        args = mock_get_recommendations.call_args[0]
        self.assertEqual(args[0], 1)  # dialogue_id
        self.assertEqual(args[1], 'test_user')  # user_id
        self.assertEqual(args[2], '1')  # issue_id
        
        # Проверяем, что результат отформатирован правильно
        self.assertIn("📚 Рекомендуемые книги:", formatted_recommendations)
        self.assertIn("🌐 Полезные ресурсы:", formatted_recommendations)
    
    @patch('telegram_bot.ai_service.ai_books.OpenAI')
    def test_get_book_recommendations_json_error(self, mock_openai):
        """Тест обработки ошибки при парсинге JSON в ответе API"""
        # Мокаем ответ от OpenAI с некорректным JSON
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_completion = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Это не JSON"
        
        # Вызываем функцию получения рекомендаций
        recommendations = get_book_recommendations(1, 'test_user', '1', [])
        
        # Проверяем, что возвращается пустой словарь с пустыми списками
        self.assertEqual(recommendations, {"books": [], "resources": []})


if __name__ == '__main__':
    unittest.main() 
import unittest
import os
import sqlite3
import json
from datetime import datetime
import sys
import tempfile
import shutil

# Добавляем корневую директорию проекта в sys.path для импорта модулей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from telegram_bot.ai_service.database import (
    get_db_connection,
    init_db,
    log_dialogue,
    log_book_recommendations,
    get_user_dialogues,
    get_user_recommendations,
    get_dialogue_by_id
)

class TestDatabase(unittest.TestCase):
    """Тесты для модуля database.py"""
    
    def setUp(self):
        """Подготовка тестового окружения перед каждым тестом"""
        # Создаем временную директорию для тестовой базы данных
        self.test_dir = tempfile.mkdtemp()
        
        # Переопределяем путь к базе данных для тестов
        import telegram_bot.ai_service.database as database_module
        self.original_db_path = database_module.DATABASE_PATH
        database_module.DATABASE_PATH = os.path.join(self.test_dir, 'test_dialogues.db')
        
        # Инициализируем тестовую базу данных
        init_db()
        
    def tearDown(self):
        """Очистка после каждого теста"""
        # Возвращаем оригинальный путь к базе данных
        import telegram_bot.ai_service.database as database_module
        database_module.DATABASE_PATH = self.original_db_path
        
        # Удаляем временную директорию
        shutil.rmtree(self.test_dir)
    
    def test_init_db(self):
        """Тест инициализации базы данных"""
        # Проверяем, что база данных создана
        import telegram_bot.ai_service.database as database_module
        self.assertTrue(os.path.exists(database_module.DATABASE_PATH))
        
        # Проверяем, что таблицы созданы
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Проверка таблицы dialogues
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dialogues'")
        self.assertIsNotNone(cursor.fetchone())
        
        # Проверка таблицы book_recommendations
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='book_recommendations'")
        self.assertIsNotNone(cursor.fetchone())
        
        conn.close()
    
    def test_log_dialogue(self):
        """Тест логирования диалога в базу данных"""
        user_id = 'test_user'
        issue_id = '1'
        dialogue = [
            {"role": "system", "content": "Системное сообщение"},
            {"role": "user", "content": "Тестовое сообщение пользователя"},
            {"role": "assistant", "content": "Тестовый ответ ассистента"}
        ]
        
        # Логируем диалог
        dialogue_id = log_dialogue(user_id, issue_id, dialogue)
        
        # Проверяем, что ID возвращен и > 0
        self.assertIsNotNone(dialogue_id)
        self.assertGreater(dialogue_id, 0)
        
        # Проверяем, что запись создана в базе
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dialogues WHERE id = ?", (dialogue_id,))
        record = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(record)
        self.assertEqual(record['user_id'], user_id)
        self.assertEqual(record['issue_id'], issue_id)
        
        # Проверяем, что JSON диалога сохранен корректно
        saved_dialogue = json.loads(record['dialogue_json'])
        self.assertEqual(len(saved_dialogue), len(dialogue))
        self.assertEqual(saved_dialogue[0]['content'], dialogue[0]['content'])
    
    def test_log_book_recommendations(self):
        """Тест логирования рекомендаций книг в базу данных"""
        user_id = 'test_user'
        issue_id = '1'
        dialogue = [{"role": "user", "content": "Тестовое сообщение"}]
        
        # Сначала логируем диалог
        dialogue_id = log_dialogue(user_id, issue_id, dialogue)
        
        # Создаем тестовые рекомендации
        recommendations = {
            "books": [
                {
                    "title": "Тестовая книга",
                    "author": "Тестовый автор",
                    "description": "Описание книги",
                    "why_relevant": "Объяснение релевантности"
                }
            ],
            "resources": [
                {
                    "title": "Тестовый ресурс",
                    "type": "Статья",
                    "description": "Описание ресурса",
                    "link": "https://test.com"
                }
            ]
        }
        
        # Логируем рекомендации
        recommendation_id = log_book_recommendations(user_id, issue_id, recommendations, dialogue_id)
        
        # Проверяем, что ID возвращен и > 0
        self.assertIsNotNone(recommendation_id)
        self.assertGreater(recommendation_id, 0)
        
        # Проверяем, что запись создана в базе
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM book_recommendations WHERE id = ?", (recommendation_id,))
        record = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(record)
        self.assertEqual(record['user_id'], user_id)
        self.assertEqual(record['issue_id'], issue_id)
        self.assertEqual(record['dialogue_id'], dialogue_id)
        
        # Проверяем, что JSON рекомендаций сохранен корректно
        saved_recommendations = json.loads(record['recommendations_json'])
        self.assertEqual(len(saved_recommendations['books']), len(recommendations['books']))
        self.assertEqual(saved_recommendations['books'][0]['title'], recommendations['books'][0]['title'])
    
    def test_get_user_dialogues(self):
        """Тест получения диалогов пользователя"""
        user_id = 'test_user'
        issue_id = '1'
        
        # Создаем несколько тестовых диалогов
        dialogue1 = [{"role": "user", "content": "Диалог 1"}]
        dialogue2 = [{"role": "user", "content": "Диалог 2"}]
        
        dialogue_id1 = log_dialogue(user_id, issue_id, dialogue1)
        dialogue_id2 = log_dialogue(user_id, issue_id, dialogue2)
        
        # Получаем диалоги пользователя
        user_dialogues = get_user_dialogues(user_id)
        
        # Проверяем, что получены все диалоги
        self.assertEqual(len(user_dialogues), 2)
        
        # Проверяем, что диалоги содержат ожидаемые данные
        dialogue_ids = [d['id'] for d in user_dialogues]
        self.assertIn(dialogue_id1, dialogue_ids)
        self.assertIn(dialogue_id2, dialogue_ids)
        
        # Проверяем, что содержимое диалогов соответствует сохраненным данным
        for dialogue in user_dialogues:
            if dialogue['id'] == dialogue_id1:
                self.assertEqual(dialogue['dialogue_json'][0]['content'], dialogue1[0]['content'])
            elif dialogue['id'] == dialogue_id2:
                self.assertEqual(dialogue['dialogue_json'][0]['content'], dialogue2[0]['content'])
    
    def test_get_user_recommendations(self):
        """Тест получения рекомендаций пользователя"""
        user_id = 'test_user'
        issue_id = '1'
        
        # Создаем тестовый диалог и рекомендации
        dialogue = [{"role": "user", "content": "Тестовое сообщение"}]
        dialogue_id = log_dialogue(user_id, issue_id, dialogue)
        
        recommendations1 = {
            "books": [{"title": "Книга 1", "author": "Автор 1", "description": "Описание", "why_relevant": "Причина"}]
        }
        recommendations2 = {
            "books": [{"title": "Книга 2", "author": "Автор 2", "description": "Описание", "why_relevant": "Причина"}]
        }
        
        rec_id1 = log_book_recommendations(user_id, issue_id, recommendations1, dialogue_id)
        rec_id2 = log_book_recommendations(user_id, issue_id, recommendations2, dialogue_id)
        
        # Получаем рекомендации пользователя
        user_recommendations = get_user_recommendations(user_id)
        
        # Проверяем, что получены все рекомендации
        self.assertEqual(len(user_recommendations), 2)
        
        # Проверяем, что рекомендации содержат ожидаемые данные
        rec_ids = [r['id'] for r in user_recommendations]
        self.assertIn(rec_id1, rec_ids)
        self.assertIn(rec_id2, rec_ids)
        
        # Проверяем, что содержимое рекомендаций соответствует сохраненным данным
        for rec in user_recommendations:
            if rec['id'] == rec_id1:
                self.assertEqual(rec['recommendations_json']['books'][0]['title'], recommendations1['books'][0]['title'])
            elif rec['id'] == rec_id2:
                self.assertEqual(rec['recommendations_json']['books'][0]['title'], recommendations2['books'][0]['title'])
    
    def test_get_dialogue_by_id(self):
        """Тест получения диалога по ID"""
        user_id = 'test_user'
        issue_id = '1'
        dialogue = [
            {"role": "system", "content": "Системное сообщение"},
            {"role": "user", "content": "Сообщение пользователя"}
        ]
        
        # Логируем диалог
        dialogue_id = log_dialogue(user_id, issue_id, dialogue)
        
        # Получаем диалог по ID
        retrieved_dialogue = get_dialogue_by_id(dialogue_id)
        
        # Проверяем, что диалог получен
        self.assertIsNotNone(retrieved_dialogue)
        self.assertEqual(retrieved_dialogue['id'], dialogue_id)
        self.assertEqual(retrieved_dialogue['user_id'], user_id)
        self.assertEqual(retrieved_dialogue['issue_id'], issue_id)
        
        # Проверяем содержимое диалога
        self.assertEqual(len(retrieved_dialogue['dialogue_json']), len(dialogue))
        self.assertEqual(retrieved_dialogue['dialogue_json'][0]['content'], dialogue[0]['content'])
        self.assertEqual(retrieved_dialogue['dialogue_json'][1]['content'], dialogue[1]['content'])
    
    def test_get_nonexistent_dialogue(self):
        """Тест получения несуществующего диалога"""
        # Пытаемся получить диалог с несуществующим ID
        nonexistent_dialogue = get_dialogue_by_id(9999)
        
        # Проверяем, что возвращается None
        self.assertIsNone(nonexistent_dialogue)


if __name__ == '__main__':
    unittest.main() 
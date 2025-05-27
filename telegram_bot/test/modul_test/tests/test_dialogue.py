import unittest
import os
import json
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Добавляем корневую директорию проекта в sys.path для импорта модулей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from telegram_bot.ai_service.ai_main import (
    initialize_dialogue,
    get_llm_response,
    read_messages,
    chat
)

class TestDialogue(unittest.TestCase):
    """Тесты для модуля ai_main.py"""
    
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
            {"role": "user", "content": "Я чувствую себя подавленным"}
        ]
        with open(self.test_dialogue_path, 'w', encoding='utf-8') as f:
            json.dump(test_dialogue, f)
        
        # Создаем тестовый файл system_prompts.json
        self.system_prompts_path = 'telegram_bot/ai_service/system_prompts.json'
        self.original_prompts_path = self.system_prompts_path
        
        if not os.path.exists(self.system_prompts_path):
            os.makedirs(os.path.dirname(self.system_prompts_path), exist_ok=True)
            test_prompts = {
                "1": {
                    "system_prompt": "Ты психолог, специализирующийся на депрессии",
                    "initial_message": "Здравствуйте! Я здесь, чтобы помочь вам с депрессией."
                },
                "2": {
                    "system_prompt": "Ты психолог, специализирующийся на выгорании",
                    "initial_message": "Здравствуйте! Я здесь, чтобы помочь вам с выгоранием."
                },
                "3": {
                    "system_prompt": "Ты психолог, специализирующийся на отношениях",
                    "initial_message": "Здравствуйте! Я здесь, чтобы помочь вам с проблемами в отношениях."
                }
            }
            with open(self.system_prompts_path, 'w', encoding='utf-8') as f:
                json.dump(test_prompts, f)
        
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
    
    def tearDown(self):
        """Очистка после каждого теста"""
        # Возвращаем оригинальный путь к базе данных
        import telegram_bot.ai_service.database as database_module
        database_module.DATABASE_PATH = self.original_db_path
        
        # Удаляем временную директорию
        shutil.rmtree(self.test_dir)
    
    def test_initialize_dialogue(self):
        """Тест инициализации диалога"""
        # Тест без использования моков, так как функция log_dialogue вызывается внутри initialize_dialogue
        
        # Вызываем функцию инициализации диалога
        user_id = 'test_user'
        issue_id = '1'  # Депрессия
        dialogue_id = initialize_dialogue(issue_id, user_id)
        
        # Проверяем, что ID диалога возвращен и > 0
        self.assertIsNotNone(dialogue_id)
        self.assertGreater(dialogue_id, 0)
        
        # Проверяем, что диалог записан в базу данных
        import telegram_bot.ai_service.database as db
        dialogue = db.get_dialogue_by_id(dialogue_id)
        
        # Проверяем, что диалог содержит правильные данные
        self.assertEqual(dialogue['user_id'], user_id)
        self.assertEqual(dialogue['issue_id'], issue_id)
        
        # Проверяем структуру диалога
        self.assertEqual(len(dialogue['dialogue_json']), 2)  # Системное сообщение и начальное сообщение ассистента
        self.assertEqual(dialogue['dialogue_json'][0]['role'], 'system')
        self.assertEqual(dialogue['dialogue_json'][1]['role'], 'assistant')
    
    @patch('telegram_bot.ai_service.ai_main.OpenAI')
    def test_get_llm_response(self, mock_openai):
        """Тест получения ответа от LLM"""
        # Мокаем ответ от OpenAI
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_completion = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Я понимаю ваши чувства. Расскажите подробнее."
        
        # Подготавливаем тестовые данные
        messages = [
            {"role": "system", "content": "Ты психолог-консультант"},
            {"role": "user", "content": "Я чувствую себя подавленным"}
        ]
        user_id = 'test_user'
        issue_id = '1'
        
        # Вызываем функцию получения ответа
        response = get_llm_response(messages, user_id, issue_id)
        
        # Проверяем, что OpenAI был вызван с правильными аргументами
        mock_client.chat.completions.create.assert_called_once()
        _, kwargs = mock_client.chat.completions.create.call_args
        self.assertEqual(kwargs['messages'], messages)
        
        # Проверяем, что ответ соответствует ожидаемому
        self.assertEqual(response, "Я понимаю ваши чувства. Расскажите подробнее.")
        
        # Проверяем, что диалог был сохранен в базу данных
        import telegram_bot.ai_service.database as db
        dialogues = db.get_user_dialogues(user_id)
        self.assertGreater(len(dialogues), 0)
        
        # Находим последний диалог
        latest_dialogue = max(dialogues, key=lambda d: d['id'])
        
        # Проверяем, что последнее сообщение в диалоге - это ответ ассистента
        dialogue_messages = latest_dialogue['dialogue_json']
        self.assertEqual(dialogue_messages[-1]['role'], 'assistant')
        self.assertEqual(dialogue_messages[-1]['content'], "Я понимаю ваши чувства. Расскажите подробнее.")
    
    def test_read_messages(self):
        """Тест чтения сообщений из файла"""
        # Вызываем функцию чтения сообщений
        messages = read_messages(self.test_dialogue_path)
        
        # Проверяем, что сообщения загружены корректно
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]['role'], 'system')
        self.assertEqual(messages[0]['content'], 'Ты психолог-консультант')
        self.assertEqual(messages[1]['role'], 'user')
        self.assertEqual(messages[1]['content'], 'Я чувствую себя подавленным')
    
    @patch('telegram_bot.ai_service.ai_main.get_llm_response')
    def test_chat(self, mock_get_llm_response):
        """Тест основной функции чата"""
        # Подготавливаем мок для get_llm_response
        mock_get_llm_response.return_value = "Я понимаю ваши чувства. Расскажите подробнее."
        
        # Вызываем функцию чата
        user_id = 'test_user'
        issue_id = '1'
        response = chat(issue_id, user_id, self.test_dialogue_path)
        
        # Проверяем, что get_llm_response был вызван с правильными аргументами
        mock_get_llm_response.assert_called_once()
        args = mock_get_llm_response.call_args[0]
        
        # Проверяем аргументы вызова
        self.assertEqual(len(args[0]), 2)  # messages
        self.assertEqual(args[1], user_id)
        self.assertEqual(args[2], issue_id)
        
        # Проверяем возвращаемое значение
        self.assertEqual(response, "Я понимаю ваши чувства. Расскажите подробнее.")
    
    def test_initialize_dialogue_invalid_issue_id(self):
        """Тест инициализации диалога с недопустимым issue_id"""
        # Проверяем, что исключение правильно вызывается
        with self.assertRaises(ValueError) as context:
            initialize_dialogue('5', 'test_user')
        
        # Проверяем сообщение исключения
        self.assertIn("Invalid issue_id: 5", str(context.exception))


if __name__ == '__main__':
    unittest.main() 
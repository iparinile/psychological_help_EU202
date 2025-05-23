from openai import OpenAI
import json
from typing import List, Dict
import os
import logging
from .database import log_dialogue, log_book_recommendations
from .ai_books import get_book_recommendations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def initialize_dialogue(issue_id: str, user_id: str, output_path: str = 'ai_service/demo_dialogue.json') -> int:
    """
    Initialize dialogue with system prompt based on selected issue.
    
    Args:
        issue_id (str): ID of the psychological issue (1 - depression, 2 - burnout, 3 - relationship problems)
        user_id (str): Unique identifier for the user
        output_path (str): Path where to save the initial dialogue
        
    Returns:
        int: ID of the created dialogue in the database
    """
    logging.info(f"Initializing dialogue for user {user_id} with issue {issue_id}")
    
    # Load system prompts
    with open('ai_service/system_prompts.json', 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    
    if issue_id not in prompts:
        logging.error(f"Invalid issue_id: {issue_id}")
        raise ValueError(f"Invalid issue_id: {issue_id}. Must be one of: 1, 2, 3")
    
    # Create initial dialogue with system prompt and first message
    initial_dialogue = [
        {
            "role": "system",
            "content": prompts[issue_id]["system_prompt"]
        },
        {
            "role": "assistant",
            "content": prompts[issue_id]["initial_message"]
        }
    ]
    logging.info("Created initial dialogue with system prompt")
    
    # Log the initial dialogue and return its ID
    dialogue_id = log_dialogue(user_id, issue_id, initial_dialogue)
    logging.info(f"Initial dialogue logged with ID: {dialogue_id}")
    return dialogue_id

def get_llm_response(messages: List[Dict[str, str]], user_id: str, issue_id: str) -> str:
    """
    Get response from LLM based on dialogue history.
    
    Args:
        messages (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content' keys
        user_id (str): Unique identifier for the user
        issue_id (str): ID of the psychological issue
        
    Returns:
        str: LLM's response text
    """
    logging.info(f"Getting LLM response for user {user_id}, issue {issue_id}")
    
    # Load config
    with open('ai_service/config.json', 'r') as f:
        config = json.load(f)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=config['openrouter_api_key'],
    )
    
    logging.info("Sending request to LLM")
    
    try:
        completion = client.chat.completions.create(
            model="google/gemma-3-4b-it:free",
            messages=messages,
            max_tokens=4000,
            temperature=0.7
        )
        response = completion.choices[0].message.content
        logging.info(f"Received response: '{response[:50]}...' (length: {len(response) if response else 0})")
        
    except Exception as api_error:
        logging.error(f"Error getting LLM response: {api_error}")
        response = "Извините, произошла техническая ошибка. Попробуйте повторить запрос позже."
    
    # Log the updated dialogue with the new response
    updated_messages = messages + [{"role": "assistant", "content": response}]
    dialogue_id = log_dialogue(user_id, issue_id, updated_messages)
    logging.info(f"Updated dialogue logged with ID: {dialogue_id}")
    
    # Get and log book recommendations
    # Можно добавить рекомендации книг, но пока оставим без них для простоты
    # recommendations = get_book_recommendations(dialogue_id, user_id, issue_id, updated_messages)
    # от ai_books import log_book_recommendations уже импортирован в database
    
    return response

def read_messages(path: str) -> List[Dict[str, str]]:
    """
    Read messages from a file
    
    Args:
        path (str): Path to the message file
        
    Returns:
        List[Dict[str, str]]: List of message dictionaries
    """
    logging.info(f"Reading messages from {path}")
    with open(path, 'r', encoding='utf-8') as f:
        messages = json.load(f)
    logging.info(f"Successfully read {len(messages)} messages")
    return messages

def chat(issue_id: str, user_id: str, input_path: str = 'ai_service/demo_dialogue.json') -> str:
    """
    Main chat function that handles the conversation flow.
    
    Args:
        issue_id (str): ID of the psychological issue
        user_id (str): Unique identifier for the user
        input_path (str): Path to the dialogue file
        
    Returns:
        str: Response from the LLM
    """
    logging.info(f"Starting chat session for user {user_id} with issue {issue_id}")
    messages = read_messages(input_path)
    response = get_llm_response(messages, user_id, issue_id)
    logging.info("Chat session completed")
    return response

if __name__ == "__main__":
    # Example usage with a demo user
    logging.info("Starting demo chat session")
    chat('1', 'demo_user', 'ai_service/demo_dialogue.json')
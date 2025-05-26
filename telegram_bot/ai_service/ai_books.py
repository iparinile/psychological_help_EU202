from openai import OpenAI
import json
from typing import List, Dict, Optional
import os
import logging
from .database import log_book_recommendations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_book_recommendations(dialogue_id: int, user_id: str, issue_id: str, dialogue: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    """
    Get personalized book and resource recommendations based on the user's issue and dialogue.
    
    Args:
        dialogue_id (int): ID of the dialogue to associate recommendations with
        user_id (str): Unique identifier for the user
        issue_id (str): ID of the psychological issue (1 - depression, 2 - burnout, 3 - relationship problems)
        dialogue (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content' keys
        
    Returns:
        Dict[str, List[Dict[str, str]]]: Dictionary containing recommended books and resources
    """
    logging.info(f"Getting book recommendations for user {user_id}, issue {issue_id}, dialogue {dialogue_id}")
    
    # Load config
    with open('telegram_bot/ai_service/config.json', 'r') as f:
        config = json.load(f)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=config['openrouter_api_key'],
    )

    # Create recommendation prompt
    recommendation_prompt = create_recommendation_prompt(issue_id, dialogue)
    logging.info("Created recommendation prompt")
    
    messages = [
        {
            "role": "system",
            "content": """Ты - эксперт по психологической литературе и ресурсам. 
            Твоя задача - рекомендовать книги и ресурсы, которые могут помочь человеку с его конкретной проблемой.
            Рекомендации должны быть:
            1. Релевантными проблеме
            2. Научно обоснованными
            3. Практичными и доступными
            4. Разнообразными (книги, статьи, онлайн-ресурсы)
            
            Формат ответа должен быть в JSON:
            {
                "books": [
                    {
                        "title": "Название книги",
                        "author": "Автор",
                        "description": "Краткое описание",
                        "why_relevant": "Почему эта книга подходит"
                    }
                ],
                "resources": [
                    {
                        "title": "Название ресурса",
                        "type": "Тип (статья/сайт/приложение)",
                        "description": "Описание",
                        "link": "Ссылка (если есть)"
                    }
                ]
            }"""
        },
        {
            "role": "user",
            "content": recommendation_prompt
        }
    ]

    logging.info("Sending request to LLM for book recommendations")
    completion = client.chat.completions.create(
        model="google/gemma-3-4b-it:free",
        messages=messages
    )
    response = completion.choices[0].message.content
    logging.info("Received response from LLM")
    
    try:
        recommendations = json.loads(response.replace("```json", "").replace("```", ""))
        logging.info("Successfully parsed recommendations JSON")
        
        # Log the recommendations to the database
        recommendation_id = log_book_recommendations(user_id, issue_id, recommendations, dialogue_id)
        logging.info(f"Book recommendations logged with ID: {recommendation_id}")
        
        return recommendations
    except json.JSONDecodeError:
        logging.error("Failed to parse recommendations JSON")
        return {"books": [], "resources": []}

def create_recommendation_prompt(issue_id: str, dialogue: List[Dict[str, str]]) -> str:
    """
    Create a prompt for book recommendations based on the issue and dialogue.
    
    Args:
        issue_id (str): ID of the psychological issue
        dialogue (List[Dict[str, str]]): List of message dictionaries
        
    Returns:
        str: Formatted prompt for recommendations
    """
    logging.info(f"Creating recommendation prompt for issue {issue_id}")
    
    issue_types = {
        "1": "депрессия",
        "2": "профессиональное выгорание",
        "3": "проблемы в отношениях"
    }
    
    # Extract relevant information from dialogue
    user_messages = [msg["content"] for msg in dialogue if msg["role"] == "user"]
    context = " ".join(user_messages[-3:])  # Use last 3 user messages for context
    
    prompt = f"""На основе диалога с пользователем, который испытывает проблемы с {issue_types.get(issue_id, "психологическим состоянием")}, 
    порекомендуй подходящие книги и ресурсы. 
    
    Контекст из диалога:
    {context}
    
    Пожалуйста, предоставь рекомендации в указанном JSON формате."""
    
    logging.info("Recommendation prompt created")
    return prompt

def format_recommendations(recommendations: Dict[str, List[Dict[str, str]]]) -> str:
    """
    Format recommendations into a readable string.
    
    Args:
        recommendations (Dict[str, List[Dict[str, str]]]): Dictionary of recommendations
        
    Returns:
        str: Formatted recommendations text
    """
    logging.info("Formatting recommendations")
    
    formatted_text = "📚 Рекомендуемые книги:\n\n"
    
    for book in recommendations.get("books", []):
        formatted_text += f"• {book['title']} - {book['author']}\n"
        formatted_text += f"  {book['description']}\n"
        formatted_text += f"  Почему подходит: {book['why_relevant']}\n\n"
    
    formatted_text += "🌐 Полезные ресурсы:\n\n"
    
    for resource in recommendations.get("resources", []):
        formatted_text += f"• {resource['title']} ({resource['type']})\n"
        formatted_text += f"  {resource['description']}\n"
        if resource.get('link'):
            formatted_text += f"  Ссылка: {resource['link']}\n"
        formatted_text += "\n"
    
    logging.info("Recommendations formatted successfully")
    return formatted_text

def get_book_recommendations_from_file(file_path: str, dialogue_id: int, user_id: str, issue_id: str) -> str:
    """
    Get book recommendations from a dialogue file.
    
    Args:
        file_path (str): Path to the dialogue file
        dialogue_id (int): ID of the dialogue to associate recommendations with
        user_id (str): Unique identifier for the user
        issue_id (str): ID of the psychological issue
        
    Returns:
        str: Formatted recommendations text
    """
    logging.info(f"Getting book recommendations from file {file_path}")
    
    with open(file_path, 'r') as f:
        file_content = json.load(f)
    dialogue = file_content[1:]
    logging.info(f"Read dialogue from file with {len(dialogue)} messages")
    
    recommendations = get_book_recommendations(dialogue_id, user_id, issue_id, dialogue)
    formatted_recommendations = format_recommendations(recommendations)
    logging.info("Book recommendations processed successfully")
    return formatted_recommendations

if __name__ == "__main__":
    # Example usage
    logging.info("Starting demo book recommendations")
    print(get_book_recommendations_from_file('telegram_bot/ai_service/demo_dialogue.json', 1, 'demo_user', '1'))


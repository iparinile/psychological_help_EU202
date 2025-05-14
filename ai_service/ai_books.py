from openai import OpenAI
import json
from typing import List, Dict, Optional
import os
import logging

def get_book_recommendations(issue_id: str, dialogue: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    """
    Get personalized book and resource recommendations based on the user's issue and dialogue.
    
    Args:
        issue_id (str): ID of the psychological issue (1 - depression, 2 - burnout, 3 - relationship problems)
        dialogue (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content' keys
        
    Returns:
        Dict[str, List[Dict[str, str]]]: Dictionary containing recommended books and resources
    """
    # Load config
    with open('ai_service/config.json', 'r') as f:
        config = json.load(f)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=config['openrouter_api_key'],
    )

    # Create recommendation prompt
    recommendation_prompt = create_recommendation_prompt(issue_id, dialogue)
    
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

    completion = client.chat.completions.create(
        model="google/gemma-3-4b-it:free",
        messages=messages
    )
    response = completion.choices[0].message.content
    try:
        recommendations = json.loads(response.replace("```json", "").replace("```", ""))
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
    
    return prompt

def format_recommendations(recommendations: Dict[str, List[Dict[str, str]]]) -> str:
    """
    Format recommendations into a readable string.
    
    Args:
        recommendations (Dict[str, List[Dict[str, str]]]): Dictionary of recommendations
        
    Returns:
        str: Formatted recommendations text
    """
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
    
    return formatted_text

def get_book_recommendations_from_file(file_path: str, issue_id: str) -> Dict[str, List[Dict[str, str]]]:
    with open(file_path, 'r') as f:
        file_content = json.load(f)
    dialogue = file_content[1:]
    recommendations = get_book_recommendations(issue_id, dialogue)
    print(recommendations)
    formatted_recommendations = format_recommendations(recommendations)
    return formatted_recommendations

if __name__ == "__main__":
    print(get_book_recommendations_from_file('ai_service/demo_dialogue.json', '1'))


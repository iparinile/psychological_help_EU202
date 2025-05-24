"""
AI Service package for psychological support chatbot.
Contains modules for dialogue handling, book recommendations, and database operations.
"""

from .database import (
    init_db,
    get_db_connection,
    log_dialogue,
    log_book_recommendations,
    get_user_dialogues,
    get_user_recommendations,
    get_dialogue_by_id
)

from .ai_main import (
    initialize_dialogue,
    get_llm_response,
    read_messages,
    chat
)

from .ai_books import (
    get_book_recommendations,
    create_recommendation_prompt,
    format_recommendations,
    get_book_recommendations_from_file
)

__all__ = [
    # Database functions
    'init_db',
    'get_db_connection',
    'log_dialogue',
    'log_book_recommendations',
    'get_user_dialogues',
    'get_user_recommendations',
    'get_dialogue_by_id',
    
    # Main AI functions
    'initialize_dialogue',
    'get_llm_response',
    'read_messages',
    'chat',
    
    # Book recommendation functions
    'get_book_recommendations',
    'create_recommendation_prompt',
    'format_recommendations',
    'get_book_recommendations_from_file'
] 
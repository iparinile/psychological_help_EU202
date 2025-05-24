import sqlite3
from typing import List, Dict
import json
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Путь к базе данных относительно корня проекта
DATABASE_PATH = 'telegram_bot/ai_service/dialogues.db'

def get_db_connection():
    """Create a database connection and return it"""
    logging.info("Creating database connection")
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    logging.info("Initializing database")
    if not os.path.exists(os.path.dirname(DATABASE_PATH)):
        os.makedirs(os.path.dirname(DATABASE_PATH))
        logging.info(f"Created directory: {os.path.dirname(DATABASE_PATH)}")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create dialogues table
    logging.info("Creating dialogues table")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dialogues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            issue_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            dialogue_json TEXT NOT NULL
        )
    ''')
    
    # Create book recommendations table
    logging.info("Creating book_recommendations table")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS book_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            issue_id TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            recommendations_json TEXT NOT NULL,
            dialogue_id INTEGER,
            FOREIGN KEY (dialogue_id) REFERENCES dialogues (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logging.info("Database initialization completed")

def log_dialogue(user_id: str, issue_id: str, dialogue: List[Dict[str, str]]) -> int:
    """
    Log a dialogue to the database
    
    Args:
        user_id (str): Unique identifier for the user
        issue_id (str): ID of the psychological issue
        dialogue (List[Dict[str, str]]): The dialogue history
        
    Returns:
        int: ID of the inserted dialogue record
    """
    logging.info(f"Logging dialogue for user {user_id}, issue {issue_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    dialogue_json = json.dumps(dialogue, ensure_ascii=False)
    
    cursor.execute('''
        INSERT INTO dialogues (user_id, issue_id, dialogue_json)
        VALUES (?, ?, ?)
    ''', (user_id, issue_id, dialogue_json))
    
    dialogue_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logging.info(f"Dialogue logged successfully with ID: {dialogue_id}")
    return dialogue_id

def log_book_recommendations(user_id: str, issue_id: str, recommendations: Dict, dialogue_id: int) -> int:
    """
    Log book recommendations to the database
    
    Args:
        user_id (str): Unique identifier for the user
        issue_id (str): ID of the psychological issue
        recommendations (Dict): The recommendations provided
        dialogue_id (int): ID of the related dialogue
        
    Returns:
        int: ID of the inserted recommendation record
    """
    logging.info(f"Logging book recommendations for user {user_id}, issue {issue_id}, dialogue {dialogue_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    recommendations_json = json.dumps(recommendations, ensure_ascii=False)
    
    cursor.execute('''
        INSERT INTO book_recommendations (user_id, issue_id, recommendations_json, dialogue_id)
        VALUES (?, ?, ?, ?)
    ''', (user_id, issue_id, recommendations_json, dialogue_id))
    
    recommendation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    logging.info(f"Book recommendations logged successfully with ID: {recommendation_id}")
    return recommendation_id

def get_user_dialogues(user_id: str) -> List[Dict]:
    """
    Retrieve all dialogues for a specific user
    
    Args:
        user_id (str): Unique identifier for the user
        
    Returns:
        List[Dict]: List of dialogue records
    """
    logging.info(f"Retrieving dialogues for user {user_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM dialogues 
        WHERE user_id = ? 
        ORDER BY timestamp DESC
    ''', (user_id,))
    
    rows = cursor.fetchall()
    dialogues = []
    for row in rows:
        dialogue_dict = dict(row)
        dialogue_dict['dialogue_json'] = json.loads(dialogue_dict['dialogue_json'])
        dialogues.append(dialogue_dict)
    
    conn.close()
    logging.info(f"Retrieved {len(dialogues)} dialogues for user {user_id}")
    return dialogues

def get_user_recommendations(user_id: str) -> List[Dict]:
    """
    Retrieve all book recommendations for a specific user
    
    Args:
        user_id (str): Unique identifier for the user
        
    Returns:
        List[Dict]: List of recommendation records
    """
    logging.info(f"Retrieving book recommendations for user {user_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM book_recommendations 
        WHERE user_id = ? 
        ORDER BY timestamp DESC
    ''', (user_id,))
    
    rows = cursor.fetchall()
    recommendations = []
    for row in rows:
        rec_dict = dict(row)
        rec_dict['recommendations_json'] = json.loads(rec_dict['recommendations_json'])
        recommendations.append(rec_dict)
    
    conn.close()
    logging.info(f"Retrieved {len(recommendations)} book recommendations for user {user_id}")
    return recommendations

def get_dialogue_by_id(dialogue_id: int) -> Dict:
    """
    Retrieve a specific dialogue by its ID
    
    Args:
        dialogue_id (int): ID of the dialogue to retrieve
        
    Returns:
        Dict: Dialogue record or None if not found
    """
    logging.info(f"Retrieving dialogue with ID {dialogue_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM dialogues 
        WHERE id = ?
    ''', (dialogue_id,))
    
    row = cursor.fetchone()
    if row:
        dialogue_dict = dict(row)
        dialogue_dict['dialogue_json'] = json.loads(dialogue_dict['dialogue_json'])
        conn.close()
        logging.info(f"Successfully retrieved dialogue {dialogue_id}")
        return dialogue_dict
    
    conn.close()
    logging.warning(f"Dialogue {dialogue_id} not found")
    return None

# Initialize the database when the module is imported
init_db() 
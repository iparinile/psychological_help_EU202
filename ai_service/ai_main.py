from openai import OpenAI
import json
from typing import List, Dict
import os
import logging
def initialize_dialogue(issue_id: str, output_path: str = 'ai_service/demo_dialogue.json') -> None:
    """
    Initialize dialogue with system prompt based on selected issue.
    
    Args:
        issue_id (str): ID of the psychological issue (1 - depression, 2 - burnout, 3 - relationship problems)
        output_path (str): Path where to save the initial dialogue
    """
    # Load system prompts
    with open('ai_service/system_prompts.json', 'r', encoding='utf-8') as f:
        prompts = json.load(f)
    
    if issue_id not in prompts:
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
    print(f"Initial dialogue: {initial_dialogue}")
    get_llm_response(initial_dialogue)


def get_llm_response(messages: List[Dict[str, str]]) -> str:
    """
    Get response from LLM based on dialogue history.
    
    Args:
        messages (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content' keys
        
    Returns:
        str: LLM's response text
    """
    # Load config
    with open('ai_service/config.json', 'r') as f:
        config = json.load(f)

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=config['openrouter_api_key'],
    )
    print(f"Getting response from LLM")
    completion = client.chat.completions.create(
        model="google/gemma-3-4b-it:free",
        messages=messages
    )
    print(f"Response from LLM: {completion.choices[0].message.content}")
    return completion.choices[0].message.content

def read_messages(path: str) -> List[Dict[str, str]]:
    print(f"Reading messages from {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def chat(issue_id: str, input_path: str = 'ai_service/demo_dialogue.json'):
    print(f"Chatting with issue_id: {issue_id}")
    messages = read_messages(input_path)
    response = get_llm_response(messages)
    # messages.append({"role": "assistant", "content": response})
    return response

if __name__ == "__main__":
    chat(1, 'ai_service/demo_dialogue.json')
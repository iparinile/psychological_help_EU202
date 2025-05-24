from openai import OpenAI
import json

with open('telegram_bot/ai_service/config.json', 'r') as f:
    config = json.load(f)

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=config['openrouter_api_key'],
)

completion = client.chat.completions.create(
  model="google/gemma-3-4b-it:free",
  messages=[
    {
      "role": "user",
      "content": "В чем смысл жизни? Коротко в 1 предложении"
    },
    {
      "role": "assistant",
      "content": "В чем смысл жизни? Коротко в 1 предложении"
    },
    {
      "role": "user",
      "content": "В чем смысл жизни? Коротко в 1 предложении"
    },
    {
      "role": "assistant",
      "content": "В чем смысл жизни? Коротко в 1 предложении"
    },
    {
      "role": "user",
      "content": "В чем смысл жизни? Коротко в 1 предложении"
    },
    {
      "role": "assistant",
      "content": "В чем смысл жизни? Коротко в 1 предложении"
    },
  ]
)

print(completion.choices[0].message.content)

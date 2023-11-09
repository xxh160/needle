#!/usr/bin/env python

import os
import requests

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

headers = {
    'Content-Type': 'application/json',
    'Authorization': f"Bearer {OPENAI_API_KEY}",
}

json_data = {
    'model': 'gpt-3.5-turbo',
    'messages': [
        {
            'role': 'user',
            'content': 'Hello!',
        },
    ],
}


if __name__ == "__main__":
    response = requests.post('https://api.openai-proxy.com/v1/chat/completions', headers=headers, json=json_data)
    print(response.content)

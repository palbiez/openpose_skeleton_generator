import requests
import json

try:
    response = requests.get("http://127.0.0.1:8190/api/filter", timeout=5)
    data = response.json()
    print(f"Loaded {len(data)} poses")
    if data:
        print(f"First pose: {data[0].get('filename', 'unknown')}")
except Exception as e:
    print(f"Error: {e}")
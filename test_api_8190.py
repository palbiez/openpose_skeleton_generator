import requests

response = requests.get("http://127.0.0.1:8190/api/filter")
data = response.json()
print(f"API returned {len(data['poses'])} poses")
print(f"Total count: {data['count']}")
print(f"Total pages: {data['total_pages']}")

if data['poses']:
    print(f"First pose: {data['poses'][0]['filename']}")
else:
    print("No poses in response!")
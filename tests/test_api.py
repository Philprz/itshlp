import requests

url = "https://testback-dutt.onrender.com/api/search"

payload = {
    "query": "Problèmes de connexion SAP",
    "client": "AZERGO",
    "erp": "SAP",
    "format": "Summary",
    "recentOnly": True,
    "limit": 5
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

print(f"✅ Status: {response.status_code}")
print("📦 Réponse:")
print(response.json())

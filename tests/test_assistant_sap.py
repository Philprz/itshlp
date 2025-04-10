import openai
import os
import time

# 🔐 Authentification OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = "org-vu89XIsbAjj5MmWlFs040tRC"

# 🆔 ID de l'assistant SAP (à mettre à jour après création)
ASSISTANT_ID = "asst_tL6bKrZfqK0aBivBJOFkDbHz"  # Remplace par le bon ID

# 🧵 Crée un thread de conversation
thread = openai.beta.threads.create()
print("\U0001f9f5 Thread créé :", thread.id)

# 💬 Ajoute une question utilisateur
openai.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="Comment fonctionne le processus d'approvisionnement dans SAP Business One ?"
)

# ⏳ Lance l'exécution de l'assistant
run = openai.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=ASSISTANT_ID
)

print("\u23f3 Exécution en cours...")
while True:
    run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    if run_status.status == "completed":
        break
    elif run_status.status in ["failed", "cancelled"]:
        print("❌ Échec :", run_status.status)
        exit(1)
    time.sleep(1)

# 📄 Récupère la réponse
messages = openai.beta.threads.messages.list(thread_id=thread.id)
response = messages.data[0].content[0].text.value

print("\n✅ Réponse de l'assistant :\n")
print(response)

# 🔧 Nettoyage optionnel du thread
openai.beta.threads.delete(thread_id=thread.id)

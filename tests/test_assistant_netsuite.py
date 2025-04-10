import openai
import os
import time

# Charge ta clé API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")  # ou colle-la ici directement
openai.organization = "org-vu89XIsbAjj5MmWlFs040tRC"
# ID de ton Assistant (copié depuis ton interface)
ASSISTANT_ID = "asst_89fc56lBkp9PveR5s7OunoT5"

# Étape 1 : Crée un thread de conversation
thread = openai.beta.threads.create()
print("🧵 Thread créé :", thread.id)

# Étape 2 : Ajoute un message utilisateur dans ce thread
openai.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="Quels sont les modules standards de NetSuite ?"
)

# Étape 3 : Lance l'exécution de l'assistant
run = openai.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=ASSISTANT_ID
)

print("⏳ Exécution en cours...")
while True:
    run_status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    if run_status.status == "completed":
        break
    elif run_status.status in ["failed", "cancelled"]:
        print("❌ Échec :", run_status.status)
        exit(1)
    time.sleep(1)

# Étape 4 : Récupère les messages de réponse
messages = openai.beta.threads.messages.list(thread_id=thread.id)
response = messages.data[0].content[0].text.value

print("\n✅ Réponse de l'assistant :\n")
print(response)

# Étape 5 : Nettoie le thread (optionnel)
openai.beta.threads.delete(thread_id=thread.id)

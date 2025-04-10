import openai
import os

# 🔐 Authentification
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = "org-vu89XIsbAjj5MmWlFs040tRC"  # ton organisation

# 🧠 Contenu de l'assistant
instructions = """
Tu es un assistant spécialisé en NetSuite. Lorsque tu réponds à une question, commence par rechercher des informations sur les sites suivants, par ordre de priorité :
https://netsuiteprofessionals.com
https://blog.prolecto.com
https://docs.oracle.com/en/cloud/saas/netsuite/ns-online-help/

Si la réponse n’est pas disponible sur ces sites, élargis ta réponse avec tes connaissances internes.
Fournis des réponses claires, structurées, sourcées, avec des liens directs si possible.

Ta réponse doit être fonctionnelle, destinée à des consultants ou utilisateurs de NetSuite.
"""

# ⚙️ Création
assistant = openai.beta.assistants.create(
    name="NetSuiteAssistant",
    instructions=instructions,
    model="gpt-4o"
)

print("✅ Assistant créé avec succès !")
print("🆔 Assistant ID :", assistant.id)

import redis
import os

# Utilise la variable d'environnement REDIS_URL si disponible
redis_url = os.getenv("REDIS_URL", "redis-cli --tls -u redis://default:ASmFAAIjcDFhZTE4MDU2MzQ0OGE0YTE3OGY5ZDJlMDUxNzVkMGM4NXAxMA@finer-octopus-10629.upstash.io:6379")  # Remplace ici !

try:
    print(f"🔌 Connexion à Redis : {redis_url}")
    r = redis.Redis.from_url(redis_url)

    # Test simple : écrire et lire une clé
    r.set("test:ping", "pong")
    value = r.get("test:ping")

    print("✅ Connexion réussie ! Valeur lue :", value.decode())
except Exception as e:
    print("❌ Erreur de connexion à Redis :", str(e))

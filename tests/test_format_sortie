import sys
import os
# Ajoute le dossier parent (QdrantWeb) au path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from query_system import QdrantSystem


if __name__ == "__main__":
    system = QdrantSystem("ListeClients.csv")

    query = "problème de connexion SAP"
    client = "AZERGO"
    format_types = ["Summary", "Detail", "Guide"]

    for fmt in format_types:
        print(f"\n===== 🔎 FORMAT : {fmt.upper()} =====")
        result = system.process_query(
            query=query,
            client_name=client,
            format_type=fmt,
            recent_only=True,
            limit=5
        )

        print(f"\n📦 Sources : {result['sources']}\n")

        for i, content in enumerate(result["content"], 1):
            print(f"--- Résultat {i} ---\n{content}\n")

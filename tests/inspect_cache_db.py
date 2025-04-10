from sqlalchemy import create_engine, inspect

# Connexion à la base SQLite
engine = create_engine("sqlite:///cache.db")
inspector = inspect(engine)

# Liste des tables
tables = inspector.get_table_names()
print("📋 Tables trouvées dans cache.db :", tables)

# Afficher les colonnes de chaque table attendue
for table in ["cached_queries", "cached_formats"]:
    if table in tables:
        print(f"\n🔍 Colonnes dans {table} :")
        columns = inspector.get_columns(table)
        for col in columns:
            print(f"  - {col['name']} ({col['type']})")
    else:
        print(f"\n⚠️ Table {table} non trouvée.")

import sqlite3
import pandas as pd
import os

# Constants
DB_NAME = "nhl_data.db"  # Name your DB generically since you'll expand
CSV_FOLDER = "."         # Folder where CSVs are stored (same as script for now)

# Connect to or create the SQLite database
conn = sqlite3.connect(DB_NAME)

# Loop through all CSVs in the folder
for filename in os.listdir(CSV_FOLDER):
    if filename.endswith(".csv"):
        table_name = filename.replace(".csv", "").lower().replace("-", "_")
        file_path = os.path.join(CSV_FOLDER, filename)

        try:
            df = pd.read_csv(file_path)
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            print(f"✅ Imported '{filename}' as table '{table_name}'")
        except Exception as e:
            print(f"❌ Failed to import '{filename}': {e}")

# Close DB connection
conn.close()

print(f"\n✅ All CSVs added to '{DB_NAME}' successfully.")

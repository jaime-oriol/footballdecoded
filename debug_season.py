# debug_season.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_manager
import pandas as pd

db = get_db_manager()

# Check what seasons exist in database
query = "SELECT DISTINCT league, season FROM footballdecoded.teams_domestic ORDER BY league, season"
result = pd.read_sql(query, db.engine)

print("SEASONS IN DATABASE:")
print(result)

db.close()
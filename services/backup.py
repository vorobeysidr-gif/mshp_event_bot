import csv
from datetime import datetime

def backup_to_csv(data):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(f"backup_{timestamp}.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            data.get("name", ""),
            data.get("phone", ""),
            data.get("age", ""),
            data.get("is_mshp_student", ""),
            data.get("time", ""),
            timestamp
        ])

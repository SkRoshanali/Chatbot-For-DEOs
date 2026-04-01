"""Run this from the chatbot folder: python test_upload_direct.py"""
import pandas as pd
from pymongo import MongoClient

df = pd.DataFrame([
    {'roll': 'CSF001', 'name': 'Student Name', 'department': 'CSE', 'semester': 3, 'batch': '2022-26', 'cgpa': 8.5, 'attendance': 85, 'backlogs': 0, 'internal': 42, 'external': 70},
    {'roll': 123,      'name': 'hklw',          'department': 'cse', 'semester': 3, 'batch': '2023-27', 'cgpa': 7.2, 'attendance': 94, 'backlogs': 0, 'internal': 48, 'external': 41},
    {'roll': 372,      'name': 'ert',            'department': 'cse', 'semester': 3, 'batch': '2023-27', 'cgpa': 7.2, 'attendance': 94, 'backlogs': 0, 'internal': 15, 'external': 5},
])

def safe_str(val, default=''):
    s = str(val).strip()
    return default if s.lower() in ('nan', 'none', '') else s

def safe_int(val, default=0):
    try:
        s = str(val).strip()
        return int(float(s)) if s.lower() not in ('nan', 'none', '') else default
    except:
        return default

def safe_float(val, default=0.0):
    try:
        s = str(val).strip()
        return float(s) if s.lower() not in ('nan', 'none', '') else default
    except:
        return default

db = MongoClient('mongodb://localhost:27017/')['deo_chatbot']
inserted = updated = 0

for _, row in df.iterrows():
    roll = safe_str(row.get('roll', ''), '').upper()
    if not roll:
        continue
    doc = {
        'roll':       roll,
        'name':       safe_str(row.get('name', ''), 'Unknown'),
        'department': safe_str(row.get('department', ''), 'CSE').upper(),
        'semester':   str(safe_int(row.get('semester', 1), 1)),
        'batch':      safe_str(row.get('batch', ''), ''),
        'cgpa':       safe_float(row.get('cgpa', 0)),
        'attendance': safe_int(row.get('attendance', 0)),
        'backlogs':   safe_int(row.get('backlogs', 0)),
        'internal':   safe_int(row.get('internal', 0)),
        'external':   safe_int(row.get('external', 0)),
    }
    print('Processing:', doc['roll'], '-', doc['name'])
    if db.students.find_one({'roll': roll}):
        db.students.update_one({'roll': roll}, {'$set': doc})
        updated += 1
    else:
        db.students.insert_one(doc)
        inserted += 1

print(f'\nDone: inserted={inserted} updated={updated}')
print(f'Total students now: {db.students.count_documents({})}')

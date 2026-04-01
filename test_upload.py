"""
Test script to verify MongoDB connection and upload functionality
Run this AFTER starting Flask app to test if upload works
"""
import pandas as pd
from pymongo import MongoClient

# Test MongoDB connection
print("=" * 50)
print("Testing MongoDB Connection...")
print("=" * 50)

try:
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("✅ MongoDB is running and accessible")
    
    db = client['deo_chatbot']
    
    # Check collections
    collections = db.list_collection_names()
    print(f"✅ Collections found: {collections}")
    
    # Check student count
    student_count = db.students.count_documents({})
    print(f"✅ Current student count: {student_count}")
    
    # List first 3 students
    if student_count > 0:
        print("\n📋 Sample students:")
        for s in db.students.find().limit(3):
            print(f"   - {s.get('roll')}: {s.get('name')} (Sem {s.get('semester')})")
    
    print("\n" + "=" * 50)
    print("Creating test Excel file...")
    print("=" * 50)
    
    # Create test data
    test_data = pd.DataFrame([
        {
            'roll': 'TEST001',
            'name': 'Test Student 1',
            'department': 'CSE',
            'semester': '3',
            'batch': '2022-26',
            'cgpa': 8.5,
            'attendance': 85,
            'backlogs': 0,
            'internal': 42,
            'external': 70
        },
        {
            'roll': 'TEST002',
            'name': 'Test Student 2',
            'department': 'ECE',
            'semester': '5',
            'batch': '2021-25',
            'cgpa': 7.8,
            'attendance': 78,
            'backlogs': 1,
            'internal': 38,
            'external': 65
        }
    ])
    
    # Save to Excel
    test_data.to_excel('test_upload.xlsx', index=False, sheet_name='Students')
    print("✅ Created test_upload.xlsx")
    print("\n📤 Now upload this file through the web interface:")
    print("   1. Login to the app")
    print("   2. Go to Data Management")
    print("   3. Click Upload File tab")
    print("   4. Upload test_upload.xlsx")
    print("   5. Check View Data tab to see if TEST001 and TEST002 appear")
    
    print("\n" + "=" * 50)
    print("All checks passed! MongoDB is ready.")
    print("=" * 50)
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 MongoDB might not be running. Try:")
    print("   1. Run start_mongodb.bat")
    print("   2. Or install MongoDB from: https://www.mongodb.com/try/download/community")
    print("   3. Make sure MongoDB service is started")

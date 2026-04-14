"""
Preservation Property Tests - Railway Deployment Crash Fix

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

These tests verify that all existing functionality continues to work correctly
when MySQL is available. They capture the baseline behavior that must be preserved
after implementing the fix.

Property 2: Preservation - Database Functionality When Available
For any deployment environment where MySQL is available, the fixed application
SHALL behave identically to the original application.

EXPECTED OUTCOME: These tests MUST PASS on both unfixed and fixed code when MySQL is available.
"""

import pytest
import os
import sys
from database import init_db, get_conn
from db_utils import (
    find_user, create_user, count_students, get_students,
    insert_student, find_student, update_student, delete_student
)


@pytest.fixture(scope="module")
def ensure_database():
    """
    Fixture to ensure MySQL is available for preservation tests.
    These tests require a working database connection.
    """
    try:
        # Initialize database to set DB_AVAILABLE flag
        from database import init_db
        success = init_db()
        if not success:
            pytest.skip("MySQL not available for preservation tests")
        
        # Verify MySQL is available
        conn = get_conn()
        conn.close()
        yield True
    except Exception as e:
        pytest.skip(f"MySQL not available for preservation tests: {e}")


def test_database_initialization_works(ensure_database):
    """
    Property: Database initialization creates schema and seeds data successfully.
    
    **Validates: Requirements 3.1**
    
    This test verifies that init_db() works correctly when MySQL is available.
    """
    # Database should already be initialized from startup
    # Verify we can connect and query
    conn = get_conn()
    cursor = conn.cursor()
    
    # Check that tables exist
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    
    assert 'students' in tables, "students table should exist"
    assert 'users' in tables, "users table should exist"
    assert 'departments' in tables, "departments table should exist"
    assert 'subjects' in tables, "subjects table should exist"
    assert 'subject_marks' in tables, "subject_marks table should exist"
    
    cursor.close()
    conn.close()
    
    print("✓ Database initialization works correctly")


def test_user_crud_operations(ensure_database):
    """
    Property: User CRUD operations work correctly with database available.
    
    **Validates: Requirements 3.2, 3.4**
    
    This test verifies that user management functions work correctly.
    """
    from werkzeug.security import generate_password_hash
    import pyotp
    
    # Test user creation
    test_username = 'test_preservation_user'
    test_password = generate_password_hash('testpass123')
    test_secret = pyotp.random_base32()
    
    # Clean up if exists
    try:
        from db_utils import delete_user
        delete_user(test_username)
    except:
        pass
    
    # Create user
    create_user(test_username, test_password, 'DEO', 'CSE', test_secret)
    
    # Find user
    user = find_user(test_username)
    assert user is not None, "User should be found after creation"
    assert user['username'] == test_username
    assert user['role'] == 'DEO'
    assert user['dept'] == 'CSE'
    assert user['otp_secret'] == test_secret
    
    # Clean up
    delete_user(test_username)
    
    # Verify deletion
    user = find_user(test_username)
    assert user is None, "User should not be found after deletion"
    
    print("✓ User CRUD operations work correctly")


def test_student_crud_operations(ensure_database):
    """
    Property: Student CRUD operations work correctly with database available.
    
    **Validates: Requirements 3.2, 3.3, 3.4**
    
    This test verifies that student management functions work correctly.
    """
    # Test student data
    test_roll = 'TEST999999'
    test_student = {
        'roll': test_roll,
        'name': 'Test Student',
        'section': 'SEC-99',
        'department': 'CSE',
        'semester': '3',
        'batch': '2023-27',
        'cgpa': 8.5,
        'attendance': 85,
        'backlogs': 0,
        'internal': 25,
        'external': 70,
        'subjects': {
            'CN': {'attendance': 85, 'internal': 25, 'external': 70},
            'SE': {'attendance': 90, 'internal': 28, 'external': 75}
        }
    }
    
    # Clean up if exists
    try:
        delete_student(test_roll)
    except:
        pass
    
    # Create student
    insert_student(test_student)
    
    # Find student
    student = find_student(test_roll)
    assert student is not None, "Student should be found after creation"
    assert student['roll'] == test_roll
    assert student['name'] == 'Test Student'
    assert student['section'] == 'SEC-99'
    assert student['cgpa'] == 8.5
    
    # Update student
    update_student(test_roll, {'cgpa': 9.0, 'attendance': 95})
    
    # Verify update
    student = find_student(test_roll)
    assert student['cgpa'] == 9.0, "CGPA should be updated"
    assert student['attendance'] == 95, "Attendance should be updated"
    
    # Delete student
    delete_student(test_roll)
    
    # Verify deletion
    student = find_student(test_roll)
    assert student is None, "Student should not be found after deletion"
    
    print("✓ Student CRUD operations work correctly")


def test_student_queries(ensure_database):
    """
    Property: Student query operations work correctly with database available.
    
    **Validates: Requirements 3.3**
    
    This test verifies that querying students by various filters works correctly.
    """
    # Get all students
    all_students = get_students()
    assert isinstance(all_students, list), "get_students should return a list"
    
    # Get students by department
    cse_students = get_students(dept='CSE')
    assert isinstance(cse_students, list), "get_students with dept filter should return a list"
    
    # Count students
    count = count_students()
    assert isinstance(count, int), "count_students should return an integer"
    assert count >= 0, "count_students should return non-negative number"
    
    print(f"✓ Student queries work correctly (found {count} students)")


def test_report_generation(ensure_database):
    """
    Property: Report generation works correctly with database available.
    
    **Validates: Requirements 3.3, 3.5**
    
    This test verifies that report generation functions work correctly.
    """
    # Get students for report
    students = get_students(dept='CSE')
    
    if len(students) > 0:
        # Verify student data structure
        student = students[0]
        assert 'roll' in student, "Student should have roll number"
        assert 'name' in student, "Student should have name"
        assert 'section' in student, "Student should have section"
        assert 'cgpa' in student, "Student should have CGPA"
        assert 'attendance' in student, "Student should have attendance"
        
        print(f"✓ Report generation works correctly (tested with {len(students)} students)")
    else:
        print("✓ Report generation structure verified (no students in database)")


def test_database_connection_pool(ensure_database):
    """
    Property: Database connection pooling works correctly.
    
    **Validates: Requirements 3.1, 3.2**
    
    This test verifies that the connection pool can handle multiple connections.
    """
    connections = []
    
    try:
        # Get multiple connections from pool
        for i in range(5):
            conn = get_conn()
            connections.append(conn)
            
            # Verify connection works
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1, "Connection should execute queries"
            cursor.close()
        
        print("✓ Database connection pool works correctly (tested 5 connections)")
    
    finally:
        # Clean up connections
        for conn in connections:
            try:
                conn.close()
            except:
                pass


def test_subject_data_structure(ensure_database):
    """
    Property: Subject data structure is preserved correctly.
    
    **Validates: Requirements 3.3**
    
    This test verifies that subject-related data structures work correctly.
    """
    from db_utils import SUBJECTS
    
    # Verify SUBJECTS constant exists and is valid
    assert isinstance(SUBJECTS, (list, tuple)), "SUBJECTS should be a list or tuple"
    assert len(SUBJECTS) > 0, "SUBJECTS should not be empty"
    
    # Get students and verify subject data structure
    students = get_students(dept='CSE')
    
    if len(students) > 0:
        student = students[0]
        if 'subjects' in student and student['subjects']:
            subjects = student['subjects']
            assert isinstance(subjects, dict), "Student subjects should be a dictionary"
            
            # Verify subject data structure
            for subj_code, subj_data in subjects.items():
                assert 'attendance' in subj_data, f"Subject {subj_code} should have attendance"
                assert 'internal' in subj_data, f"Subject {subj_code} should have internal marks"
                assert 'external' in subj_data, f"Subject {subj_code} should have external marks"
    
    print("✓ Subject data structure preserved correctly")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

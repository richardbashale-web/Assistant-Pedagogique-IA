import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

with connection.cursor() as cursor:
    try:
        cursor.execute("SELECT id, professeur FROM courses_course;")
        rows = cursor.fetchall()
        print("Courses before update:", rows)
        
        # Get or create a default professor
        cursor.execute("SELECT id FROM users_professor LIMIT 1;")
        prof = cursor.fetchone()
        
        if not prof:
            # We need to create a default user first? This might be complicated if users_professor has many fields.
            print("No professor found, deleting courses...")
            cursor.execute("TRUNCATE TABLE courses_course CASCADE;")
        else:
            prof_id = prof[0]
            print("Updating courses to use professor_id:", prof_id)
            cursor.execute("ALTER TABLE courses_course ALTER COLUMN professeur TYPE bigint USING %s;", [prof_id])
            
    except Exception as e:
        print("Error:", e)

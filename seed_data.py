import os
import django
import sys
from datetime import date

# Set up Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_main.settings')
django.setup()

from django.contrib.auth.models import User
from employees.models import Employee

def create_admin():
    if not User.objects.filter(username='admin').exists():
        print("Creating admin user...")
        User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
        print("Admin created (username: admin, password: adminpass)")
    else:
        print("Admin already exists.")

def seed_employees():
    employees_data = [
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'phone': '123-456-7890',
            'department': 'Engineering',
            'designation': 'Software Engineer',
            'salary': 85000.00,
            'join_date': date(2022, 1, 15),
            'username': 'johndoe',
            'password': 'password123'
        },
        {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@example.com',
            'phone': '098-765-4321',
            'department': 'Human Resources',
            'designation': 'HR Manager',
            'salary': 90000.00,
            'join_date': date(2021, 5, 10),
            'username': 'janesmith',
            'password': 'password123'
        },
        {
            'first_name': 'Mike',
            'last_name': 'Johnson',
            'email': 'mike.johnson@example.com',
            'phone': '555-555-5555',
            'department': 'Sales',
            'designation': 'Sales Representative',
            'salary': 65000.00,
            'join_date': date(2023, 8, 1),
            'username': 'mikej',
            'password': 'password123'
        }
    ]

    for data in employees_data:
        if not User.objects.filter(username=data['username']).exists():
            print(f"Creating user and employee for {data['first_name']} {data['last_name']}...")
            user = User.objects.create_user(username=data['username'], email=data['email'], password=data['password'])
            
            Employee.objects.create(
                user=user,
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                phone=data['phone'],
                department=data['department'],
                designation=data['designation'],
                salary=data['salary'],
                join_date=data['join_date']
            )
        else:
            print(f"User {data['username']} already exists.")

if __name__ == '__main__':
    create_admin()
    seed_employees()
    print("Database seeding complete!")

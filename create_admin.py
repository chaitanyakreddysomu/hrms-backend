# Create Admin User Script
# Run this with: poetry run python create_admin.py

import requests
import json

def create_admin():
    """Create an admin user via the API"""
    
    url = "http://localhost:8000/add-admin/"
    
    # Admin credentials
    admin_data = {
        "email": "admin@hrms.com",
        "password": "admin123",
        "name": "System Administrator"
    }
    
    print("Creating admin user...")
    print(f"Email: {admin_data['email']}")
    print(f"Password: {admin_data['password']}")
    print()
    
    try:
        response = requests.post(url, json=admin_data)
        
        if response.status_code == 201:
            print("✓ Admin created successfully!")
            print()
            print("Response:")
            print(json.dumps(response.json(), indent=2))
            print()
            print("You can now login with:")
            print(f"  Email: {admin_data['email']}")
            print(f"  Password: {admin_data['password']}")
        else:
            print("✗ Failed to create admin")
            print(f"Status Code: {response.status_code}")
            print("Response:")
            print(json.dumps(response.json(), indent=2))
            
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to the server")
        print("Make sure Django server is running at http://localhost:8000")
        print()
        print("Start the server with:")
        print("  cd c:\\Users\\HP\\Downloads\\hrms-main-django")
        print("  poetry run python manage.py runserver")
    except Exception as e:
        print(f"✗ Error: {str(e)}")

if __name__ == "__main__":
    create_admin()

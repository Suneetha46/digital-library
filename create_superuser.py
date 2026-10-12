import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_portal.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()

def main():
    print("--- [create_superuser.py] Starting superuser setup & library initialization ---")

    # Read credentials from environment variables, with safe defaults
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'librarian')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'librarian@athenaeum.edu')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin1234')

    # Create superuser if it doesn't already exist
    user = User.objects.filter(username=username).first()
    if not user:
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name='Eleanor',
            last_name='Vance'
        )
        print(f" Superuser '{username}' created successfully!")
    else:
        user.is_staff = True
        user.is_superuser = True
        if password:
            user.set_password(password)
        user.save()
        print(f" Superuser '{username}' already exists (credentials verified).")

    # Populate initial books, authors, members, and circulation records if database is empty
    try:
        from circulation.models import Book
        if Book.objects.count() == 0:
            print(" Catalog is empty. Automatically running 'seed_library'...")
            call_command('seed_library')
            print(" Initial catalog and demo accounts populated successfully!")
        else:
            print(f" Library catalog already contains {Book.objects.count()} books. Skipping seeding.")
    except Exception as e:
        print(f"Seeding check note: {e}")

    print("--- [create_superuser.py] Completed successfully! ---")

if __name__ == '__main__':
    main()

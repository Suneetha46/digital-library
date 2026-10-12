from datetime import timedelta, date
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from circulation.models import Author, Book, Member, CirculationRecord


class Command(BaseCommand):
    help = 'Seeds initial sample authors, books, members, staff user, and circulation records.'

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding for Athenaeum Digital Library...")

        # 1. Create Superuser / Staff Librarian
        librarian_user, created = User.objects.get_or_create(
            username='librarian',
            defaults={
                'email': 'librarian@athenaeum.edu',
                'first_name': 'Eleanor',
                'last_name': 'Vance',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        librarian_user.set_password('admin1234')
        librarian_user.save()
        self.stdout.write(self.style.SUCCESS(f"Staff Librarian created: 'librarian' / 'admin1234'"))

        # 2. Create Library Members
        member1_user, _ = User.objects.get_or_create(
            username='alex_reader',
            defaults={
                'email': 'alex@example.com',
                'first_name': 'Alex',
                'last_name': 'Rivers',
            }
        )
        member1_user.set_password('member1234')
        member1_user.save()

        member1, _ = Member.objects.get_or_create(
            user=member1_user,
            defaults={
                'membership_id': 'LIB-2026-ALEX01',
                'phone': '+1 (555) 234-5678',
                'address': '42 Evergreen Terrace, Seattle, WA',
                'max_books_allowed': 5,
            }
        )

        member2_user, _ = User.objects.get_or_create(
            username='sophia_books',
            defaults={
                'email': 'sophia@example.com',
                'first_name': 'Sophia',
                'last_name': 'Chen',
            }
        )
        member2_user.set_password('member1234')
        member2_user.save()

        member2, _ = Member.objects.get_or_create(
            user=member2_user,
            defaults={
                'membership_id': 'LIB-2026-SOPH02',
                'phone': '+1 (555) 987-6543',
                'address': '108 Beacon Street, Boston, MA',
                'max_books_allowed': 5,
            }
        )
        self.stdout.write(self.style.SUCCESS("Library members created: alex_reader and sophia_books (password: member1234)"))

        # 3. Create Authors
        authors_data = [
            {
                'name': 'Robert C. Martin',
                'nationality': 'American',
                'birth_date': date(1952, 12, 5),
                'bio': 'Software engineer and author famously known as "Uncle Bob". Co-author of the Agile Manifesto and creator of Clean Code principles.',
                'photo_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=300&q=80',
            },
            {
                'name': 'Martin Fowler',
                'nationality': 'British',
                'birth_date': date(1963, 12, 18),
                'bio': 'Software engineer, speaker, and prominent author specializing in object-oriented analysis, refactoring, architecture, and agile software development.',
                'photo_url': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=300&q=80',
            },
            {
                'name': 'Frank Herbert',
                'nationality': 'American',
                'birth_date': date(1920, 10, 8),
                'bio': 'Critically acclaimed American science fiction author best known for his landmark epic novel Dune and its sequels.',
                'photo_url': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?auto=format&fit=crop&w=300&q=80',
            },
            {
                'name': 'Yuval Noah Harari',
                'nationality': 'Israeli',
                'birth_date': date(1976, 2, 24),
                'bio': 'Historian, philosopher, and professor in the Department of History at the Hebrew University of Jerusalem.',
                'photo_url': 'https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?auto=format&fit=crop&w=300&q=80',
            },
            {
                'name': 'Walter Isaacson',
                'nationality': 'American',
                'birth_date': date(1952, 5, 20),
                'bio': 'Acclaimed biographer, journalist, and professor. Author of biographies of Steve Jobs, Albert Einstein, and Leonardo da Vinci.',
                'photo_url': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=300&q=80',
            },
            {
                'name': 'Andrew Hunt & David Thomas',
                'nationality': 'American',
                'birth_date': date(1964, 4, 1),
                'bio': 'Pioneers in agile development and authors of The Pragmatic Programmer, transforming engineering culture worldwide.',
                'photo_url': 'https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=300&q=80',
            },
        ]

        authors_dict = {}
        for a_data in authors_data:
            author, _ = Author.objects.get_or_create(
                name=a_data['name'],
                defaults=a_data
            )
            authors_dict[author.name] = author

        self.stdout.write(self.style.SUCCESS(f"Created/verified {len(authors_dict)} authors."))

        # 4. Create Books
        books_data = [
            {
                'title': 'Clean Code: A Handbook of Agile Software Craftsmanship',
                'author': authors_dict['Robert C. Martin'],
                'isbn': '978-0132350884',
                'genre': 'Computer Science',
                'description': 'Even bad code can function. But if code isn’t clean, it can bring a development organization to its knees. Every year, countless hours and significant resources are lost because of poorly written code. This book is a must-read for any developer wanting to write readable, maintainable software.',
                'cover_url': 'https://images.unsplash.com/photo-1532012164546-f432f2e37271?auto=format&fit=crop&w=600&q=80',
                'total_copies': 4,
                'available_copies': 3,
                'publication_year': 2008,
                'publisher': 'Prentice Hall',
                'is_ebook_available': True,
            },
            {
                'title': 'Refactoring: Improving the Design of Existing Code',
                'author': authors_dict['Martin Fowler'],
                'isbn': '978-0134757599',
                'genre': 'Computer Science',
                'description': 'For more than twenty years, serious programmers have relied on Martin Fowler’s Refactoring to improve the design of existing code and enhance software maintainability.',
                'cover_url': 'https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=600&q=80',
                'total_copies': 3,
                'available_copies': 2,
                'publication_year': 2018,
                'publisher': 'Addison-Wesley Professional',
                'is_ebook_available': True,
            },
            {
                'title': 'The Pragmatic Programmer: Your Journey To Mastery',
                'author': authors_dict['Andrew Hunt & David Thomas'],
                'isbn': '978-0135957059',
                'genre': 'Computer Science',
                'description': 'Straight from the programming trenches, The Pragmatic Programmer cuts through the increasing specialization and technicalities of modern development to examine the core process.',
                'cover_url': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80',
                'total_copies': 5,
                'available_copies': 4,
                'publication_year': 2019,
                'publisher': 'Addison-Wesley',
                'is_ebook_available': True,
            },
            {
                'title': 'Dune (The Dune Chronicles, Book 1)',
                'author': authors_dict['Frank Herbert'],
                'isbn': '978-0441172719',
                'genre': 'Fantasy & Sci-Fi',
                'description': 'Set on the desert planet Arrakis, Dune tells the story of Paul Atreides as he navigates political betrayal, ecology, religion, and human destiny across the cosmos.',
                'cover_url': 'https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=600&q=80',
                'total_copies': 4,
                'available_copies': 3,
                'publication_year': 1965,
                'publisher': 'Chilton Books',
                'is_ebook_available': True,
            },
            {
                'title': 'Sapiens: A Brief History of Humankind',
                'author': authors_dict['Yuval Noah Harari'],
                'isbn': '978-0062316097',
                'genre': 'History & Biography',
                'description': 'From a renowned historian comes a groundbreaking narrative of humanity’s creation and evolution that explores the ways in which biology and history have defined us.',
                'cover_url': 'https://images.unsplash.com/photo-1461360370896-922624d12aa1?auto=format&fit=crop&w=600&q=80',
                'total_copies': 2,
                'available_copies': 0,  # Explicitly 0 to test out-of-stock validation!
                'publication_year': 2015,
                'publisher': 'Harper',
                'is_ebook_available': False,
            },
            {
                'title': 'Steve Jobs: The Exclusive Biography',
                'author': authors_dict['Walter Isaacson'],
                'isbn': '978-1451648539',
                'genre': 'History & Biography',
                'description': 'Based on more than forty interviews with Steve Jobs conducted over two years, this is the definitive, unvarnished portrait of the greatest tech innovator of our generation.',
                'cover_url': 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=600&q=80',
                'total_copies': 3,
                'available_copies': 3,
                'publication_year': 2011,
                'publisher': 'Simon & Schuster',
                'is_ebook_available': True,
            },
        ]

        books_dict = {}
        for b_data in books_data:
            book, _ = Book.objects.get_or_create(
                isbn=b_data['isbn'],
                defaults=b_data
            )
            books_dict[book.isbn] = book

        self.stdout.write(self.style.SUCCESS(f"Created/verified {len(books_dict)} books in catalog."))

        # 5. Create Circulation Records
        today = timezone.now().date()

        # Record A: Active regular loan (Alex Rivers has Clean Code)
        CirculationRecord.objects.get_or_create(
            book=books_dict['978-0132350884'],
            member=member1,
            status='ISSUED',
            defaults={
                'issue_date': today - timedelta(days=4),
                'due_date': today + timedelta(days=10),
                'issued_by': librarian_user,
                'notes': 'Book checked out in mint condition.',
            }
        )

        # Record B: Overdue loan (Alex Rivers has Refactoring - issued 20 days ago, due 6 days ago!)
        CirculationRecord.objects.get_or_create(
            book=books_dict['978-0134757599'],
            member=member1,
            status='OVERDUE',
            defaults={
                'issue_date': today - timedelta(days=20),
                'due_date': today - timedelta(days=6),
                'issued_by': librarian_user,
                'notes': 'Overdue reminder notice sent to member email.',
            }
        )

        # Record C: Returned book with paid fine (Sophia Chen had Dune, returned 2 days overdue)
        CirculationRecord.objects.get_or_create(
            book=books_dict['978-0441172719'],
            member=member2,
            status='RETURNED',
            return_date=today - timedelta(days=2),
            defaults={
                'issue_date': today - timedelta(days=18),
                'due_date': today - timedelta(days=4),
                'fine_amount': Decimal('2.00'),
                'fine_paid': True,
                'issued_by': librarian_user,
                'return_processed_by': librarian_user,
                'notes': 'Returned 2 days late. Fine of $2.00 paid via cash.',
            }
        )

        # Record D: Returned book on time with zero fine (Sophia Chen had Steve Jobs)
        CirculationRecord.objects.get_or_create(
            book=books_dict['978-1451648539'],
            member=member2,
            status='RETURNED',
            return_date=today - timedelta(days=5),
            defaults={
                'issue_date': today - timedelta(days=15),
                'due_date': today - timedelta(days=1),
                'fine_amount': Decimal('0.00'),
                'fine_paid': True,
                'issued_by': librarian_user,
                'return_processed_by': librarian_user,
                'notes': 'Returned on time in pristine condition.',
            }
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded circulation records with active, overdue, and returned states."))
        self.stdout.write(self.style.SUCCESS("All seed operations completed!"))

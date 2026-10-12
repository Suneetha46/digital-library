from datetime import timedelta, date
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from circulation.models import Author, Book, Member, CirculationRecord


class DigitalLibraryCirculationTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Staff User
        self.staff_user = User.objects.create_user(
            username='staff_test',
            password='password123',
            is_staff=True,
            is_superuser=True
        )

        # Create Regular Member User
        self.member_user = User.objects.create_user(
            username='member_test',
            password='password123',
            first_name='John',
            last_name='Doe',
            email='john@example.com'
        )
        self.member = Member.objects.create(
            user=self.member_user,
            membership_id='LIB-TEST-001',
            max_books_allowed=5
        )

        # Create Author
        self.author = Author.objects.create(
            name='Arthur Conan Doyle',
            bio='Creator of Sherlock Holmes',
            nationality='British'
        )

        # Create Book with 2 available copies
        self.book_available = Book.objects.create(
            title='A Study in Scarlet',
            author=self.author,
            isbn='978-0140439083',
            genre='Mystery & Thriller',
            total_copies=2,
            available_copies=2
        )

        # Create Book with 0 available copies (Out of stock)
        self.book_empty = Book.objects.create(
            title='The Sign of the Four',
            author=self.author,
            isbn='978-0140439076',
            genre='Mystery & Thriller',
            total_copies=1,
            available_copies=0
        )

    def test_home_page_loads_and_displays_catalog(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A Study in Scarlet')
        self.assertContains(response, 'Arthur Conan Doyle')
        self.assertContains(response, 'Mystery &amp; Thriller')

    def test_api_search_endpoint(self):
        response = self.client.get(reverse('api_books_search') + '?q=Scarlet')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['title'], 'A Study in Scarlet')

    def test_issue_book_decreases_copies_and_sets_14_day_due_date(self):
        self.client.login(username='staff_test', password='password123')

        response = self.client.post(reverse('issue_book'), {
            'member': self.member.id,
            'book': self.book_available.id,
            'due_days': 14,
            'notes': 'Test issue'
        })
        self.assertEqual(response.status_code, 302)  # Redirects on success

        # Verify book copy decreased
        self.book_available.refresh_from_db()
        self.assertEqual(self.book_available.available_copies, 1)

        # Verify circulation record created
        record = CirculationRecord.objects.get(book=self.book_available, member=self.member)
        self.assertEqual(record.status, 'ISSUED')
        expected_due_date = timezone.now().date() + timedelta(days=14)
        self.assertEqual(record.due_date, expected_due_date)

    def test_prevent_issuing_book_when_zero_copies(self):
        self.client.login(username='staff_test', password='password123')

        response = self.client.post(reverse('issue_book'), {
            'member': self.member.id,
            'book': self.book_empty.id,
            'due_days': 14,
            'notes': 'Should fail'
        })
        # Form error should be raised
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select a valid choice')

        # Verify copies stayed at 0
        self.book_empty.refresh_from_db()
        self.assertEqual(self.book_empty.available_copies, 0)
        self.assertFalse(CirculationRecord.objects.filter(book=self.book_empty).exists())

    def test_return_book_increases_copies_and_calculates_on_time_fine(self):
        self.client.login(username='staff_test', password='password123')

        # Issue book first
        record = CirculationRecord.objects.create(
            book=self.book_available,
            member=self.member,
            issue_date=timezone.now().date() - timedelta(days=5),
            due_date=timezone.now().date() + timedelta(days=9),
            status='ISSUED'
        )
        self.book_available.available_copies = 1
        self.book_available.save()

        # Return book today (on time)
        response = self.client.post(reverse('return_book'), {
            'record_id': record.id,
            'notes': 'Returned on time'
        })
        self.assertEqual(response.status_code, 302)

        # Verify available copies increased
        self.book_available.refresh_from_db()
        self.assertEqual(self.book_available.available_copies, 2)

        # Verify record updated
        record.refresh_from_db()
        self.assertEqual(record.status, 'RETURNED')
        self.assertEqual(record.fine_amount, Decimal('0.00'))
        self.assertTrue(record.fine_paid)

    def test_return_book_calculates_overdue_fines(self):
        self.client.login(username='staff_test', password='password123')

        # Issue book with due date 5 days ago
        today = timezone.now().date()
        record = CirculationRecord.objects.create(
            book=self.book_available,
            member=self.member,
            issue_date=today - timedelta(days=19),
            due_date=today - timedelta(days=5),
            status='OVERDUE'
        )
        self.book_available.available_copies = 1
        self.book_available.save()

        # Process return with fine collected
        response = self.client.post(reverse('return_book'), {
            'record_id': record.id,
            'fine_collected': 'on',
            'notes': '5 days overdue paid'
        })
        self.assertEqual(response.status_code, 302)

        record.refresh_from_db()
        self.assertEqual(record.status, 'RETURNED')
        # 5 days * $1.00 = $5.00
        self.assertEqual(record.fine_amount, Decimal('5.00'))
        self.assertTrue(record.fine_paid)

        # Available copies increased
        self.book_available.refresh_from_db()
        self.assertEqual(self.book_available.available_copies, 2)

    def test_member_dashboard_shows_borrowed_books_and_history(self):
        self.client.login(username='member_test', password='password123')

        # Create 1 active loan and 1 returned loan
        today = timezone.now().date()
        active = CirculationRecord.objects.create(
            book=self.book_available,
            member=self.member,
            issue_date=today,
            due_date=today + timedelta(days=14),
            status='ISSUED'
        )
        returned = CirculationRecord.objects.create(
            book=self.book_empty,
            member=self.member,
            issue_date=today - timedelta(days=20),
            due_date=today - timedelta(days=6),
            return_date=today - timedelta(days=1),
            status='RETURNED',
            fine_amount=Decimal('5.00'),
            fine_paid=True
        )

        response = self.client.get(reverse('member_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A Study in Scarlet')
        self.assertContains(response, 'The Sign of the Four')
        self.assertContains(response, 'LIB-TEST-001')

import uuid
from datetime import timedelta
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError


class Author(models.Model):
    name = models.CharField(max_length=200, help_text="Full name of the author")
    bio = models.TextField(blank=True, help_text="Author biography")
    nationality = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    photo_url = models.URLField(blank=True, help_text="Direct URL to author photo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def book_count(self):
        return self.books.count()


class Book(models.Model):
    GENRE_CHOICES = [
        ('Fiction', 'Fiction'),
        ('Non-Fiction', 'Non-Fiction'),
        ('Science & Technology', 'Science & Technology'),
        ('Computer Science', 'Computer Science'),
        ('History & Biography', 'History & Biography'),
        ('Philosophy', 'Philosophy'),
        ('Literature & Classics', 'Literature & Classics'),
        ('Business & Economics', 'Business & Economics'),
        ('Fantasy & Sci-Fi', 'Fantasy & Sci-Fi'),
        ('Mystery & Thriller', 'Mystery & Thriller'),
    ]

    title = models.CharField(max_length=255)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='books')
    isbn = models.CharField(max_length=20, unique=True, help_text="10 or 13 digit ISBN number")
    genre = models.CharField(max_length=50, choices=GENRE_CHOICES, default='Fiction')
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True)
    cover_url = models.URLField(blank=True, help_text="Online image URL for cover")
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    publication_year = models.PositiveIntegerField(null=True, blank=True)
    publisher = models.CharField(max_length=200, blank=True)
    language = models.CharField(max_length=50, default='English')
    is_ebook_available = models.BooleanField(default=True)
    ebook_file = models.FileField(upload_to='ebooks/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', 'title']

    def __str__(self):
        return f"{self.title} ({self.isbn})"

    def clean(self):
        if self.available_copies > self.total_copies:
            raise ValidationError({'available_copies': 'Available copies cannot exceed total copies.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_available(self):
        return self.available_copies > 0

    def get_cover_image(self):
        if self.cover_image:
            return self.cover_image.url
        if self.cover_url:
            return self.cover_url
        # Fallback SVG placeholder or default cover
        return f"https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=400&q=80"


class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_profile')
    membership_id = models.CharField(max_length=30, unique=True, blank=True)
    phone = models.CharField(max_length=25, blank=True)
    address = models.TextField(blank=True)
    joined_date = models.DateField(default=timezone.now)
    max_books_allowed = models.PositiveIntegerField(default=5)

    class Meta:
        ordering = ['membership_id']

    def __str__(self):
        full_name = self.user.get_full_name() or self.user.username
        return f"{full_name} ({self.membership_id})"

    def save(self, *args, **kwargs):
        if not self.membership_id:
            # Generate unique membership ID
            unique_part = uuid.uuid4().hex[:6].upper()
            year = timezone.now().year
            self.membership_id = f"LIB-{year}-{unique_part}"
        super().save(*args, **kwargs)

    @property
    def active_borrows(self):
        return self.circulation_records.filter(status='ISSUED')

    @property
    def active_borrows_count(self):
        return self.active_borrows.count()

    @property
    def can_borrow(self):
        return self.active_borrows_count < self.max_books_allowed

    @property
    def unpaid_fines_total(self):
        unpaid = self.circulation_records.filter(fine_paid=False, fine_amount__gt=0)
        return sum(record.fine_amount for record in unpaid)


class CirculationRecord(models.Model):
    STATUS_CHOICES = [
        ('ISSUED', 'Issued / Active'),
        ('RETURNED', 'Returned'),
        ('OVERDUE', 'Overdue'),
    ]

    DAILY_FINE_RATE = Decimal('1.00')  # $1.00 per day overdue

    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name='circulation_records')
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='circulation_records')
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField(blank=True)
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ISSUED')
    fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    fine_paid = models.BooleanField(default=False)
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_by_records')
    return_processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='returned_by_records')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issue_date', '-created_at']

    def __str__(self):
        return f"{self.book.title} -> {self.member.user.username} ({self.status})"

    def clean(self):
        if not self.pk and self.book.available_copies <= 0:
            raise ValidationError({'book': f'Cannot issue "{self.book.title}". Zero copies available.'})

    def save(self, *args, **kwargs):
        # Default due date is 14 days after issue date if not set
        if not self.due_date:
            if not self.issue_date:
                self.issue_date = timezone.now().date()
            self.due_date = self.issue_date + timedelta(days=14)

        # Update status if overdue
        today = timezone.now().date()
        if self.status == 'ISSUED' and today > self.due_date:
            self.status = 'OVERDUE'

        super().save(*args, **kwargs)

    @property
    def is_currently_overdue(self):
        if self.return_date:
            return self.return_date > self.due_date
        return timezone.now().date() > self.due_date

    @property
    def overdue_days(self):
        ref_date = self.return_date or timezone.now().date()
        if ref_date > self.due_date:
            return (ref_date - self.due_date).days
        return 0

    @property
    def estimated_fine(self):
        days = self.overdue_days
        return Decimal(days) * self.DAILY_FINE_RATE

    @property
    def days_remaining(self):
        today = timezone.now().date()
        if self.due_date >= today:
            return (self.due_date - today).days
        return 0

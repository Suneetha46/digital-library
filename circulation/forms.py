from datetime import timedelta
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Book, Author, Member, CirculationRecord


class IssueBookForm(forms.Form):
    member = forms.ModelChoiceField(
        queryset=Member.objects.select_related('user').all(),
        widget=forms.Select(attrs={'class': 'form-select select2-enable', 'id': 'issue-member-select'}),
        help_text="Select an enrolled library member"
    )
    book = forms.ModelChoiceField(
        queryset=Book.objects.filter(available_copies__gt=0).select_related('author'),
        widget=forms.Select(attrs={'class': 'form-select select2-enable', 'id': 'issue-book-select'}),
        help_text="Only books with available copies (> 0) are shown"
    )
    due_days = forms.IntegerField(
        initial=14,
        min_value=1,
        max_value=60,
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'issue-due-days'}),
        help_text="Loan period in days (Standard: 14 days)"
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional loan notes, condition check, etc.'})
    )

    def clean(self):
        cleaned_data = super().clean()
        member = cleaned_data.get('member')
        book = cleaned_data.get('book')

        if member and book:
            # Check availability
            if book.available_copies <= 0:
                raise ValidationError(f'Cannot issue "{book.title}". There are 0 available copies remaining.')

            # Check member quota
            if not member.can_borrow:
                raise ValidationError(
                    f'Member {member.user.get_full_name() or member.user.username} has reached the maximum borrowing limit '
                    f'of {member.max_books_allowed} books. Please return an existing book first.'
                )

            # Check if already holding this book
            already_borrowed = CirculationRecord.objects.filter(
                member=member,
                book=book,
                status__in=['ISSUED', 'OVERDUE']
            ).exists()
            if already_borrowed:
                raise ValidationError(
                    f'Member {member.user.username} already currently holds an active copy of "{book.title}".'
                )

        return cleaned_data


class ReturnBookForm(forms.Form):
    record_id = forms.IntegerField(widget=forms.HiddenInput())
    fine_collected = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'fine_collected_check'}),
        label="Mark fine as settled/collected"
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional return notes, book condition, etc.'})
    )


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            'title', 'author', 'isbn', 'genre', 'description',
            'cover_url', 'cover_image', 'total_copies', 'available_copies',
            'publication_year', 'publisher', 'language', 'is_ebook_available'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. The Pragmatic Programmer'}),
            'author': forms.Select(attrs={'class': 'form-select'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 978-0135957059'}),
            'genre': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Book synopsis...'}),
            'cover_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'total_copies': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'available_copies': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'publication_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2024'}),
            'publisher': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Addison-Wesley'}),
            'language': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. English'}),
            'is_ebook_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_copies')
        avail = cleaned_data.get('available_copies')
        if total is not None and avail is not None and avail > total:
            raise ValidationError({'available_copies': 'Available copies cannot be greater than total copies.'})
        return cleaned_data


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['name', 'bio', 'nationality', 'birth_date', 'photo_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Andy Hunt'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Author biography...'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. American'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'photo_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
        }


class MemberRegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose username'})
    )
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1 (555) 000-0000'})
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Residential address'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create secure password'})
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'})
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('password_confirm')
        if p1 and p2 and p1 != p2:
            raise ValidationError({'password_confirm': 'Passwords do not match.'})
        return cleaned_data

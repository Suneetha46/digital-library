from datetime import timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.utils import timezone

from .models import Book, Author, Member, CirculationRecord
from .forms import (
    IssueBookForm, ReturnBookForm, BookForm, AuthorForm, MemberRegistrationForm
)


def is_staff_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


# -------------------------------------------------------------
# Home & Public Catalog
# -------------------------------------------------------------
def home(request):
    """
    Responsive home page with modern digital library design,
    instant catalog display, search/filter support, and library statistics.
    """
    search_query = request.GET.get('q', '').strip()
    selected_genre = request.GET.get('genre', '').strip()
    availability_filter = request.GET.get('availability', '').strip()

    books = Book.objects.select_related('author').all()

    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__name__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(genre__icontains=search_query)
        )

    if selected_genre:
        books = books.filter(genre__iexact=selected_genre)

    if availability_filter == 'available':
        books = books.filter(available_copies__gt=0)
    elif availability_filter == 'borrowed':
        books = books.filter(available_copies=0)

    # Statistics for portal showcase
    total_books_count = Book.objects.count()
    total_copies_sum = Book.objects.aggregate(total=Sum('total_copies'))['total'] or 0
    available_copies_sum = Book.objects.aggregate(avail=Sum('available_copies'))['avail'] or 0
    active_members_count = Member.objects.count()
    active_loans_count = CirculationRecord.objects.filter(status='ISSUED').count()
    overdue_loans_count = CirculationRecord.objects.filter(
        status='ISSUED', due_date__lt=timezone.now().date()
    ).count()

    # Genres for filtering pills
    all_genres = [g[0] for g in Book.GENRE_CHOICES]

    context = {
        'books': books,
        'search_query': search_query,
        'selected_genre': selected_genre,
        'availability_filter': availability_filter,
        'all_genres': all_genres,
        'total_books_count': total_books_count,
        'total_copies_sum': total_copies_sum,
        'available_copies_sum': available_copies_sum,
        'active_members_count': active_members_count,
        'active_loans_count': active_loans_count,
        'overdue_loans_count': overdue_loans_count,
    }
    return render(request, 'circulation/home.html', context)


def book_detail(request, pk):
    """Detailed book view with availability, metadata, and circulation status."""
    book = get_object_or_404(Book.objects.select_related('author'), pk=pk)
    active_records = book.circulation_records.filter(status='ISSUED').select_related('member__user')
    
    # Related books by same author or genre
    related_books = Book.objects.filter(
        Q(genre=book.genre) | Q(author=book.author)
    ).exclude(pk=book.pk)[:4]

    context = {
        'book': book,
        'active_records': active_records,
        'related_books': related_books,
    }
    return render(request, 'circulation/book_detail.html', context)


# -------------------------------------------------------------
# Staff Circulation Management
# -------------------------------------------------------------
@user_passes_test(is_staff_user, login_url='login')
def staff_circulation_portal(request):
    """
    Staff circulation dashboard showing active loans, overdue alerts,
    loan actions, and circulation history.
    """
    status_filter = request.GET.get('status', 'ISSUED')
    q = request.GET.get('q', '').strip()

    records = CirculationRecord.objects.select_related('book', 'member__user', 'issued_by').all()

    # Update overdue statuses on the fly
    today = timezone.now().date()
    overdue_issued = records.filter(status='ISSUED', due_date__lt=today)
    overdue_issued.update(status='OVERDUE')

    if status_filter and status_filter != 'ALL':
        if status_filter == 'ACTIVE':
            records = records.filter(status__in=['ISSUED', 'OVERDUE'])
        else:
            records = records.filter(status=status_filter)

    if q:
        records = records.filter(
            Q(book__title__icontains=q) |
            Q(book__isbn__icontains=q) |
            Q(member__user__username__icontains=q) |
            Q(member__user__first_name__icontains=q) |
            Q(member__user__last_name__icontains=q) |
            Q(member__membership_id__icontains=q)
        )

    # Counts
    active_count = CirculationRecord.objects.filter(status__in=['ISSUED', 'OVERDUE']).count()
    overdue_count = CirculationRecord.objects.filter(status='OVERDUE').count()
    returned_count = CirculationRecord.objects.filter(status='RETURNED').count()
    total_fines = CirculationRecord.objects.aggregate(total=Sum('fine_amount'))['total'] or Decimal('0.00')

    context = {
        'records': records,
        'status_filter': status_filter,
        'q': q,
        'active_count': active_count,
        'overdue_count': overdue_count,
        'returned_count': returned_count,
        'total_fines': total_fines,
        'return_form': ReturnBookForm(),
    }
    return render(request, 'circulation/staff_circulation_portal.html', context)


@user_passes_test(is_staff_user, login_url='login')
def issue_book(request):
    """
    Staff only: Issue a book to a member.
    Validates available copies > 0, member borrowing limits,
    decrements available_copies atomically, and sets due_date = issue_date + 14 days.
    """
    preset_book_id = request.GET.get('book_id')
    initial_data = {}
    if preset_book_id:
        try:
            book_obj = Book.objects.get(pk=preset_book_id, available_copies__gt=0)
            initial_data['book'] = book_obj
        except Book.DoesNotExist:
            pass

    if request.method == 'POST':
        form = IssueBookForm(request.POST)
        if form.is_valid():
            member = form.cleaned_data['member']
            book = form.cleaned_data['book']
            due_days = form.cleaned_data.get('due_days', 14)
            notes = form.cleaned_data.get('notes', '')

            try:
                with transaction.atomic():
                    # Re-lock and re-verify book copies to prevent race conditions
                    fresh_book = Book.objects.select_for_update().get(pk=book.pk)
                    if fresh_book.available_copies <= 0:
                        messages.error(request, f'Cannot issue "{fresh_book.title}". Zero copies available.')
                        return render(request, 'circulation/issue_book.html', {'form': form})

                    # Decrement available copies
                    fresh_book.available_copies -= 1
                    fresh_book.save()

                    # Calculate due date (default 14 days)
                    issue_date = timezone.now().date()
                    due_date = issue_date + timedelta(days=due_days)

                    # Create circulation record
                    record = CirculationRecord.objects.create(
                        book=fresh_book,
                        member=member,
                        issue_date=issue_date,
                        due_date=due_date,
                        status='ISSUED',
                        issued_by=request.user,
                        notes=notes
                    )

                messages.success(
                    request,
                    f'Successfully issued "{fresh_book.title}" to {member.user.get_full_name() or member.user.username}. '
                    f'Due date is {due_date.strftime("%b %d, %Y")} ({due_days} days).'
                )
                return redirect('staff_circulation_portal')

            except Exception as e:
                messages.error(request, f'Error processing issue: {str(e)}')
    else:
        form = IssueBookForm(initial=initial_data)

    context = {
        'form': form,
    }
    return render(request, 'circulation/issue_book.html', context)


@user_passes_test(is_staff_user, login_url='login')
def return_book(request, pk=None):
    """
    Staff only: Return an issued book.
    Increases available copies atomically, calculates overdue fine if returned past due_date,
    and updates circulation record.
    """
    if request.method == 'POST':
        record_id = pk or request.POST.get('record_id')
        record = get_object_or_404(
            CirculationRecord.objects.select_related('book', 'member__user'),
            pk=record_id
        )

        if record.status == 'RETURNED':
            messages.warning(request, f'Book "{record.book.title}" was already returned on {record.return_date}.')
            return redirect('staff_circulation_portal')

        fine_collected = request.POST.get('fine_collected') == 'on'
        notes = request.POST.get('notes', '')

        try:
            with transaction.atomic():
                return_date = timezone.now().date()
                record.return_date = return_date
                record.return_processed_by = request.user

                # Calculate fine if overdue
                if return_date > record.due_date:
                    days_overdue = (return_date - record.due_date).days
                    fine_amount = Decimal(days_overdue) * record.DAILY_FINE_RATE
                    record.fine_amount = fine_amount
                    record.fine_paid = fine_collected
                    record.status = 'RETURNED'
                    fine_message = f"Overdue by {days_overdue} days. Fine calculated: ${fine_amount:.2f}."
                else:
                    record.fine_amount = Decimal('0.00')
                    record.fine_paid = True
                    record.status = 'RETURNED'
                    fine_message = "Returned on time. No overdue fine."

                if notes:
                    record.notes = f"{record.notes}\nReturn note: {notes}".strip()

                record.save()

                # Atomically increment available copies
                fresh_book = Book.objects.select_for_update().get(pk=record.book.pk)
                fresh_book.available_copies += 1
                if fresh_book.available_copies > fresh_book.total_copies:
                    fresh_book.available_copies = fresh_book.total_copies
                fresh_book.save()

            messages.success(
                request,
                f'Returned "{record.book.title}" from member {record.member.user.get_full_name() or record.member.user.username}. '
                f'{fine_message} Available copies now: {fresh_book.available_copies}.'
            )
        except Exception as e:
            messages.error(request, f'Error returning book: {str(e)}')

        return redirect('staff_circulation_portal')

    # GET request - return preview page
    record = get_object_or_404(
        CirculationRecord.objects.select_related('book', 'member__user'),
        pk=pk
    )
    today = timezone.now().date()
    is_overdue = today > record.due_date
    days_overdue = (today - record.due_date).days if is_overdue else 0
    estimated_fine = Decimal(days_overdue) * record.DAILY_FINE_RATE if is_overdue else Decimal('0.00')

    context = {
        'record': record,
        'today': today,
        'is_overdue': is_overdue,
        'days_overdue': days_overdue,
        'estimated_fine': estimated_fine,
    }
    return render(request, 'circulation/return_book_confirm.html', context)


# -------------------------------------------------------------
# Member Portal & Dashboard
# -------------------------------------------------------------
@login_required
def member_dashboard(request):
    """
    Member Dashboard:
    Displays member profile, currently borrowed books with due dates & overdue alerts,
    and complete borrowing history.
    """
    # Ensure Member profile exists
    member, created = Member.objects.get_or_create(user=request.user)

    # Active borrowed books
    today = timezone.now().date()
    active_borrows = CirculationRecord.objects.filter(
        member=member,
        status__in=['ISSUED', 'OVERDUE']
    ).select_related('book', 'book__author').order_by('due_date')

    # Borrowing history (returned books)
    borrowing_history = CirculationRecord.objects.filter(
        member=member,
        status='RETURNED'
    ).select_related('book', 'book__author').order_by('-return_date')

    # Summary metrics
    active_count = active_borrows.count()
    overdue_count = sum(1 for b in active_borrows if today > b.due_date)
    unpaid_fines = sum(r.fine_amount for r in borrowing_history if not r.fine_paid and r.fine_amount > 0)
    total_books_read = borrowing_history.count()

    context = {
        'member': member,
        'active_borrows': active_borrows,
        'borrowing_history': borrowing_history,
        'today': today,
        'active_count': active_count,
        'overdue_count': overdue_count,
        'unpaid_fines': unpaid_fines,
        'total_books_read': total_books_read,
    }
    return render(request, 'circulation/member_dashboard.html', context)


# -------------------------------------------------------------
# Book & Author Management (Staff)
# -------------------------------------------------------------
@user_passes_test(is_staff_user, login_url='login')
def add_book(request):
    """Staff only: Add new book to catalog."""
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" added to catalog successfully.')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm()

    return render(request, 'circulation/book_form.html', {'form': form, 'title': 'Add New Book'})


@user_passes_test(is_staff_user, login_url='login')
def edit_book(request, pk):
    """Staff only: Edit existing book."""
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, f'Book "{book.title}" updated successfully.')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)

    return render(request, 'circulation/book_form.html', {'form': form, 'title': f'Edit "{book.title}"', 'book': book})


@user_passes_test(is_staff_user, login_url='login')
def add_author(request):
    """Staff only: Add new author."""
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            author = form.save()
            messages.success(request, f'Author "{author.name}" added successfully.')
            return redirect('home')
    else:
        form = AuthorForm()

    return render(request, 'circulation/author_form.html', {'form': form, 'title': 'Add Author'})


# -------------------------------------------------------------
# Authentication & Registration
# -------------------------------------------------------------
def member_register(request):
    """Public: Register as a library member."""
    if request.user.is_authenticated:
        return redirect('member_dashboard')

    if request.method == 'POST':
        form = MemberRegistrationForm(request.POST)
        if form.is_valid():
            # Create user
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name']
            )
            # Create member profile
            Member.objects.create(
                user=user,
                phone=form.cleaned_data.get('phone', ''),
                address=form.cleaned_data.get('address', '')
            )
            login(request, user)
            messages.success(request, f'Welcome to the Digital Library, {user.first_name}! Your membership account is active.')
            return redirect('member_dashboard')
    else:
        form = MemberRegistrationForm()

    return render(request, 'circulation/register.html', {'form': form})


def user_login_view(request):
    """Login view for both Staff and Members."""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('staff_circulation_portal')
        return redirect('member_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if user.is_staff:
                return redirect('staff_circulation_portal')
            return redirect('member_dashboard')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = AuthenticationForm()

    return render(request, 'circulation/login.html', {'form': form})


def user_logout_view(request):
    """Logout view."""
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('home')


# -------------------------------------------------------------
# Instant JSON Search API
# -------------------------------------------------------------
def api_books_search(request):
    """JSON API endpoint for instant search / autocomplete."""
    query = request.GET.get('q', '').strip()
    genre = request.GET.get('genre', '').strip()

    books = Book.objects.select_related('author').all()
    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__name__icontains=query) |
            Q(isbn__icontains=query) |
            Q(genre__icontains=query)
        )
    if genre:
        books = books.filter(genre__iexact=genre)

    data = [
        {
            'id': b.id,
            'title': b.title,
            'author': b.author.name,
            'isbn': b.isbn,
            'genre': b.genre,
            'available_copies': b.available_copies,
            'total_copies': b.total_copies,
            'is_available': b.is_available,
            'cover_image': b.get_cover_image(),
            'url': f"/books/{b.id}/"
        }
        for b in books[:30]
    ]
    return JsonResponse({'results': data})

from decimal import Decimal
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Author, Book, Member, CirculationRecord


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('name', 'nationality', 'birth_date', 'books_count', 'created_at')
    search_fields = ('name', 'bio', 'nationality')
    list_filter = ('nationality',)

    def books_count(self, obj):
        return obj.books.count()
    books_count.short_description = "Books in Library"


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'genre', 'isbn', 'availability_badge',
        'available_copies', 'total_copies', 'is_ebook_available'
    )
    list_filter = ('genre', 'is_ebook_available', 'publication_year')
    search_fields = ('title', 'author__name', 'isbn', 'publisher')
    list_editable = ('available_copies', 'total_copies')

    def availability_badge(self, obj):
        if obj.available_copies > 0:
            return format_html(
                '<span style="background-color:#198754; color:white; padding:3px 8px; border-radius:12px; font-weight:600;">Available ({})</span>',
                obj.available_copies
            )
        return format_html(
            '<span style="background-color:#dc3545; color:white; padding:3px 8px; border-radius:12px; font-weight:600;">Out of Stock</span>'
        )
    availability_badge.short_description = "Status"


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('membership_id', 'member_name', 'email', 'phone', 'active_loans', 'joined_date')
    search_fields = ('membership_id', 'user__username', 'user__first_name', 'user__last_name', 'user__email', 'phone')
    list_filter = ('joined_date',)

    def member_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    member_name.short_description = "Member Name"

    def email(self, obj):
        return obj.user.email
    email.short_description = "Email"

    def active_loans(self, obj):
        count = obj.active_borrows_count
        return format_html('<b>{}/{}</b>', count, obj.max_books_allowed)
    active_loans.short_description = "Active Borrows"


@admin.register(CirculationRecord)
class CirculationRecordAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'book_title', 'member_name', 'issue_date', 'due_date',
        'return_date', 'status_badge', 'fine_amount', 'fine_paid'
    )
    list_filter = ('status', 'fine_paid', 'issue_date', 'due_date')
    search_fields = (
        'book__title', 'book__isbn',
        'member__user__username', 'member__user__first_name',
        'member__user__last_name', 'member__membership_id'
    )
    actions = ['mark_returned_today', 'settle_fines']

    def book_title(self, obj):
        return obj.book.title
    book_title.short_description = "Book"

    def member_name(self, obj):
        return f"{obj.member.user.get_full_name() or obj.member.user.username} ({obj.member.membership_id})"
    member_name.short_description = "Member"

    def status_badge(self, obj):
        colors = {
            'ISSUED': '#0d6efd',
            'RETURNED': '#198754',
            'OVERDUE': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:12px; font-weight:600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = "Status"

    @admin.action(description="Mark selected as returned today (and increment book copy)")
    def mark_returned_today(self, request, queryset):
        today = timezone.now().date()
        for record in queryset:
            if record.status != 'RETURNED':
                record.return_date = today
                record.status = 'RETURNED'
                if today > record.due_date:
                    days = (today - record.due_date).days
                    record.fine_amount = Decimal(days) * record.DAILY_FINE_RATE
                record.save()
                # Increment available copies
                b = record.book
                b.available_copies = min(b.available_copies + 1, b.total_copies)
                b.save()
        self.message_user(request, "Selected circulation records were marked as returned.")

    @admin.action(description="Mark fine as paid for selected records")
    def settle_fines(self, request, queryset):
        queryset.update(fine_paid=True)
        self.message_user(request, "Selected fines marked as paid.")

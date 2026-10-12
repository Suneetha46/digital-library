from django.urls import path
from . import views

urlpatterns = [
    # Public & Catalog
    path('', views.home, name='home'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    path('api/books/search/', views.api_books_search, name='api_books_search'),

    # Member Portal
    path('dashboard/', views.member_dashboard, name='member_dashboard'),
    path('register/', views.member_register, name='register'),
    path('login/', views.user_login_view, name='login'),
    path('logout/', views.user_logout_view, name='logout'),

    # Staff Circulation Management
    path('staff/circulation/', views.staff_circulation_portal, name='staff_circulation_portal'),
    path('staff/issue/', views.issue_book, name='issue_book'),
    path('staff/return/', views.return_book, name='return_book'),
    path('staff/return/<int:pk>/', views.return_book, name='return_book_confirm'),
    path('staff/books/add/', views.add_book, name='add_book'),
    path('staff/books/<int:pk>/edit/', views.edit_book, name='edit_book'),
    path('staff/authors/add/', views.add_author, name='add_author'),
]

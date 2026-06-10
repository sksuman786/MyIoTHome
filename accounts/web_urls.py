"""
HTML page routes for the accounts app.
"""

from django.urls import path
from accounts.views import LoginPageView, RegisterPageView, logout_view

urlpatterns = [
    path('login/', LoginPageView.as_view(), name='login_page'),
    path('register/', RegisterPageView.as_view(), name='register_page'),
    path('logout/', logout_view, name='logout_page'),
]

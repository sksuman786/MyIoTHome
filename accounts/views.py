"""
Views for user authentication and account management.
"""

from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, login, logout
from django.utils.timezone import now, timedelta
from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import redirect
from django.views.generic import FormView
from django import forms

from django.conf import settings

from accounts.models import User, APIKey, PasswordResetToken, LoginLog
from accounts.serializers import (
    UserSerializer, UserDetailSerializer, RegisterSerializer, LoginSerializer,
    ChangePasswordSerializer, APIKeySerializer, APIKeyCreateSerializer, LoginLogSerializer
)
import secrets
import string


class RegisterView(generics.CreateAPIView):
    """User registration endpoint."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = User.objects.get(email=request.data['email'])
        # Account is created inactive and requires admin activation
        return Response({
            'message': 'User registered successfully. Your account will be activated by an administrator.',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    # Email verification removed: accounts are manually activated by admin.


class LoginForm(forms.Form):
    """Form used for HTML login pages."""
    email = forms.EmailField(label='Email Address')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    remember = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(self.request, username=email, password=password)
            if user is None:
                user_lookup = User.objects.filter(email__iexact=email).first()
                if user_lookup:
                    user = authenticate(self.request, username=user_lookup.username, password=password)

            if user is None:
                raise forms.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise forms.ValidationError('This account is inactive. Please contact support.')

            cleaned_data['user'] = user

        return cleaned_data


class LoginPageView(FormView):
    """Render the login page and handle browser-based login redirects."""
    template_name = 'accounts/login.html'
    form_class = LoginForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', self.request.POST.get('next', '/dashboard/'))
        return context

    def form_valid(self, form):
        user = form.cleaned_data['user']
        login(self.request, user)

        if not form.cleaned_data.get('remember'):
            self.request.session.set_expiry(0)

        next_url = self.request.POST.get('next') or self.request.GET.get('next') or '/dashboard/'
        if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={self.request.get_host()}, require_https=self.request.is_secure()):
            next_url = '/dashboard/'

        return redirect(next_url)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class RegisterForm(forms.ModelForm):
    """Form used for browser-based account registration."""
    password = forms.CharField(label='Password', widget=forms.PasswordInput, min_length=8)
    password_confirm = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    terms = forms.BooleanField(label='I agree to the Terms and Conditions', required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with that email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Passwords do not match.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class RegisterPageView(FormView):
    """Render the registration page and create a new user through the browser."""
    template_name = 'accounts/register.html'
    form_class = RegisterForm

    def form_valid(self, form):
        user = form.save()
        # Create user as inactive; admin will manually activate known users.
        user.is_active = False
        user.save()
        return redirect('/accounts/login/')

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


def logout_view(request):
    logout(request)
    return redirect('/accounts/login/')


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view with JWT tokens."""
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Log login
            LoginLog.objects.create(
                user=user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                is_successful=True
            )
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserDetailSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for user management."""
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile."""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password."""
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'error': 'Invalid old password'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({'message': 'Password changed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def update_profile(self, request):
        """Update user profile."""
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def toggle_theme(self, request):
        """Toggle between light and dark mode."""
        user = request.user
        user.theme = 'dark' if user.theme == 'light' else 'light'
        user.save()
        return Response({'theme': user.theme})
    
    @action(detail=False, methods=['get'])
    def login_history(self, request):
        """Get user login history."""
        logs = LoginLog.objects.filter(user=request.user).order_by('-created_at')[:10]
        serializer = LoginLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate_user(self, request, pk=None):
        """Activate user (admin only)."""
        if request.user.role != 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'message': 'User activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate_user(self, request, pk=None):
        """Deactivate user (admin only)."""
        if request.user.role != 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'message': 'User deactivated'})


class APIKeyViewSet(viewsets.ModelViewSet):
    """ViewSet for API Key management."""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role == 'admin':
            return APIKey.objects.all()
        return APIKey.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return APIKeyCreateSerializer
        return APIKeySerializer
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerate API key."""
        api_key = self.get_object()
        
        if api_key.user != request.user and request.user.role != 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        alphabet = string.ascii_letters + string.digits
        new_key = ''.join(secrets.choice(alphabet) for i in range(40))
        while APIKey.objects.filter(key=new_key).exists():
            new_key = ''.join(secrets.choice(alphabet) for i in range(40))
        
        api_key.key = new_key
        api_key.save()
        
        return Response(APIKeySerializer(api_key).data)


    # VerifyEmailView removed — email verification flow disabled.

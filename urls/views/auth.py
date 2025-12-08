from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from urls.forms import RegisterForm

from django.contrib.auth.forms import AuthenticationForm

@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    User login view using AuthenticationForm.
    
    GET: Display login form
    POST: Authenticate and login user
    """
    if request.user.is_authenticated:
        return redirect('urls:dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            
            # Redirect to 'next' parameter or dashboard
            next_url = request.GET.get('next', 'urls:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'urls/login.html', {'form': form})


@require_http_methods(["GET", "POST"])
def register_view(request):
    """
    User registration view
    
    GET: Display registration form
    POST: Validate and create new user
    """
    if request.user.is_authenticated:
        return redirect('urls:dashboard')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request, 
                f'Account created! Welcome, {user.username}!'
            )
            return redirect('urls:dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.capitalize()}: {error}')
    else:
        form = RegisterForm()
    
    return render(request, 'urls/register.html', {'form': form})


@login_required
@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('urls:home')
    
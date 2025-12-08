from django.urls import path, include
from rest_framework.routers import DefaultRouter
from urls.views.shortener import (
    URLViewSet, 
    shorten_url_api, 
    redirect_short_url, 
    home, 
    dashboard
)
from urls.views.auth import (
    login_view, 
    register_view, 
    logout_view
)

router = DefaultRouter()
router.register(r'urls', URLViewSet, basename='url')

app_name = 'urls'

urlpatterns = [
    # Web views
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),

    #Auth views
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),

    # API endpoints
    path('api/', include(router.urls)),
    path('api/shorten/', shorten_url_api, name='shorten-api'),
    
    # Redirect must be last to catch all short codes
    path('<str:short_code>/', redirect_short_url, name='redirect'),
]
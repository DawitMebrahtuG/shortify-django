from django.urls import path, include
from rest_framework.routers import DefaultRouter
from urls.views.shortener import (
    URLViewSet, 
    shorten_url_api, 
    redirect_short_url, 
    home, 
    dashboard,
    urls_list,
    qrcodes_list,
    QRCodeCreateView
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
    path('links/', urls_list, name='url_list'),  
    path('qrcodes/', qrcodes_list, name='qrcodes_list'),

    #Auth views
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),

    # API endpoints
    path('api/', include(router.urls)),
    path('api/shorten/', shorten_url_api, name='shorten-api'),
    path('api/qrcode/create/', QRCodeCreateView.as_view(), name='qrcode-create'),
    
    # Redirect must be last to catch all short codes
    path('<str:short_code>/', redirect_short_url, name='redirect'),
]
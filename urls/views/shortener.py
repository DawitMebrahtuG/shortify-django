import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Count
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
import user_agents

from urls.models import URL, Click, QRCode
from urls.serializers import (
    URLSerializer, 
    URLCreateSerializer, 
    URLAnalyticsSerializer,
    FullDashboardSerializer,
    DashboardStatsSerializer,
    URLPerformanceSerializer,
    ReferrerSerializer,
    RecentClickSerializer,
    ClickTimeSeriesSerializer,
    ClickHourlySerializer,
)
from urls.services.qrcode import generate_qr_code
from urls.services.analytics import get_url_analytics
from urls.services.dashboard import DashboardService
from urls.utils import paginate_queryset

def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def parse_user_agent(user_agent_string):
    """Parse user agent string to extract browser, device, and OS."""
    ua = user_agents.parse(user_agent_string)
    return {
        'browser': f"{ua.browser.family} {ua.browser.version_string}",
        'device': ua.device.family,
        'os': f"{ua.os.family} {ua.os.version_string}"
    }


def redirect_short_url(request, short_code):
    """
    Redirect to the original URL and track analytics.
    
    Args:
        short_code: The unique short code for the URL
    """
    url_obj: URL = get_object_or_404(URL, short_code=short_code)
    
    # Check if URL is active and not expired
    if not url_obj.is_active:
        return render(request, 'urls/error.html', {
            'message': 'This short URL has been deactivated.',
            'status_code': 410
        }, status=410)
    
    if url_obj.is_expired():
        return render(request, 'urls/error.html', {
            'message': 'This short URL has expired.',
            'status_code': 410
        }, status=410)
    
    # Track the click
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    parsed_ua = parse_user_agent(user_agent_string)
    
    Click.create_click(
        url=url_obj,
        ip_address=get_client_ip(request),
        referrer=request.META.get('HTTP_REFERER'),
        user_agent=user_agent_string,
        browser=parsed_ua['browser'],
        device=parsed_ua['device'],
        os=parsed_ua['os']
    )
    
    return redirect(url_obj.original_url)


@login_required
def dashboard(request):
    service = DashboardService(request.user)
    context = service.get_full_dashboard_context()
    context['clicks_over_time'] = json.dumps(
        context['clicks_over_time'], 
        cls=DjangoJSONEncoder
    )
    context['active_page'] = 'dashboard'

    return render(request, 'urls/dashboard.html', context)


def home(request):
    return render(request, 'urls/home.html')


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def shorten_url_api(request):
    """
    API endpoint to shorten a URL.
    
    POST data:
        - original_url (required): The URL to shorten
        - expires_at (optional): Expiration date/time
    
    Returns:
        - short_code: The generated short code
        - short_url: The full shortened URL
        - original_url: The original URL
    """
    serializer = URLCreateSerializer(data=request.data)
    
    if serializer.is_valid():
        url_obj: URL = serializer.save(
            user=request.user if request.user.is_authenticated else None
        )
        # Build full short URL
        short_url = request.build_absolute_uri(url_obj.get_absolute_url())
        
        return Response(
            {
                'success': True,
                'short_code': url_obj.short_code,
                'short_url': short_url,
                'original_url': url_obj.original_url,
                'expires_at': url_obj.expires_at,
            }, 
            status=status.HTTP_201_CREATED
        )
    return Response(
        {
            'success': False,
            'errors': serializer.errors
        }, 
        status=status.HTTP_400_BAD_REQUEST
    )


@login_required
def urls_list(request):
    queryset = (
        URL.objects
        .filter(user=request.user)
        .annotate(click_count=Count("clicks"))
        .only("id", "original_url", "short_code", "created_at", "is_active")
        .order_by("-created_at")
    )

    urls = paginate_queryset(request, queryset, per_page=5)

    return render(
        request,
        "urls/url_list.html",
        {
            "urls": urls,
            "active_page": "urls",
        },
    )


@login_required
def qrcodes_list(request):
    queryset = (
        QRCode.objects
        .filter(url__user=request.user)
        .select_related("url")
        .only("id", "created_at", "url__id", "url__short_code")
        .order_by("-created_at")
    )

    qrcodes = paginate_queryset(request, queryset, per_page=12)

    user_urls = (
        URL.objects
        .filter(user=request.user, is_active=True)
        .only("id", "short_code", "original_url")
        .order_by("-created_at")[:50]
    )

    return render(
        request,
        "urls/qrcode_list.html",
        {
            "qrcodes": qrcodes,
            "user_urls": user_urls,
            "active_page": "qrcodes",
        },
    )


class QRCodeCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        short_code = request.data.get('url_short_code')
        name = request.data.get('name', '')
        
        try:
            url = URL.objects.get(short_code=short_code, user=request.user)
        except URL.DoesNotExist:
            return Response({'detail': 'URL not found'}, status=404)
        
        qr = QRCode.objects.create(url=url, name=name)
        return Response({
            'id': qr.id,
            'name': qr.name,
            'short_code': url.short_code
        }, status=201)


class URLViewSet(viewsets.ModelViewSet):
    """
    ViewSet for URL shortening API.
    
    Provides CRUD operations and analytics for shortened URLs.
    """
    queryset = URL.objects.all()
    serializer_class = URLSerializer
    lookup_field = 'short_code'
    
    def get_permissions(self):
        """
        Allow anyone to create URLs, but only authenticated users 
        can view/manage their own URLs.
        """
        if self.action == 'create':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return URL.objects.filter(user=self.request.user)
        return URL.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return URLCreateSerializer
        return URLSerializer
    
    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, short_code=None):
        url_obj = self.get_object()
        data = get_url_analytics(url_obj)
        return Response(URLAnalyticsSerializer(data).data)

    @action(detail=True, methods=['get'])
    def qrcode(self, request, short_code=None):
        url_obj = self.get_object()
        short_url = request.build_absolute_uri(url_obj.get_absolute_url())
        img_bytes = generate_qr_code(short_url)
        return HttpResponse(img_bytes, content_type='image/png')

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard_full(self, request):
        """Get complete dashboard analytics data."""
        service = DashboardService(request.user)
        data = service.get_full_dashboard_context()
        data['stats'] = data['stats'].__dict__ # Convert dataclass to dict for serialization
        return Response(FullDashboardSerializer(data).data)

    @action(detail=False, methods=['get'], url_path='dashboard/stats')
    def dashboard_stats(self, request):
        """Get core dashboard statistics."""
        service = DashboardService(request.user)
        stats = service.get_stats()
        return Response(DashboardStatsSerializer(stats.__dict__).data)
    
    @action(detail=False, methods=['get'], url_path='dashboard/top-urls')
    def dashboard_top_urls(self, request):
        """Get top performing URLs by click count."""
        limit = int(request.query_params.get('limit', 10))
        service = DashboardService(request.user)
        data = service.get_top_urls(limit=limit)
        return Response(URLPerformanceSerializer(data, many=True).data)
    
    @action(detail=False, methods=['get'], url_path='dashboard/recent-urls')
    def dashboard_recent_urls(self, request):
        """Get most recently created URLs."""
        limit = int(request.query_params.get('limit', 5))
        service = DashboardService(request.user)
        data = service.get_recent_urls(limit=limit)
        return Response(URLPerformanceSerializer(data, many=True).data)
    
    @action(detail=False, methods=['get'], url_path='dashboard/clicks-over-time')
    def dashboard_clicks_over_time(self, request):
        """Get click counts by date for the last N days."""
        days = int(request.query_params.get('days', 30))
        service = DashboardService(request.user)
        data = service.get_clicks_over_time(days=days)
        return Response(ClickTimeSeriesSerializer(data, many=True).data)
    
    @action(detail=False, methods=['get'], url_path='dashboard/clicks-by-hour')
    def dashboard_clicks_by_hour(self, request):
        """Get click distribution by hour of day."""
        days = int(request.query_params.get('days', 7))
        service = DashboardService(request.user)
        data = service.get_clicks_by_hour(days=days)
        return Response(ClickHourlySerializer(data, many=True).data)
    
    @action(detail=False, methods=['get'], url_path='dashboard/devices')
    def dashboard_devices(self, request):
        """Get click counts by device type."""
        service = DashboardService(request.user)
        data = service.get_device_breakdown()
        return Response(data)
    
    @action(detail=False, methods=['get'], url_path='dashboard/browsers')
    def dashboard_browsers(self, request):
        """Get click counts by browser."""
        service = DashboardService(request.user)
        data = service.get_browser_breakdown()
        return Response(data)
    
    @action(detail=False, methods=['get'], url_path='dashboard/os')
    def dashboard_os(self, request):
        """Get click counts by operating system."""
        service = DashboardService(request.user)
        data = service.get_os_breakdown()
        return Response(data)
    
    @action(detail=False, methods=['get'], url_path='dashboard/referrers')
    def dashboard_referrers(self, request):
        """Get top referrer sources."""
        limit = int(request.query_params.get('limit', 10))
        service = DashboardService(request.user)
        data = service.get_top_referrers(limit=limit)
        return Response(ReferrerSerializer(data, many=True).data)
    
    @action(detail=False, methods=['get'], url_path='dashboard/recent-clicks')
    def dashboard_recent_clicks(self, request):
        """Get recent click activity feed."""
        limit = int(request.query_params.get('limit', 20))
        service = DashboardService(request.user)
        data = service.get_recent_clicks(limit=limit)
        return Response(RecentClickSerializer(data, many=True).data)

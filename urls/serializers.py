from rest_framework import serializers
from django.contrib.auth.models import User
from .models import URL, Click


class URLSerializer(serializers.ModelSerializer):    
    click_count = serializers.IntegerField(source='get_click_count', read_only=True)
    short_url = serializers.CharField(source='get_absolute_url', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = URL
        fields = [
            'id', 
            'original_url', 
            'short_code', 
            'short_url',
            'created_at', 
            'updated_at',
            'expires_at',
            'is_active',
            'is_expired',
            'click_count'
        ]
        read_only_fields = ['id', 'short_code', 'created_at', 'updated_at']
    
    def validate_original_url(self, value):
        # Validate that the URL starts with http:// or https://
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError(
                "URL must start with http:// or https://"
            )
        return value


class URLCreateSerializer(serializers.ModelSerializer):    
    class Meta:
        model = URL
        fields = ['original_url', 'expires_at']
    
    def validate_original_url(self, value):
        # Validate that the URL starts with http:// or https://
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError(
                "URL must start with http:// or https://"
            )
        return value


class ClickSerializer(serializers.ModelSerializer):
    class Meta:
        model = Click
        fields = [
            'id',
            'timestamp',
            'ip_address',
            'referrer',
            'browser',
            'device',
            'os'
        ]


class URLAnalyticsSerializer(serializers.Serializer):
    total_clicks = serializers.IntegerField()
    unique_ips = serializers.IntegerField()
    top_referrers = serializers.ListField()
    browsers = serializers.DictField()
    devices = serializers.DictField()
    operating_systems = serializers.DictField()
    clicks_over_time = serializers.ListField()
    recent_clicks = ClickSerializer(many=True)


class DashboardStatsSerializer(serializers.Serializer):
    total_urls = serializers.IntegerField()
    active_urls = serializers.IntegerField()
    expired_urls = serializers.IntegerField()
    total_clicks = serializers.IntegerField()
    unique_visitors = serializers.IntegerField()
    clicks_today = serializers.IntegerField()
    clicks_this_week = serializers.IntegerField()
    clicks_this_month = serializers.IntegerField()


class URLPerformanceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    short_code = serializers.CharField()
    original_url = serializers.URLField()
    created_at = serializers.DateTimeField()
    expires_at = serializers.DateTimeField(allow_null=True)
    is_active = serializers.BooleanField()
    click_count = serializers.IntegerField()
    unique_visitors = serializers.IntegerField(required=False)
    last_clicked = serializers.DateTimeField(allow_null=True, required=False)


class ClickTimeSeriesSerializer(serializers.Serializer):
    date = serializers.CharField()
    count = serializers.IntegerField()


class ClickHourlySerializer(serializers.Serializer):
    hour = serializers.IntegerField()
    count = serializers.IntegerField()


class ReferrerSerializer(serializers.Serializer):
    referrer = serializers.CharField()
    count = serializers.IntegerField()


class RecentClickSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    timestamp = serializers.DateTimeField()
    ip_address = serializers.CharField(allow_null=True)
    browser = serializers.CharField(allow_null=True)
    device = serializers.CharField(allow_null=True)
    os = serializers.CharField(allow_null=True)
    referrer = serializers.CharField(allow_null=True)
    url_short_code = serializers.CharField()
    url_original = serializers.CharField()


class FullDashboardSerializer(serializers.Serializer):
    stats = DashboardStatsSerializer()
    top_urls = URLPerformanceSerializer(many=True)
    recent_urls = URLPerformanceSerializer(many=True)
    clicks_over_time = ClickTimeSeriesSerializer(many=True)
    clicks_by_hour = ClickHourlySerializer(many=True)
    device_breakdown = serializers.DictField(child=serializers.IntegerField())
    browser_breakdown = serializers.DictField(child=serializers.IntegerField())
    os_breakdown = serializers.DictField(child=serializers.IntegerField())
    top_referrers = ReferrerSerializer(many=True)
    recent_clicks = RecentClickSerializer(many=True)
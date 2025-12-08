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
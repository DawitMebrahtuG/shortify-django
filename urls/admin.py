from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import URL, Click, QRCode


class ClickInline(admin.TabularInline):
    model = Click
    extra = 0
    readonly_fields = ['timestamp', 'ip_address', 'referrer', 'browser', 'device', 'os']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(URL)
class URLAdmin(admin.ModelAdmin):    
    list_display = [
        'short_code', 
        'original_url_truncated', 
        'user',
        'click_count_display',
        'is_active',
        'created_at',
        'expires_at',
        'view_analytics'
    ]
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['short_code', 'original_url', 'user__username']
    readonly_fields = ['short_code', 'created_at', 'updated_at', 'click_count_display']
    date_hierarchy = 'created_at'
    inlines = [ClickInline]
    
    fieldsets = (
        ('URL Information', {
            'fields': ('original_url', 'short_code', 'user')
        }),
        ('Status', {
            'fields': ('is_active', 'expires_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'click_count_display'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queries by annotating with click count."""
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(click_count=Count('clicks'))
        return queryset
    
    def original_url_truncated(self, obj):
        """Display truncated original URL."""
        max_length = 60
        if len(obj.original_url) > max_length:
            return obj.original_url[:max_length] + '...'
        return obj.original_url
    original_url_truncated.short_description = 'Original URL'
    
    def click_count_display(self, obj):
        """Display click count with color coding."""
        count = obj.click_count if hasattr(obj, 'click_count') else obj.get_click_count()
        
        if count > 100:
            color = 'green'
        elif count > 10:
            color = 'orange'
        else:
            color = 'gray'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            count
        )
    click_count_display.short_description = 'Clicks'
    click_count_display.admin_order_field = 'click_count'
    
    def view_analytics(self, obj):
        """Link to view detailed analytics."""
        url = reverse('admin:urls_url_change', args=[obj.id])
        return format_html(
            '<a href="{}#clicks-group">View Analytics</a>',
            url
        )
    view_analytics.short_description = 'Analytics'


@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):    
    list_display = [
        'url',
        'timestamp',
        'ip_address',
        'browser',
        'device',
        'os',
        'referrer_truncated'
    ]
    list_filter = ['timestamp', 'browser', 'device', 'os']
    search_fields = ['url__short_code', 'ip_address', 'referrer']
    readonly_fields = [
        'url', 
        'timestamp', 
        'ip_address', 
        'referrer', 
        'user_agent',
        'browser',
        'device',
        'os'
    ]
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """Prevent manual creation of clicks."""
        return False
    
    def referrer_truncated(self, obj):
        """Display truncated referrer."""
        if not obj.referrer:
            return '(direct)'
        max_length = 50
        if len(obj.referrer) > max_length:
            return obj.referrer[:max_length] + '...'
        return obj.referrer
    referrer_truncated.short_description = 'Referrer'


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'url__short_code']
    readonly_fields = ['url', 'created_at', 'fill_color', 'back_color', 'box_size']
    date_hierarchy = 'created_at'

admin.site.site_header = "URL Shortener Administration"
admin.site.site_title = "URL Shortener Admin"
admin.site.index_title = "Welcome to URL Shortener Admin Panel"
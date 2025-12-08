from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import string
import secrets


def generate_short_code(length=6):
    """Generate a random short code for URL shortening."""
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


class URL(models.Model):
    """Stores shortened URLs with optional expiration."""
    
    original_url = models.URLField(max_length=2048)
    short_code = models.CharField(
        max_length=10, 
        unique=True, 
        db_index=True,
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='urls',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Optional expiration date for this URL"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this URL is currently active"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "URL"
        verbose_name_plural = "URLs"
    
    def __str__(self):
        return f"{self.short_code} -> {self.original_url[:50]}"
    
    def save(self, *args, **kwargs):
        """Generate short code if not provided."""
        if not self.short_code:
            # Keep generating until we get a unique code
            while True:
                code = generate_short_code()
                if not URL.objects.filter(short_code=code).exists():
                    self.short_code = code
                    break
        super().save(*args, **kwargs)
    
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def get_click_count(self):
        return self.clicks.count()
    
    def get_absolute_url(self):
        return f"/{self.short_code}/"


class Click(models.Model):
    """Tracks analytics for each click on a shortened URL."""
    
    url = models.ForeignKey(
        URL, 
        on_delete=models.CASCADE, 
        related_name='clicks',
        help_text="The shortened URL that was clicked"
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address of the visitor"
    )
    referrer = models.URLField(
        max_length=2048, 
        null=True, 
        blank=True,
        help_text="Referrer URL (where the visitor came from)"
    )
    user_agent = models.TextField(
        null=True, 
        blank=True,
        help_text="User agent string (browser/device information)"
    )
    # Parsed user agent information
    browser = models.CharField(max_length=100, null=True, blank=True)
    device = models.CharField(max_length=100, null=True, blank=True)
    os = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Click"
        verbose_name_plural = "Clicks"
        indexes = [
            models.Index(fields=['-timestamp', 'url']),
        ]
    
    def __str__(self):
        return f"Click on {self.url.short_code} at {self.timestamp}"
    
    @classmethod
    def create_click(cls, url, ip_address, referrer, user_agent, browser, device, os):
        return cls.objects.create(
            url=url,
            ip_address=ip_address,
            referrer=referrer,
            user_agent=user_agent,
            browser=browser,
            device=device,
            os=os
        )
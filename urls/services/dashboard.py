from __future__ import annotations
from dataclasses import dataclass
from datetime import timedelta, date
from typing import List, Dict, Any, Iterable, Tuple
from collections import OrderedDict

from django.db.models import Count, Q, Max, F
from django.db.models.functions import TruncDate, ExtractHour
from django.utils import timezone
from django.contrib.auth.models import User

from urls.models import URL, Click


@dataclass
class DashboardStats:
    """Core stats for the dashboard."""
    total_urls: int
    active_urls: int
    expired_urls: int
    total_clicks: int
    unique_visitors: int
    clicks_today: int
    clicks_this_week: int
    clicks_this_month: int


class DashboardService:
    """
    Optimized service for generating dashboard analytics.
    - Reduces number of DB queries by using `.aggregate()` and annotated querysets.
    - Fills missing buckets (dates/hours) in Python.
    - Returns consistent, predictable structures: dataclass for stats, lists of dicts for collections.
    """

    DEFAULT_TOP_LIMIT = 10
    DEFAULT_RECENT_LIMIT = 20

    def __init__(self, user: User):
        self.user = user
        self._now = timezone.now()

    @property
    def now(self):
        return self._now

    @property
    def today_start(self):
        return self.now.replace(hour=0, minute=0, second=0, microsecond=0)

    @property
    def week_start(self):
        # Monday-based week start
        return (self.today_start - timedelta(days=self.now.weekday()))

    @property
    def month_start(self):
        return self.today_start.replace(day=1)

    @property
    def _urls_qs(self):
        return URL.objects.filter(user=self.user)

    @property
    def _clicks_qs(self):
        return Click.objects.filter(url__user=self.user)

    def get_stats(self) -> DashboardStats:
        """
        Compute URL counts and click aggregates using as few queries as possible.
        """

        # Get URL aggregates in one query
        url_agg = self._urls_qs.aggregate(
            total_urls=Count('id'),
            active_urls=Count('id', filter=Q(is_active=True) & (Q(expires_at__isnull=True) | Q(expires_at__gt=self.now))),
            expired_urls=Count('id', filter=Q(expires_at__lt=self.now)),
        )

        # Get click aggregates in one query
        clicks_agg = self._clicks_qs.aggregate(
            total_clicks=Count('id'),
            unique_visitors=Count('ip_address', distinct=True),
            clicks_today=Count('id', filter=Q(timestamp__gte=self.today_start)),
            clicks_this_week=Count('id', filter=Q(timestamp__gte=self.week_start)),
            clicks_this_month=Count('id', filter=Q(timestamp__gte=self.month_start)),
        )

        # Return aggregated results as a DashboardStats object
        # ensure values are integers and default to 0 if not present
        return DashboardStats(
            total_urls=int(url_agg.get('total_urls') or 0),
            active_urls=int(url_agg.get('active_urls') or 0),
            expired_urls=int(url_agg.get('expired_urls') or 0),
            total_clicks=int(clicks_agg.get('total_clicks') or 0),
            unique_visitors=int(clicks_agg.get('unique_visitors') or 0),
            clicks_today=int(clicks_agg.get('clicks_today') or 0),
            clicks_this_week=int(clicks_agg.get('clicks_this_week') or 0),
            clicks_this_month=int(clicks_agg.get('clicks_this_month') or 0),
        )

    def get_top_urls(self, limit: int = DEFAULT_TOP_LIMIT) -> List[Dict[str, Any]]:
        """
        Top URLs by click_count. Annotate click_count, unique_visitors, and last_clicked.
        """
        qs = (
            self._urls_qs
            # Add aggregated fields to the queryset: 
            # total clicks, distinct visitors, last click timestamp
            .annotate(
                click_count=Count('clicks'),
                unique_visitors=Count('clicks__ip_address', distinct=True),
                last_clicked=Max('clicks__timestamp'),
            )
            .filter(click_count__gt=0) # filter out urls with no clicks
            .order_by('-click_count')[:limit] # order by click_count descending and limit results
            .values(
                'id', 'short_code', 'original_url', 'created_at', 'expires_at',
                'is_active', 'click_count', 'unique_visitors', 'last_clicked'
            )
        )
        return list(qs)

    def get_recent_urls(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Most recently created URLs with click_count and last_clicked.
        """
        qs = (
            self._urls_qs
            # Add aggregated fields to the queryset: click_count and last_clicked
            .annotate(
                click_count=Count('clicks'),
                last_clicked=Max('clicks__timestamp'),
            )
            .order_by('-created_at')[:limit]
            .values(
                'id', 'short_code', 'original_url', 'created_at', 'expires_at',
                'is_active', 'click_count', 'last_clicked'
            )
        )
        return list(qs)

    def get_clicks_over_time(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Returns a list of dicts with 'date' (ISO) and 'count' for each day in the range.
        """
        start = (self.now - timedelta(days=days)).date()
        end = self.now.date()

        qs = (
            self._clicks_qs
            .filter(timestamp__date__gte=start)
            .annotate(day=TruncDate('timestamp')) # Truncate timestamp to date (group by day)
            .values('day')
            .annotate(count=Count('id')) # Count clicks per day
            .order_by('day')
        )

        date_counts = {row['day']: row['count'] for row in qs} # Map each day to its click count
        results: List[Dict[str, Any]] = []
        curr = start
        while curr <= end:
            # Append dict with ISO date and click count (default 0 if missing)
            results.append({'date': curr.isoformat(), 'count': int(date_counts.get(curr, 0))})
            curr = curr + timedelta(days=1)

        return results

    def get_clicks_by_hour(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Returns click counts for each hour of day (0..23) aggregated across the last `days`.
        """
        start_dt = self.now - timedelta(days=days)
        qs = (
            self._clicks_qs
            .filter(timestamp__gte=start_dt)
            .annotate(hour_of_day=ExtractHour('timestamp')) # Extract hour from timestamp (0-23)
            .values('hour_of_day')
            .annotate(count=Count('id')) # Count clicks per hour
            .order_by('hour_of_day')
        )

        # Map each hour to its click count
        hour_counts = {int(row['hour_of_day']): int(row['count']) for row in qs}

        # Ensure 0-23 coverage
        return [{'hour': h, 'count': hour_counts.get(h, 0)} for h in range(24)]

    def _aggregate_field(self, field: str, limit: int = DEFAULT_TOP_LIMIT) -> OrderedDict:
        """
        Generic aggregator for Click fields (device/browser/os/referrer).
        """
        qs = (
            self._clicks_qs
            .exclude(**{f'{field}__isnull': True})
            .exclude(**{field: ''})
            .values(field)
            .annotate(count=Count('id'))
            .order_by('-count')[:limit]
        )
        
        return OrderedDict((row[field], int(row['count'])) for row in qs)

    def get_device_breakdown(self) -> Dict[str, int]:
        return self._aggregate_field('device')

    def get_browser_breakdown(self) -> Dict[str, int]:
        return self._aggregate_field('browser')

    def get_os_breakdown(self) -> Dict[str, int]:
        return self._aggregate_field('os')

    def get_top_referrers(self, limit: int = DEFAULT_TOP_LIMIT) -> List[Dict[str, Any]]:
        qs = (
            self._clicks_qs
            .exclude(referrer__isnull=True)
            .exclude(referrer='')
            .values('referrer') # Group by referrer field
            .annotate(count=Count('id')) # Count number of clicks for each referrer
            .order_by('-count')[:limit]
        )
        return [{'referrer': r['referrer'], 'count': int(r['count'])} for r in qs]

    def get_recent_clicks(self, limit: int = DEFAULT_RECENT_LIMIT) -> List[Dict[str, Any]]:
        """
        Recent clicks with URL info.
        """
        qs = (
            self._clicks_qs
            .select_related('url')
            .order_by('-timestamp')[:limit]
            .values(
                'id', 'timestamp', 'ip_address', 'browser', 'device', 'os',
                'referrer', url_short_code=F('url__short_code'), url_original=F('url__original_url')
            )
        )

        # Build list of dics with click + url info
        return [
            {
                'id': row['id'],
                'timestamp': row['timestamp'],
                'ip_address': row['ip_address'],
                'browser': row['browser'],
                'device': row['device'],
                'os': row['os'],
                'referrer': row['referrer'],
                'url_short_code': row.get('url_short_code'),
                'url_original': row.get('url_original'),
            }
            for row in qs
        ]

    def get_full_dashboard_context(self) -> Dict[str, Any]:
        """
        Build and return the full dashboard context.

        Aggregates multiple analytics components including:
        - Overall stats
        - Top and recent URLs
        - Clicks over time (daily)
        - Clicks by hour (0–23)
        - Device, browser, and OS breakdowns
        - Top referrers
        - Recent clicks with details

        """
        stats = self.get_stats()
        context = {
            'stats': stats,
            'top_urls': self.get_top_urls(),
            'recent_urls': self.get_recent_urls(),
            'clicks_over_time': self.get_clicks_over_time(),
            'clicks_by_hour': self.get_clicks_by_hour(),
            'device_breakdown': self.get_device_breakdown(),
            'browser_breakdown': self.get_browser_breakdown(),
            'os_breakdown': self.get_os_breakdown(),
            'top_referrers': self.get_top_referrers(),
            'recent_clicks': self.get_recent_clicks(),
        }
        return context
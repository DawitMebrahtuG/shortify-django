from datetime import timedelta
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone


def _aggregate_field(clicks, field):
    """Aggregate click counts for a given field."""
    cleaned = (
        clicks.exclude(**{f"{field}__isnull": True})
        .exclude(**{field: ""})
    )
    return dict(
        cleaned.values_list(field).annotate(count=Count("id"))
    )


def get_url_analytics(url_obj):
    """Compute analytics for a shortened URL."""
    clicks = url_obj.clicks.all()

    total_clicks = clicks.count()
    unique_ips = (
        clicks.exclude(ip_address__isnull=True)
        .exclude(ip_address="")
        .values("ip_address")
        .distinct()
        .count()
    )

    top_referrers = list(
        clicks.exclude(referrer__isnull=True)
        .exclude(referrer="")
        .values("referrer")
        .annotate(count=Count("id"))
        .order_by("-count")[:10]
    )

    browsers = _aggregate_field(clicks, "browser")
    devices = _aggregate_field(clicks, "device")
    operating_systems = _aggregate_field(clicks, "os")

    thirty_days_ago = timezone.now() - timedelta(days=30)

    clicks_by_date = (
        clicks.filter(timestamp__gte=thirty_days_ago)
        .annotate(date=TruncDate("timestamp"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    clicks_over_time = [
        {"date": item["date"], "count": item["count"]}
        for item in clicks_by_date
    ]

    recent_clicks = clicks.order_by("-timestamp")[:20]

    return {
        "total_clicks": total_clicks,
        "unique_ips": unique_ips,
        "top_referrers": top_referrers,
        "browsers": browsers,
        "devices": devices,
        "operating_systems": operating_systems,
        "clicks_over_time": clicks_over_time,
        "recent_clicks": recent_clicks,
    }

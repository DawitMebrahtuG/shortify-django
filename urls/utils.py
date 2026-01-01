from django.core.paginator import Paginator
from django.http import HttpRequest
from django.db.models import QuerySet


def paginate_queryset(
    request: HttpRequest,
    queryset: QuerySet,
    per_page: int,
):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)

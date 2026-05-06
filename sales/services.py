from django.db.models import Sum, Count

from .models import Sale, SaleItem, SalePayment


def get_total_revenue(start_date, end_date):
    return (
        Sale.objects.filter(
            status=Sale.Status.COMPLETED,
            completed_at__date__gte=start_date,
            completed_at__date__lte=end_date,
        ).aggregate(total=Sum("net_amount"))["total"]
        or 0
    )


def get_revenue_by_payment_method(start_date, end_date):
    return (
        SalePayment.objects.filter(
            sale__status=Sale.Status.COMPLETED,
            sale__completed_at__date__gte=start_date,
            sale__completed_at__date__lte=end_date,
        )
        .values("method")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )


def get_sales_by_user(start_date, end_date):
    return (
        Sale.objects.filter(
            status=Sale.Status.COMPLETED,
            completed_at__date__gte=start_date,
            completed_at__date__lte=end_date,
        )
        .values("user__first_name", "user__last_name", "user__email")
        .annotate(total_revenue=Sum("net_amount"), sale_count=Count("id"))
        .order_by("-total_revenue")
    )


def get_top_selling_items(start_date, end_date):
    return (
        SaleItem.objects.filter(
            sale__status=Sale.Status.COMPLETED,
            sale__completed_at__date__gte=start_date,
            sale__completed_at__date__lte=end_date,
        )
        .values("product_name_snapshot")
        .annotate(total_quantity=Sum("quantity"), total_revenue=Sum("total_price"))
        .order_by("-total_quantity")[:10]
    )


def get_total_discounts(start_date, end_date):
    return (
        Sale.objects.filter(
            status=Sale.Status.COMPLETED,
            completed_at__date__gte=start_date,
            completed_at__date__lte=end_date,
        ).aggregate(total=Sum("discount_amount"))["total"]
        or 0
    )

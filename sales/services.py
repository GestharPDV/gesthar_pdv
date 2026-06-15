from decimal import Decimal

from django.db.models import (
    Sum, Count, Avg, F, ExpressionWrapper, DecimalField, Value, Subquery, OuterRef,
)
from django.db.models.functions import Coalesce, TruncDate

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


def get_financial_indicators(start_date, end_date):
    from product.models import ProductSupplier

    base_qs = Sale.objects.filter(
        status=Sale.Status.COMPLETED,
        completed_at__date__gte=start_date,
        completed_at__date__lte=end_date,
    )

    agg = base_qs.aggregate(
        gross_revenue=Sum("gross_amount"),
        total_discounts=Sum("discount_amount"),
        net_revenue=Sum("net_amount"),
    )

    gross_revenue = agg["gross_revenue"] or Decimal("0")
    total_discounts = agg["total_discounts"] or Decimal("0")
    net_revenue = agg["net_revenue"] or Decimal("0")

    avg_cost_subq = (
        ProductSupplier.objects.filter(product=OuterRef("variation__product"))
        .values("product")
        .annotate(avg=Avg("cost_price"))
        .values("avg")
    )

    cmv_agg = (
        SaleItem.objects.filter(
            sale__status=Sale.Status.COMPLETED,
            sale__completed_at__date__gte=start_date,
            sale__completed_at__date__lte=end_date,
        )
        .annotate(
            supplier_avg_cost=Coalesce(
                Subquery(avg_cost_subq, output_field=DecimalField(max_digits=10, decimal_places=2)),
                Value(Decimal("0"), output_field=DecimalField(max_digits=10, decimal_places=2)),
            )
        )
        .annotate(
            item_cmv=ExpressionWrapper(
                F("supplier_avg_cost") * F("quantity"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
        .aggregate(total=Sum("item_cmv"))
    )

    cmv = cmv_agg["total"] or Decimal("0")
    gross_profit = net_revenue - cmv
    profit_margin = (gross_profit / net_revenue * 100) if net_revenue > 0 else Decimal("0")

    return {
        "gross_revenue": gross_revenue,
        "net_revenue": net_revenue,
        "total_discounts": total_discounts,
        "cmv": cmv,
        "gross_profit": gross_profit,
        "profit_margin": profit_margin,
    }


def get_average_ticket(start_date, end_date):
    count = Sale.objects.filter(
        status=Sale.Status.COMPLETED,
        completed_at__date__gte=start_date,
        completed_at__date__lte=end_date,
    ).count()

    if count == 0:
        return Decimal("0")

    return get_total_revenue(start_date, end_date) / count


def get_abc_curve(start_date, end_date):
    from product.models import ProductSupplier

    avg_cost_subq = (
        ProductSupplier.objects.filter(product=OuterRef("variation__product"))
        .values("product")
        .annotate(avg=Avg("cost_price"))
        .values("avg")
    )

    return (
        SaleItem.objects.filter(
            sale__status=Sale.Status.COMPLETED,
            sale__completed_at__date__gte=start_date,
            sale__completed_at__date__lte=end_date,
        )
        .values("variation__product", "variation__product__name")
        .annotate(
            total_quantity=Sum("quantity"),
            total_revenue=Sum("total_price"),
            avg_unit_cost=Coalesce(
                Subquery(avg_cost_subq, output_field=DecimalField(max_digits=10, decimal_places=2)),
                Value(Decimal("0"), output_field=DecimalField(max_digits=10, decimal_places=2)),
            ),
        )
        .order_by("-total_revenue")[:20]
    )


def get_sales_evolution(start_date, end_date):
    return (
        Sale.objects.filter(
            status=Sale.Status.COMPLETED,
            completed_at__date__gte=start_date,
            completed_at__date__lte=end_date,
        )
        .annotate(sale_date=TruncDate("completed_at"))
        .values("sale_date")
        .annotate(daily_revenue=Sum("net_amount"), sale_count=Count("id"))
        .order_by("sale_date")
    )


def _avg_supplier_cost_subq(product_outer_ref):
    """Subquery que retorna o custo médio de ProductSupplier para um dado product OuterRef."""
    from product.models import ProductSupplier

    return (
        ProductSupplier.objects.filter(product=OuterRef(product_outer_ref))
        .values("product")
        .annotate(avg=Avg("cost_price"))
        .values("avg")
    )


def get_capital_imobilizado():
    from product.models import ProductVariation

    avg_cost_subq = _avg_supplier_cost_subq("product")

    return (
        ProductVariation.objects.filter(is_active=True, product__is_active=True)
        .annotate(
            effective_cost=Coalesce(
                Subquery(avg_cost_subq, output_field=DecimalField(max_digits=10, decimal_places=2)),
                Value(Decimal("0"), output_field=DecimalField(max_digits=10, decimal_places=2)),
            )
        )
        .annotate(
            line_value=ExpressionWrapper(
                F("stock") * F("effective_cost"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
        .aggregate(total=Coalesce(Sum("line_value"), Value(Decimal("0"))))
    )["total"]


def get_gmroi(start_date, end_date):
    net_revenue = get_total_revenue(start_date, end_date)

    avg_cost_subq = _avg_supplier_cost_subq("variation__product")

    cogs = (
        SaleItem.objects.filter(
            sale__status=Sale.Status.COMPLETED,
            sale__completed_at__date__gte=start_date,
            sale__completed_at__date__lte=end_date,
        )
        .annotate(
            supplier_cost=Coalesce(
                Subquery(avg_cost_subq, output_field=DecimalField(max_digits=10, decimal_places=2)),
                Value(Decimal("0"), output_field=DecimalField(max_digits=10, decimal_places=2)),
            )
        )
        .annotate(
            item_cogs=ExpressionWrapper(
                F("supplier_cost") * F("quantity"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
        .aggregate(total=Coalesce(Sum("item_cogs"), Value(Decimal("0"))))
    )["total"]

    gross_margin = net_revenue - cogs
    inventory_value = get_capital_imobilizado()

    if inventory_value > 0:
        return gross_margin / inventory_value
    return Decimal("0")


def get_stock_coverage_and_turnover(product_id, days_analyzed=30):
    from product.models import ProductVariation
    from datetime import date, timedelta

    end_date = date.today()
    start_date = end_date - timedelta(days=days_analyzed)

    current_stock = (
        ProductVariation.objects.filter(product_id=product_id, is_active=True)
        .aggregate(total=Coalesce(Sum("stock"), Value(0)))
    )["total"]

    total_sold = (
        SaleItem.objects.filter(
            sale__status=Sale.Status.COMPLETED,
            sale__completed_at__date__gte=start_date,
            sale__completed_at__date__lte=end_date,
            variation__product_id=product_id,
        )
        .aggregate(total=Coalesce(Sum("quantity"), Value(0)))
    )["total"]

    avg_daily = Decimal(str(total_sold)) / Decimal(str(days_analyzed))

    if avg_daily > 0:
        days_coverage = int(current_stock / avg_daily)
    else:
        days_coverage = None

    return {
        "current_stock": current_stock,
        "avg_daily_sales": round(float(avg_daily), 2),
        "days_coverage": days_coverage,
    }


def get_bulk_stock_coverage(product_ids, days_analyzed=30):
    from product.models import ProductVariation
    from datetime import date, timedelta

    end_date = date.today()
    start_date = end_date - timedelta(days=days_analyzed)

    stock_rows = (
        ProductVariation.objects.filter(product__in=product_ids, is_active=True)
        .values("product")
        .annotate(total_stock=Coalesce(Sum("stock"), Value(0)))
    )
    stock_by_product = {row["product"]: row["total_stock"] for row in stock_rows}

    sales_rows = (
        SaleItem.objects.filter(
            sale__status=Sale.Status.COMPLETED,
            sale__completed_at__date__gte=start_date,
            sale__completed_at__date__lte=end_date,
            variation__product__in=product_ids,
        )
        .values("variation__product")
        .annotate(total_sold=Coalesce(Sum("quantity"), Value(0)))
    )
    sold_by_product = {row["variation__product"]: row["total_sold"] for row in sales_rows}

    result = {}
    for product_id in product_ids:
        current_stock = stock_by_product.get(product_id, 0)
        total_sold = sold_by_product.get(product_id, 0)
        avg_daily = total_sold / days_analyzed if total_sold else 0
        days_coverage = int(current_stock / avg_daily) if avg_daily > 0 else None
        result[product_id] = {
            "current_stock": current_stock,
            "avg_daily_sales": round(avg_daily, 2),
            "days_coverage": days_coverage,
        }

    return result


def get_stockout_risk_list(days_analyzed=30, coverage_threshold=7):
    from django.core.cache import cache
    from product.models import ProductVariation
    from datetime import date, timedelta

    cache_key = f"stockout_risk_{days_analyzed}_{coverage_threshold}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    end_date = date.today()
    start_date = end_date - timedelta(days=days_analyzed)

    stock_rows = (
        ProductVariation.objects.filter(is_active=True, product__is_active=True)
        .values("product", "product__name")
        .annotate(total_stock=Coalesce(Sum("stock"), Value(0)))
    )
    stock_by_product = {
        row["product"]: (row["total_stock"], row["product__name"]) for row in stock_rows
    }

    sales_rows = (
        SaleItem.objects.filter(
            sale__status=Sale.Status.COMPLETED,
            sale__completed_at__date__gte=start_date,
            sale__completed_at__date__lte=end_date,
        )
        .values("variation__product")
        .annotate(total_sold=Coalesce(Sum("quantity"), Value(0)))
    )

    alerts = []
    for row in sales_rows:
        product_id = row["variation__product"]
        total_sold = row["total_sold"]

        if not total_sold or product_id not in stock_by_product:
            continue

        current_stock, product_name = stock_by_product[product_id]
        avg_daily = total_sold / days_analyzed
        days_coverage = current_stock / avg_daily if avg_daily > 0 else None

        if days_coverage is not None and days_coverage < coverage_threshold:
            alerts.append(
                {
                    "product_name": product_name,
                    "current_stock": current_stock,
                    "avg_daily_sales": round(avg_daily, 2),
                    "days_coverage": round(days_coverage, 1),
                }
            )

    alerts.sort(key=lambda x: x["days_coverage"])
    cache.set(cache_key, alerts, 3600)
    return alerts

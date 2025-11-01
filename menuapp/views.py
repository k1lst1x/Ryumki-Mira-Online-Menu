# menuapp/views.py
from __future__ import annotations

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.db.models import Prefetch, Count  # ← добавили Count
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import get_language, gettext as _
from django.views.decorators.http import require_POST

from .models import Category, Dish, Order, OrderItem

AGE_COOKIE = "AGE_VERIFIED_21"


# ========================= helpers =========================
def _age_verified(request: HttpRequest) -> bool:
    return request.COOKIES.get(AGE_COOKIE) == "1"


def _lang_code() -> str:
    return (get_language() or "ru").split("-")[0].lower()


def _wants_json(request: HttpRequest) -> bool:
    ct = request.headers.get("x-requested-with") == "XMLHttpRequest"
    acc = request.headers.get("accept", "")
    return ct or "application/json" in acc


def _get_or_create_open_order(request: HttpRequest) -> Order:
    order, _ = Order.objects.get_or_create(
        user=request.user,
        status=Order.STATUS_NEW,
    )
    return order


# ========================= pages =========================
def home(request: HttpRequest) -> HttpResponse:
    """
    Главная: список категорий + «популярные» блюда.
    """
    # Категории с доступными блюдами
    categories = (
        Category.objects.all()
        .order_by("nav_position", "position", "id")
        .prefetch_related(
            Prefetch(
                "dishes",
                queryset=Dish.objects.filter(is_available=True).order_by("position", "id"),
            )
        )
    )

    # Популярные по числу заказов; если пусто — просто доступные по позиции
    popular = (
        Dish.objects.filter(is_available=True)
        .annotate(times=Count("orderitem"))      # OrderItem через related_name по умолчанию
        .order_by("-times", "position", "id")[:12]
    )
    if not popular:
        popular = Dish.objects.filter(is_available=True).order_by("position", "id")[:12]

    locked = categories.filter(is_21plus=True).exists() and not _age_verified(request)

    return render(
        request,
        "menuapp/home.html",
        {
            "categories": categories,
            "popular_dishes": popular,   # ← вот и контент для карусели
            "background_url": None,
            "lang_code": _lang_code(),
            "age_locked": locked,
        },
    )


def category_detail(request: HttpRequest, slug: str) -> HttpResponse:
    category = get_object_or_404(
        Category.objects.prefetch_related(
            Prefetch(
                "dishes",
                queryset=Dish.objects.filter(is_available=True).order_by("position", "id"),
            )
        ),
        slug=slug,
    )

    if category.is_21plus and not _age_verified(request):
        messages.warning(request, _("Контент 21+. Подтвердите возраст."))
        return redirect("age_gate")

    try:
        bg = category.cover_image_url()
    except Exception:
        bg = None

    return render(
        request,
        "menuapp/category.html",
        {
            "category": category,
            "background_url": bg,
            "lang_code": _lang_code(),
        },
    )


def dish_detail(request: HttpRequest, slug: str) -> HttpResponse:
    dish = get_object_or_404(Dish.objects.select_related("category"), slug=slug)

    if dish.requires_21 and not _age_verified(request):
        messages.warning(request, _("Контент 21+. Подтвердите возраст."))
        return redirect("age_gate")

    bg_url = getattr(getattr(dish, "passport_bg", None), "url", None) or dish.category.cover_image_url()

    return render(
        request,
        "menuapp/dish.html",
        {
            "dish": dish,
            "background_url": bg_url,
            "lang_code": _lang_code(),
        },
    )


# ========================= auth =========================
def signup(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _("Добро пожаловать!"))
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "menuapp/signup.html", {"form": form})


# ========================= orders =========================
@login_required
@require_POST
@transaction.atomic
def add_to_order(request: HttpRequest, dish_id: int) -> HttpResponse:
    dish = get_object_or_404(Dish, pk=dish_id, is_available=True)

    if dish.requires_21 and not _age_verified(request):
        if _wants_json(request):
            return JsonResponse({"ok": False, "error": "age_required"}, status=403)
        return HttpResponseForbidden(_("Нужно подтвердить 21+"))

    order = _get_or_create_open_order(request)
    item, created = OrderItem.objects.select_for_update().get_or_create(order=order, dish=dish)
    if not created:
        item.quantity += 1
        item.save(update_fields=["quantity"])

    if _wants_json(request):
        return JsonResponse(
            {"ok": True, "order_id": order.id, "item_id": item.id, "quantity": item.quantity},
            status=200,
        )

    messages.success(request, _("Добавлено в заказ"))
    return redirect("view_order")


@login_required
def view_order(request: HttpRequest) -> HttpResponse:
    order = (
        Order.objects.filter(user=request.user, status__in=[Order.STATUS_NEW, Order.STATUS_KITCHEN])
        .order_by("-created_at")
        .first()
    )
    return render(request, "menuapp/order.html", {"order": order})


@login_required
@require_POST
def finalize_order(request: HttpRequest) -> HttpResponse:
    order = (
        Order.objects.filter(user=request.user, status=Order.STATUS_NEW)
        .order_by("-created_at")
        .first()
    )
    if not order:
        if _wants_json(request):
            return JsonResponse({"ok": False, "error": "no_order"}, status=400)
        messages.info(request, _("Нечего оформлять"))
        return redirect("home")

    if order.total_quantity() == 0:
        if _wants_json(request):
            return JsonResponse({"ok": False, "error": "empty"}, status=400)
        messages.info(request, _("Корзина пуста"))
        return redirect("view_order")

    order.status = Order.STATUS_KITCHEN
    order.save(update_fields=["status"])

    if _wants_json(request):
        return JsonResponse({"ok": True, "order_id": order.id, "status": order.status})

    messages.success(request, _("Заказ отправлен на кухню"))
    return redirect("home")


# ========================= kitchen =========================
def _staff_check(user) -> bool:
    return user.is_staff or user.is_superuser


@user_passes_test(_staff_check)
def kitchen_orders(request: HttpRequest) -> HttpResponse:
    orders = (
        Order.objects.filter(status__in=[Order.STATUS_NEW, Order.STATUS_KITCHEN])
        .select_related("user")
        .prefetch_related(
            Prefetch(
                "orderitem_set",
                queryset=OrderItem.objects.select_related("dish").order_by("id"),
            )
        )
        .order_by("-created_at")
    )
    return render(request, "menuapp/kitchen.html", {"orders": orders})


@user_passes_test(_staff_check)
@require_POST
def mark_accept(request: HttpRequest, order_id: int) -> HttpResponse:
    order = get_object_or_404(Order, pk=order_id)
    order.status = Order.STATUS_KITCHEN
    order.save(update_fields=["status"])
    if _wants_json(request):
        return JsonResponse({"ok": True, "order_id": order.id, "status": order.status})
    messages.success(request, _("Заказ принят на кухню"))
    return redirect("kitchen_orders")


@user_passes_test(_staff_check)
@require_POST
def mark_ready(request: HttpRequest, order_id: int) -> HttpResponse:
    order = get_object_or_404(Order, pk=order_id)
    order.status = Order.STATUS_READY
    order.save(update_fields=["status"])
    if _wants_json(request):
        return JsonResponse({"ok": True, "order_id": order.id, "status": order.status})
    messages.success(request, _("Заказ готов"))
    return redirect("kitchen_orders")


# ========================= age gate =========================
def age_gate(request: HttpRequest) -> HttpResponse:
    return render(request, "menuapp/age_gate.html")


@require_POST
def age_confirm(request: HttpRequest) -> HttpResponse:
    next_url = request.POST.get("next") or reverse("home")
    resp = redirect(next_url)
    # год действия, безопасно для фронта
    resp.set_cookie(AGE_COOKIE, "1", max_age=60 * 60 * 24 * 365, samesite="Lax")
    return resp

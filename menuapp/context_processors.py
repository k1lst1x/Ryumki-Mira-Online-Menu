# menuapp/context_processors.py
from django.conf import settings
from django.utils.translation import get_language
from .models import Category, Order

AGE_COOKIE = "AGE_VERIFIED_21"


def _age_verified(request):
    """Проверка куки возраста для шаблонов."""
    return request.COOKIES.get(AGE_COOKIE) == "1"


def nav_categories(request):
    """Категории для навбара (сортируем по реальным полям БД)."""
    categories = (
        Category.objects
        .filter(show_in_nav=True)
        .order_by("nav_position", "position", "id")
    )
    return {"nav_categories": categories}


def cart_processor(request):
    """Текущая корзина (если пользователь залогинен)."""
    order = None
    if request.user.is_authenticated:
        order = (
            Order.objects.filter(user=request.user, status__in=["new", "kitchen"])
            .order_by("-created_at")
            .first()
        )
    return {"cart_order": order}


def brand_contacts(request):
    """Контакты бренда (WhatsApp, Instagram, 2GIS)."""
    return {"BRAND_CONTACTS": getattr(settings, "BRAND_CONTACTS", {})}


def age_context(request):
    """Флаг age_verified, чтобы блюрить 21+ категории на фронте."""
    return {"age_verified": _age_verified(request)}


def i18n_context(request):
    """
    LANG — текущий язык (ru|kk|en)
    LANG_CHOICES — список поддерживаемых языков
    """
    lang = (get_language() or getattr(settings, "LANGUAGE_CODE", "ru")).split("-")[0]
    return {
        "LANG": lang,
        "LANG_CHOICES": getattr(settings, "LANGUAGES", (("ru", "Русский"),)),
    }

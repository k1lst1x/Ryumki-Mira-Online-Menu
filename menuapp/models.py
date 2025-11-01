# menuapp/models.py
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _, get_language


# ========= i18n утилиты =========
_LANGS = {"ru", "kk", "en"}


def _lang_code() -> str:
    """Текущий короткий код языка, всегда один из ru|kk|en, иначе ru."""
    code = (get_language() or "ru").split("-")[0].lower()
    return code if code in _LANGS else "ru"


def _first(*vals: Optional[str]) -> str:
    """Верни первый непустой текст из списка."""
    for v in vals:
        if v:
            return v
    return ""


# ========= Категория =========
class Category(models.Model):
    # i18n
    name_ru = models.CharField(_("Название (RU)"), max_length=100, blank=True, default="")
    name_en = models.CharField(_("Название (EN)"), max_length=100, blank=True, default="")
    name_kk = models.CharField(_("Атауы (KK)"), max_length=100, blank=True, default="")

    description_ru = models.TextField(_("Описание (RU)"), blank=True, default="")
    description_en = models.TextField(_("Описание (EN)"), blank=True, default="")
    description_kk = models.TextField(_("Сипаттама (KK)"), blank=True, default="")

    # общее
    slug = models.SlugField(_("Слаг"), max_length=120, unique=True, blank=True)
    position = models.PositiveIntegerField(_("Позиция"), default=0)
    image = models.ImageField(_("Изображение"), upload_to="categories/", blank=True, null=True)

    # навбар
    show_in_nav = models.BooleanField(_("Показывать в навбаре"), default=True)
    nav_position = models.PositiveIntegerField(_("Порядок в навбаре"), default=0)

    # 21+
    is_21plus = models.BooleanField(_("Скрывать до подтверждения 21+"), default=False)

    class Meta:
        ordering = ["nav_position", "position", "id"]
        indexes = [
            models.Index(fields=["show_in_nav", "nav_position"]),
            models.Index(fields=["position"]),
        ]
        verbose_name = _("Категория")
        verbose_name_plural = _("Категории")

    # ——— локализованные свойства ———
    @property
    def name(self) -> str:
        lang = _lang_code()
        if lang == "ru":
            return _first(self.name_ru, self.name_en, self.name_kk)
        if lang == "en":
            return _first(self.name_en, self.name_ru, self.name_kk)
        if lang == "kk":
            return _first(self.name_kk, self.name_ru, self.name_en)
        return _first(self.name_ru, self.name_en, self.name_kk)

    @property
    def description(self) -> str:
        lang = _lang_code()
        if lang == "ru":
            return _first(self.description_ru, self.description_en, self.description_kk)
        if lang == "en":
            return _first(self.description_en, self.description_ru, self.description_kk)
        if lang == "kk":
            return _first(self.description_kk, self.description_ru, self.description_en)
        return _first(self.description_ru, self.description_en, self.description_kk)

    def __str__(self) -> str:
        return self.name or self.slug or f"Category #{self.pk}"

    def save(self, *args, **kwargs):
        """
        Безопасная генерация slug:
          1) Пытаемся сделать slug из названия (RU/EN/KK).
          2) Если названия нет, сначала сохраняем, получаем pk,
             затем пишем slug вида 'cat-<pk>'.
        """
        creating = self.pk is None

        if not self.slug:
            base = _first(self.name_ru, self.name_en, self.name_kk)
            s = slugify(base or "")
            if s:
                self.slug = s[:120]

        super().save(*args, **kwargs)

        if creating and not self.slug:
            self.slug = f"cat-{self.pk}"
            super().save(update_fields=["slug"])

    def get_absolute_url(self) -> str:
        return reverse("category_detail", kwargs={"slug": self.slug})

    def cover_image_url(self) -> Optional[str]:
        """
        Обложка категории на фоне:
          1) image самой категории
          2) первая картинка блюда в категории
          3) None
        """
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        first_with_img = (
            self.dishes.exclude(image="").exclude(image__isnull=True).order_by("position", "id").first()
        )
        return getattr(first_with_img.image, "url", None) if first_with_img else None


# ========= Блюдо =========
class Dish(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="dishes",
        verbose_name=_("Категория"),
    )

    # i18n
    name_ru = models.CharField(_("Название (RU)"), max_length=150, blank=True, default="")
    name_en = models.CharField(_("Название (EN)"), max_length=150, blank=True, default="")
    name_kk = models.CharField(_("Атауы (KK)"), max_length=150, blank=True, default="")

    description_ru = models.TextField(_("Описание (RU)"), blank=True, default="")
    description_en = models.TextField(_("Описание (EN)"), blank=True, default="")
    description_kk = models.TextField(_("Сипаттама (KK)"), blank=True, default="")

    # общее
    slug = models.SlugField(_("Слаг"), max_length=160, unique=True, blank=True)
    base_price = models.DecimalField(_("Базовая цена"), max_digits=8, decimal_places=2)

    image = models.ImageField(_("Фото блюда"), upload_to="dishes/", blank=True, null=True)
    passport_bg = models.ImageField(_("Фон-паспорт"), upload_to="dishes/passports/", blank=True, null=True)

    is_available = models.BooleanField(_("Доступно"), default=True)
    position = models.PositiveIntegerField(_("Позиция"), default=0)

    class Meta:
        ordering = ["category", "position", "id"]
        indexes = [
            models.Index(fields=["category", "position"]),
            models.Index(fields=["is_available"]),
            models.Index(fields=["slug"]),
        ]
        verbose_name = _("Блюдо")
        verbose_name_plural = _("Блюда")

    @property
    def name(self) -> str:
        lang = _lang_code()
        if lang == "ru":
            return _first(self.name_ru, self.name_en, self.name_kk)
        if lang == "en":
            return _first(self.name_en, self.name_ru, self.name_kk)
        if lang == "kk":
            return _first(self.name_kk, self.name_ru, self.name_en)
        return _first(self.name_ru, self.name_en, self.name_kk)

    @property
    def description(self) -> str:
        lang = _lang_code()
        if lang == "ru":
            return _first(self.description_ru, self.description_en, self.description_kk)
        if lang == "en":
            return _first(self.description_en, self.description_ru, self.description_kk)
        if lang == "kk":
            return _first(self.description_kk, self.description_ru, self.description_en)
        return _first(self.description_ru, self.description_en, self.description_kk)

    def save(self, *args, **kwargs):
        """
        Безопасная генерация slug для блюд.
        """
        creating = self.pk is None

        if not self.slug:
            base = _first(self.name_ru, self.name_en, self.name_kk)
            s = slugify(base or "")
            if s:
                self.slug = s[:160]

        super().save(*args, **kwargs)

        if creating and not self.slug:
            self.slug = f"dish-{self.pk}"
            super().save(update_fields=["slug"])

    def __str__(self) -> str:
        return self.name or self.slug or f"Dish #{self.pk}"

    @property
    def requires_21(self) -> bool:
        """Нужно ли подтверждение 21+ (наследуется от категории)."""
        return bool(getattr(self.category, "is_21plus", False))


# ========= Заказ =========
class Order(models.Model):
    STATUS_NEW = "new"
    STATUS_KITCHEN = "kitchen"
    STATUS_READY = "ready"
    STATUS_CHOICES = [
        (STATUS_NEW, _("Новый")),
        (STATUS_KITCHEN, _("На кухне")),
        (STATUS_READY, _("Готово")),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="orders", verbose_name=_("Пользователь")
    )
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)
    items = models.ManyToManyField("Dish", through="OrderItem", verbose_name=_("Позиции"))
    status = models.CharField(_("Статус"), max_length=20, choices=STATUS_CHOICES, default=STATUS_NEW)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]
        verbose_name = _("Заказ")
        verbose_name_plural = _("Заказы")

    def __str__(self) -> str:
        username = self.user.username if self.user_id else ""
        return _("Заказ #{id} от {username}").format(id=self.id or 0, username=username)

    def total_price(self) -> Decimal:
        total = Decimal("0.00")
        for item in self.orderitem_set.select_related("dish"):
            total += item.line_price()
        return total

    def total_quantity(self) -> int:
        return sum(item.quantity for item in self.orderitem_set.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name=_("Заказ"))
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, verbose_name=_("Блюдо"))
    quantity = models.PositiveIntegerField(_("Количество"), default=1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["order", "dish"], name="uniq_order_dish"),
        ]
        verbose_name = _("Позиция заказа")
        verbose_name_plural = _("Позиции заказа")

    def __str__(self) -> str:
        return _("{dish} ×{q}").format(dish=self.dish.name, q=self.quantity)

    def line_price(self) -> Decimal:
        return (self.dish.base_price or Decimal("0.00")) * Decimal(self.quantity)

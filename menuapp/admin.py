# menuapp/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Dish


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    # генерим slug из русского названия
    prepopulated_fields = {"slug": ("name_ru",)}

    # список
    list_display = (
        "name_ru", "slug",
        "show_in_nav", "nav_position",
        "is_21plus",
        "position",
        "image_preview",
    )
    list_display_links = ("name_ru",)
    list_editable = ("show_in_nav", "nav_position", "is_21plus", "position")
    list_filter = ("show_in_nav", "is_21plus")
    search_fields = (
        "name_ru", "name_en", "name_kk",
        "description_ru", "description_en", "description_kk",
        "slug",
    )
    ordering = ("nav_position", "position", "name_ru")
    list_per_page = 50
    save_as = True
    save_on_top = True

    # форма
    fieldsets = (
        ("Название", {
            "fields": (("name_ru", "name_en", "name_kk"), "slug"),
        }),
        ("Описание", {
            "fields": (("description_ru", "description_en", "description_kk"),),
        }),
        ("Медиа", {
            "fields": ("image", "image_preview"),
        }),
        ("Навигация", {
            "fields": ("show_in_nav", "nav_position", "position", "is_21plus"),
        }),
    )
    readonly_fields = ("image_preview",)

    @admin.display(description="Фото")
    def image_preview(self, obj):
        img = getattr(obj, "image", None)
        if not img:
            return "—"
        try:
            return format_html('<img src="{}" width="60" style="border-radius:6px" />', img.url)
        except Exception:
            return "—"

    actions = ["act_show_in_nav", "act_hide_in_nav", "act_mark_21", "act_unmark_21"]

    @admin.action(description="Показать в навбаре")
    def act_show_in_nav(self, request, qs):
        qs.update(show_in_nav=True)

    @admin.action(description="Скрыть из навбара")
    def act_hide_in_nav(self, request, qs):
        qs.update(show_in_nav=False)

    @admin.action(description="Отметить 21+")
    def act_mark_21(self, request, qs):
        qs.update(is_21plus=True)

    @admin.action(description="Снять 21+")
    def act_unmark_21(self, request, qs):
        qs.update(is_21plus=False)


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name_ru",)}

    # список
    list_display = (
        "name_ru", "slug",
        "category",
        "base_price",
        "is_available",
        "position",
        "image_preview",
        "passport_preview",
    )
    list_display_links = ("name_ru",)
    list_editable = ("is_available", "position")
    list_filter = ("category", "is_available")
    search_fields = (
        "name_ru", "name_en", "name_kk",
        "description_ru", "description_en", "description_kk",
        "slug",
    )
    ordering = ("category", "position", "name_ru")
    list_select_related = ("category",)
    autocomplete_fields = ("category",)
    list_per_page = 50
    save_on_top = True

    # форма
    fieldsets = (
        ("Название", {
            "fields": (("name_ru", "name_en", "name_kk"), "slug"),
        }),
        ("Описание", {
            "fields": (("description_ru", "description_en", "description_kk"),),
        }),
        ("Свойства", {
            "fields": ("category", "base_price", "is_available", "position"),
        }),
        ("Изображения", {
            "fields": ("image", "passport_bg", "image_preview", "passport_preview"),
            "description": "image — фото блюда (вклейка). passport_bg — фон-паспорт на заднем плане.",
        }),
    )
    readonly_fields = ("image_preview", "passport_preview")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("category")

    @admin.display(description="Фото")
    def image_preview(self, obj):
        img = getattr(obj, "image", None)
        if not img:
            return "—"
        try:
            return format_html('<img src="{}" width="60" style="border-radius:6px" />', img.url)
        except Exception:
            return "—"

    @admin.display(description="Паспорт")
    def passport_preview(self, obj):
        pb = getattr(obj, "passport_bg", None)
        if not pb:
            return "—"
        try:
            return format_html('<img src="{}" width="60" style="border-radius:6px" />', pb.url)
        except Exception:
            return "—"

    actions = ["mark_available", "mark_unavailable"]

    @admin.action(description="Отметить как доступные")
    def mark_available(self, request, queryset):
        queryset.update(is_available=True)

    @admin.action(description="Скрыть из меню")
    def mark_unavailable(self, request, queryset):
        queryset.update(is_available=False)

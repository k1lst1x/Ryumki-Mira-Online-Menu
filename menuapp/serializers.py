from rest_framework import serializers
from django.utils.translation import get_language
from .models import Category, Dish

AGE_COOKIE = "AGE_VERIFIED_21"


def _age_verified(serializer) -> bool:
    req = getattr(serializer, "context", {}).get("request")
    if not req:
        return False
    return req.COOKIES.get(AGE_COOKIE) == "1"


def _abs_url(serializer, url: str | None) -> str | None:
    if not url:
        return None
    req = getattr(serializer, "context", {}).get("request")
    return req.build_absolute_uri(url) if req else url


class DishSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    passport_bg = serializers.SerializerMethodField()
    requires_21 = serializers.SerializerMethodField()
    locked = serializers.SerializerMethodField()
    lang = serializers.SerializerMethodField()

    # отдаём name/description через свойства модели (уже i18n-aware)
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "base_price",
            "image",
            "passport_bg",
            "is_available",
            "requires_21",
            "locked",
            "lang",
        )

    def get_name(self, obj):  # noqa
        return obj.name

    def get_description(self, obj):  # noqa
        return obj.description

    def get_image(self, obj):
        return _abs_url(self, obj.image.url) if obj.image else None

    def get_passport_bg(self, obj):
        pb = getattr(obj, "passport_bg", None)
        return _abs_url(self, pb.url) if getattr(pb, "url", None) else None

    def get_requires_21(self, obj):
        return bool(getattr(obj.category, "is_21plus", False))

    def get_locked(self, obj):
        return self.get_requires_21(obj) and not _age_verified(self)

    def get_lang(self, obj):
        return get_language() or "ru"


class CategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    requires_21 = serializers.SerializerMethodField()
    locked = serializers.SerializerMethodField()
    cover_background_url = serializers.SerializerMethodField()
    dishes = DishSerializer(many=True, read_only=True)
    lang = serializers.SerializerMethodField()

    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "position",
            "image",
            "requires_21",
            "locked",
            "cover_background_url",
            "dishes",
            "lang",
        )

    def get_name(self, obj):  # noqa
        return obj.name

    def get_description(self, obj):  # noqa
        return obj.description

    def get_image(self, obj):
        return _abs_url(self, obj.image.url) if obj.image else None

    def get_requires_21(self, obj):
        return bool(getattr(obj, "is_21plus", False))

    def get_locked(self, obj):
        return self.get_requires_21(obj) and not _age_verified(self)

    def get_cover_background_url(self, obj):
        cover = None
        if hasattr(obj, "cover_image_url"):
            try:
                cover = obj.cover_image_url()
            except Exception:
                cover = None
        return _abs_url(self, cover) if cover else None

    def get_lang(self, obj):
        return get_language() or "ru"

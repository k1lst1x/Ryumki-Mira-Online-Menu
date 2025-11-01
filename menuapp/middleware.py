# menuapp/middleware.py
from django.shortcuts import redirect
from django.urls import resolve

AGE_COOKIE = "AGE_VERIFIED_21"

# Префиксы URL, которые всегда пропускаем (они не ходят в i18n-паттернах)
EXCLUDE_PREFIXES = (
    "/static/",
    "/media/",
    "/api/",
    "/i18n/",       # смена языка и подобные служебные эндпоинты
    "/favicon.ico",
)

# Имена url, которые нельзя блокировать даже при небезопасных методах
# NB: имена работают независимо от языкового префикса (/ru/, /kk/, /en/)
EXCLUDE_NAMES = {
    # возрастной поток
    "age_gate",
    "age_confirm",
    # смена языка
    "set_language",
    # аутентификация
    "login",
    "logout",
    "signup",
    # кухня (операции для персонала)
    "kitchen_orders",
    "mark_accept",
    "mark_ready",
    # просмотр корзины (GET и так пропускаем, но на всякий случай)
    "view_order",
}

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _is_excluded_by_prefix(path: str) -> bool:
    return path.startswith(EXCLUDE_PREFIXES)


def _resolved_name(request) -> str | None:
    # resolve дешевле и надёжнее, чем хранить reverse-названия
    try:
        match = resolve(request.path_info)
        return match.url_name
    except Exception:
        return None


class AgeGate21Middleware:
    """
    Политика:
      • Безопасные методы (GET/HEAD/OPTIONS) не блокируем. Блюр делает фронт.
      • Небезопасные методы (POST/PUT/PATCH/DELETE) разрешаем только:
         – если есть кука AGE_VERIFIED_21=1
         – если маршрут служебный (см. EXCLUDE_*)
         – если пользователь staff/superuser
    Расчёт на то, что вьюхи 21+ дополнительно проверяют бизнес-правила.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # 1) служебные пути по префиксу
        if _is_excluded_by_prefix(path):
            return self.get_response(request)

        # 2) staff/superuser пропускаем, они знают, что делают
        user = getattr(request, "user", None)
        if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
            return self.get_response(request)

        # 3) безопасные методы не блокируем: фронт уже блюрит контент 21+
        if request.method in SAFE_METHODS:
            return self.get_response(request)

        # 4) маршруты, которые нельзя блокировать (работают с i18n-префиксами)
        name = _resolved_name(request)
        if name in EXCLUDE_NAMES:
            return self.get_response(request)

        # 5) нужна кука подтверждения возраста для небезопасных методов
        if request.COOKIES.get(AGE_COOKIE) == "1":
            return self.get_response(request)

        # 6) нет куки — отправляем на страницу подтверждения
        return redirect("age_gate")

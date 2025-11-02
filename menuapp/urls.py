# menuapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # === меню ===
    path("", views.home, name="home"),
    path("categories/", views.home, name="categories"),  # список категорий
    path("categories/<slug:slug>/", views.category_detail, name="category_detail"),  # одна категория
    path("dishes/<slug:slug>/", views.dish_detail, name="dish_detail"),  # одно блюдо

    # === аккаунты ===
    path("signup/", views.signup, name="signup"),

    # === заказы ===
    path("order/add/<int:dish_id>/", views.add_to_order, name="add_to_order"),
    path("order/", views.view_order, name="view_order"),
    path("order/finalize/", views.finalize_order, name="finalize_order"),

    # === кухня ===
    path("kitchen/", views.kitchen_orders, name="kitchen_orders"),
    path("kitchen/accept/<int:order_id>/", views.mark_accept, name="mark_accept"),
    path("kitchen/ready/<int:order_id>/", views.mark_ready, name="mark_ready"),

    # === возрастной фильтр ===
    path("age/", views.age_gate, name="age_gate"),
    path("age/confirm/", views.age_confirm, name="age_confirm"),
]

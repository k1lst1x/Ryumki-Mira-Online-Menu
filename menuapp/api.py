from django.urls import path
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Category, Dish
from .serializers import CategorySerializer, DishSerializer


@api_view(['GET'])
def categories(request):
    qs = Category.objects.prefetch_related('dishes__modifier_groups__modifiers')
    return Response(CategorySerializer(qs, many=True).data)


@api_view(['GET'])
def category(request, slug):
    obj = get_object_or_404(
        Category.objects.prefetch_related('dishes__modifier_groups__modifiers'),
        slug=slug,
    )
    return Response(CategorySerializer(obj).data)


@api_view(['GET'])
def dish(request, slug):
    obj = get_object_or_404(
        Dish.objects.prefetch_related('modifier_groups__modifiers'),
        slug=slug,
    )
    return Response(DishSerializer(obj).data)


urlpatterns = [
    path('categories/', categories),
    path('categories/<slug:slug>/', category),
    path('dishes/<slug:slug>/', dish),
]


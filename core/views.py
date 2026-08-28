from django.shortcuts import render

from menu.models import MenuItem


def home(request):
    featured_items = MenuItem.objects.filter(
        is_available=True,
        is_featured=True,
    )

    context = {
        "featured_items": featured_items,
    }

    return render(
        request,
        "core/home.html",
        context,
    )
from collections import OrderedDict

from django.shortcuts import render

from .models import MenuItem


def menu_list(request):
    items = MenuItem.objects.filter(
        is_available=True,
    )

    grouped_items = OrderedDict()

    for category_value, category_label in MenuItem.Category.choices:
        category_items = [
            item for item in items
            if item.category == category_value
        ]

        if category_items:
            grouped_items[category_label] = category_items

    context = {
        "grouped_items": grouped_items,
    }

    return render(
        request,
        "menu/menu_list.html",
        context,
    )
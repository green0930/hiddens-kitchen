from django.contrib import admin
from django.contrib.sitemaps import Sitemap
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, reverse
from django.http import HttpResponse


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return [
            "home",
            "menu:menu_list",
            "orders:preorder",
        ]

    def location(self, item):
        return reverse(item)


sitemaps = {
    "static": StaticViewSitemap,
}


urlpatterns = [
    path("admin/", admin.site.urls),

    path(
            "robots.txt",
            lambda request: HttpResponse(
                "User-agent: *\n"
                "Allow: /\n"
                "Disallow: /admin/\n"
                "Sitemap: https://hiddens-kitchen.onrender.com/sitemap.xml\n",
                content_type="text/plain",
            ),
        ),

    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),

    path(
        "menu/",
        include("menu.urls"),
    ),

    path(
        "order/",
        include("orders.urls"),
    ),

    path(
        "",
        include("core.urls"),
    ),

]
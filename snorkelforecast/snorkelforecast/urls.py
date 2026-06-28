"""
URL configuration for snorkelforecast project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path
from django.views.static import serve

from conditions.sitemaps import (
    CountrySitemap,
    GuideSitemap,
    LocationSitemap,
    LocationSeaTemperatureSitemap,
    StaticViewSitemap,
)

sitemaps = {
    "static": StaticViewSitemap,
    "guides": GuideSitemap,
    "countries": CountrySitemap,
    "locations": LocationSitemap,
    "sea_temperature": LocationSeaTemperatureSitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("__reload__/", include("django_browser_reload.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    re_path(r'^robots\.txt$', serve, {'path': 'robots.txt', 'document_root': settings.STATIC_ROOT}),
]

urlpatterns += i18n_patterns(
    path("", include("conditions.urls")),
    prefix_default_language=False,
)

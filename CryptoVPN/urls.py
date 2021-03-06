"""CryptoVPN URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from cryptovpnapp.urls import cryptovpn_api_urls
from cryptovpnapp.views import Home

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^($|index)', Home.as_view(), name='index'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/1.0/rest-auth/', include('rest_auth.urls')),
    url(r'^api/1.0/rest-auth/registration/', include('rest_auth.registration.urls')),
    url(r'^api/1.0/', include(cryptovpn_api_urls.urls)),
]


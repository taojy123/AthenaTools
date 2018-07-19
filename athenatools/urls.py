
"""URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
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

from views import *

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^$', index),
    url(r'^index/$', index),

    url(r'^xls/$', xls),
    url(r'^rsa/$', rsa),
    url(r'^mysql/$', mysql),
    
    url(r'^login/$', login),
    url(r'^logout/$', logout),
    url(r'^password/$', password),

    url(r'^output/$', output),
]


# This will work if DEBUG is True
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()

# This will work if DEBUG is True or False
# from django.conf import settings
# from django.views.static import serve
# import re
# urlpatterns.append(url(
#     '^' + re.escape(settings.STATIC_URL.lstrip('/')) + '(?P<path>.*)$',
#     serve,
#     {'document_root': './static/'}))

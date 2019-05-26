
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
import lazypage.urls

from views import *

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^$', index),
    url(r'^index/$', index),

    url(r'^xls/$', xls),
    url(r'^rsa/$', rsa),
    url(r'^mysql/$', mysql),
    url(r'^pdf/$', pdf),
    url(r'^slim/$', slim),
    url(r'^wb/$', wb),

    url(r'^cert_reminder/$', cert_reminder),
    url(r'^cert_reminder/(\d+)/$', cert_reminder_detail),

    url(r'^synote/(.*?)/?$', synote),
    url(r'^synote/(.+)/?$', synote_api),

    url(r'^login/$', login),
    url(r'^register/$', register),
    url(r'^logout/$', logout),
    url(r'^password/$', password),

    url(r'^test_slow_page/$', test_slow_page),
    url(r'^lazypage/', lazypage.urls.get_urls()),

    # hidden
    url(r'^purchase/$', purchase),
    url(r'^purchase/statistics/$', purchase_statistics),
    url(r'^purchase/statistics/groups/$', purchase_statistics_groups),
    url(r'^purchase/entry/$', purchase_entry),
    url(r'^purchase/list/$', purchase_list),
    url(r'^purchase/preview/$', purchase_preview),
    url(r'^purchase/preview/sub/$', purchase_preview_sub),
    url(r'^purchase/preview/modify/$', purchase_preview_modify),

    url(r'^nakedoor/$', nakedoor),
    url(r'^wedoor/$', wedoor),
    url(r'^gopro/$', gopro),
    url(r'^email/$', email),
    url(r'^deploy/(.+)/$', deploy),
    url(r'^charts/$', chart1),
    url(r'^chart1/$', chart1),
    url(r'^ppt/$', ppt),

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

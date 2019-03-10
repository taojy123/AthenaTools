# coding=utf-8
import StringIO
import random
from collections import OrderedDict

import xlwt
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.utils.text import capfirst

from athenatools.views import get_normal_quantity
from models import *


def find_model_index(name):
    count = 0
    for model, model_admin in admin.site._registry.items():
        if capfirst(model._meta.verbose_name_plural) == name:
            return count
        else:
            count += 1
    return count


def index_decorator(func):
    def inner(*args, **kwargs):
        templateresponse = func(*args, **kwargs)
        for app in templateresponse.context_data['app_list']:
            app['models'].sort(key=lambda x: find_model_index(x['name']))
        return templateresponse
    return inner


registry = OrderedDict()
registry.update(admin.site._registry)
admin.site._registry = registry
admin.site.index = index_decorator(admin.site.index)
admin.site.app_index = index_decorator(admin.site.app_index)
admin.site.site_header = 'Athena Tools Admin'

admin.site.unregister(Group)
admin.site.unregister(Site)


class ModelAdmin(admin.ModelAdmin):

    def lookup_allowed(self, lookup, value):
        return True


@admin.register(LogEntry)
class LogEntryAdmin(ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ['id', 'action_time', 'user', '__str__']
    readonly_fields = ['action_time', 'user', 'content_type', 'object_id', 'object_repr', 'action_flag', 'change_message', 'objects']


@admin.register(CertReminder)
class CertReminderAdmin(ModelAdmin):
    list_display = ['id', 'domain', 'user', 'expire_at', 'err']
    list_max_show_all = 10000


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['kind', 'title', 'unit', 'vendor', 'supplier', 'default_exp', 'current_stock', 'jump']
    list_display_links = ['title']
    search_fields = ['title', 'vendor', 'supplier']
    list_filter = ['kind', 'vendor', 'supplier']
    list_max_show_all = 10000

    def current_stock(self, obj):
        return obj.current_stock
    current_stock.short_description = u'当前库存'

    def jump(self, obj):
        return u'<a href="/purchase/statistics/?begin=2018-10-01&product_id=%d">查看</a>' % obj.id
    jump.allow_tags = True
    jump.short_description = u'库存记录'


@admin.register(Purchase)
class PurchaseAdmin(ModelAdmin):
    list_display = ['id', 'user', 'product', 'quantity', 'day', 'created_at', 'category']
    search_fields = ['product__title']
    list_filter = ['product__kind', 'day', 'is_consume']
    list_max_show_all = 10000


@admin.register(Document)
class DocumentAdmin(ModelAdmin):
    list_display = ['name', 'category', 'keywords', 'remark', 'file', 'created_at']
    search_fields = ['name', 'keywords', 'remark']
    list_filter = ['category', 'created_at']
    list_max_show_all = 10000


@admin.register(Deployment)
class DeploymentAdmin(ModelAdmin):
    list_display = ['name', 'cmd', 'remark']
    actions = ['deploy']

    def deploy(modeladmin, request, queryset):
        r = []
        for item in queryset.all():
            h = item.deploy()
            r.append((h.id, h.success, h.stderr))
        return JsonResponse(r, safe=False)
    deploy.short_description = 'deploy'


@admin.register(DeployHistory)
class DeployHistoryAdmin(ModelAdmin):
    list_display = ['deployment', 'stdout', 'stderr', 'success', 'created_at']


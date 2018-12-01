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
from django.http import HttpResponse
from django.utils.text import capfirst


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


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ['id', 'action_time', 'user', '__str__']
    readonly_fields = ['action_time', 'user', 'content_type', 'object_id', 'object_repr', 'action_flag', 'change_message', 'objects']


@admin.register(CertReminder)
class CertReminderAdmin(admin.ModelAdmin):
    list_display = ['id', 'domain', 'user', 'expire_at']
    list_max_show_all = 10000


def get_normal_quantity(queryset):
    quantity = queryset.aggregate(Sum('quantity')).get('quantity__sum') or 0
    if int(quantity) == quantity:
        return int(quantity)
    return quantity


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['kind', 'title', 'unit', 'vendor', 'supplier']
    list_display_links = ['title']
    search_fields = ['title', 'vendor', 'supplier']
    list_filter = ['kind', 'vendor', 'supplier']
    list_max_show_all = 10000

    def stock_statistic(modeladmin, request, queryset):

        p = Purchase.objects.order_by('day').first()
        if p:
            begin = p.day
        else:
            begin = timezone.localdate().replace(day=1)
        end = timezone.localdate()

        wb = xlwt.Workbook()

        keys = []
        titles = []

        for product in queryset.all():

            print product

            title = product.title
            unit = product.unit
            key = (title, unit)

            print key

            if key in keys:
                continue

            if title in titles:
                title = '%s_%s' % (title, random.randint(1, 100))

            ws = wb.add_sheet(title)
            keys.append(key)
            titles.append(title)

            ws.write(0, 0, u'类别')
            ws.write(0, 1, product.kind)
            ws.write(0, 2, u'原材料名称')
            ws.write(0, 3, title)
            ws.write(0, 4, u'规格')
            ws.write(0, 5, unit)

            queryset = Purchase.objects.filter(product__title=title, product__unit=unit)

            stock_begin = get_normal_quantity(queryset.filter(day__lt=begin))
            ws.write(1, 0, u'留存库存')
            ws.write(1, 1, stock_begin)

            ws.write(2, 0, u'日期')
            ws.write(2, 1, u'进货数量')
            ws.write(2, 2, u'出货数量')
            ws.write(2, 3, u'结存')
            ws.write(2, 4, u'摘要')
            ws.write(2, 5, u'备注')

            day = begin
            i = 3
            while True:
                if day > end:
                    break

                purchase_count = get_normal_quantity(queryset.filter(day=day, is_consume=False))
                consume_count = get_normal_quantity(queryset.filter(day=day, is_consume=True))
                stock = get_normal_quantity(queryset.filter(day__lte=day))

                if purchase_count == consume_count == 0:
                    day += timezone.timedelta(days=1)
                    continue

                ws.write(i, 0, str(day))
                ws.write(i, 1, purchase_count)
                ws.write(i, 2, consume_count)
                ws.write(i, 3, stock)
                ws.write(i, 4, '')
                ws.write(i, 5, '')

                day += timezone.timedelta(days=1)
                i += 1

        s = StringIO.StringIO()
        wb.save(s)
        s.seek(0)
        data = s.read()
        response = HttpResponse(data)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename="stock.xls"'
        return response

    stock_statistic.short_description = u'库存逐日统计'
    actions = [stock_statistic]


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product', 'quantity', 'day', 'created_at', 'category']
    list_max_show_all = 10000


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'keywords', 'remark', 'file', 'created_at']
    search_fields = ['name', 'keywords', 'remark']
    list_filter = ['category', 'created_at']
    list_max_show_all = 10000


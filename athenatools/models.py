# -*- coding: utf-8 -*-
import commands
import datetime
import json
import sys

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from collections import OrderedDict
from hashlib import md5


class RoughCache(object):

    data = max_size = None

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(RoughCache, cls).__new__(cls)
        return cls.instance

    def __init__(self, max_size=100 * 1000 * 1000):
        # default 100MB
        if self.data is None:
            self.data = OrderedDict()
            self.max_size = max_size

    def get(self, key, default=None):
        key = str(key)
        md5key = md5(key).hexdigest()
        return self.data.get(md5key, default)

    def set(self, key, value, check=True):
        key = str(key)
        if check:
            self.check()
        md5key = md5(key).hexdigest()
        self.data[md5key] = value

    def gets(self, *keys):
        key = ':'.join(keys)
        return self.get(key)

    def sets(self, *keys):
        assert len(keys) >= 2, 'parameters of sets function must more then two!'
        value = keys[-1]
        key = ':'.join(keys[:-1])
        return self.set(key, value)

    def has(self, *keys):
        key = ':'.join(keys)
        md5key = md5(key).hexdigest()
        return md5key in self.data

    def size(self):
        return sys.getsizeof(self.data)

    def count(self):
        return len(self.data)

    def clear(self, clear_all=True):
        if clear_all:
            self.data.clear()
        else:
            length = len(self.data)
            i = 0
            for key in self.data.iteritems():
                i += 1
                if i >= length / 2:
                    break
                del self.data[key]

    def check(self):
        if self.size() < self.max_size:
            return False
        self.clear(clear_all=False)
        return True


def normal_number(number):
    if int(number) == number:
        return int(number)
    return number


def get_normal_quantity(queryset):
    sql = unicode(queryset.query).encode('utf8')
    cache = RoughCache()
    if cache.has(sql, 'quantity__sum'):
        return cache.gets(sql, 'quantity__sum')
    quantity = queryset.aggregate(Sum('quantity')).get('quantity__sum') or 0
    quantity = normal_number(quantity)
    cache.sets(sql, 'quantity__sum', quantity)
    return quantity


class CertReminder(models.Model):
    user = models.ForeignKey(User, blank=True, null=True)
    domain = models.CharField(max_length=100, help_text='不需要加 https')
    ahead_days = models.IntegerField(default=7, help_text='提前几天提醒')
    email = models.TextField(blank=True)
    expire_at = models.DateField(blank=True, null=True, help_text='过期时间')
    extra = models.TextField(blank=True)

    @property
    def remain_days(self):
        if not self.expire_at:
            return 0
        return (self.expire_at - timezone.localdate()).days

    @property
    def is_expiring(self):
        if not self.remain_days:
            return False
        return self.remain_days <= self.ahead_days

    @property
    def is_public(self):
        return not self.user

    @property
    def is_private(self):
        return self.user

    @property
    def emails(self):
        return self.email.strip().splitlines()

    @property
    def extra_data(self):
        if not self.extra:
            return {}
        return json.loads(self.extra)

    def fetch(self):
        cmd = 'echo | openssl s_client -servername %s -connect %s:443 2>/dev/null | openssl x509 -noout -enddate' % (
            self.domain, self.domain)
        s = commands.getoutput(cmd)  # notAfter=Dec  5 02:18:56 2018 GMT
        if '=' not in s:
            self.extra = self.extra_data
            self.extra['err'] = s
            self.save()
            return
        s = s.split('=')[1].strip()
        t = datetime.datetime.strptime(s, '%b %d %H:%M:%S %Y %Z')
        t = timezone.make_aware(t)
        self.expire_at = t.date()

        if self.is_expiring:
            extra = json.loads(self.extra) if self.extra else {}
            notice_days = extra.get('notice_days', [])
            today = str(timezone.localdate())
            if today not in notice_days:
                notice_days.append(today)
                extra['notice_days'] = notice_days
                self.extra = json.dumps(extra)
                self.send_notice()

        self.save()

    def send_notice(self):
        if not self.is_expiring:
            return
        text = u'%s 该域名的 https 证书将在 %d 天后过期，为避免网站无法访问，请及时进行更新操作！' % (self.domain, self.remain_days)
        send_mail(u'Https 证书临期提醒', text, 'watchmen123456@163.com', self.emails)


class Product(models.Model):
    # title 可重复，但是 kind 和 unit 必须保持一致
    # 也就是说不允许出现 title 相同但 unit 不同的两个 product
    title = models.CharField(max_length=255, verbose_name='名称', db_index=True)
    kind = models.CharField(max_length=255, blank=True, verbose_name='类别')
    unit = models.CharField(max_length=255, blank=True, verbose_name='规格')

    vendor = models.CharField(max_length=255, blank=True, verbose_name='生产单位/进口代理商')
    supplier = models.CharField(max_length=255, blank=True, verbose_name='供应商')

    def __unicode__(self):
        return self.title

    @classmethod
    def all_titles(cls):
        titles = cls.objects.all().values_list('title', flat=True).distinct()
        return titles

    @classmethod
    def check_titles(cls):
        errors = []
        titles = cls.all_titles()
        for title in titles:
            if cls.objects.filter(title=title).values_list('kind', 'unit').distinct().count() > 1:
                errors.append(title)
        return errors

    @property
    def current_stock(self):
        stock = self.purchase_set.all().aggregate(Sum('quantity')).get('quantity__sum') or 0
        return normal_number(stock)

    class Meta:
        verbose_name = '原材料'
        verbose_name_plural = '原材料'


class Purchase(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, verbose_name='录入者')
    day = models.DateField(null=True, blank=True, default=timezone.localdate, verbose_name='日期', db_index=True)

    product = models.ForeignKey(Product, verbose_name='原材料')
    quantity = models.FloatField(default=1, verbose_name='数量')
    produced_at = models.CharField(max_length=255, blank=True, verbose_name='生产日期')
    exp = models.CharField(max_length=255, blank=True, verbose_name='保质期')
    receipt = models.CharField(max_length=255, blank=True, verbose_name='索证索票')
    expired_quantity = models.CharField(max_length=255, blank=True, verbose_name='过期处理数量')
    remark = models.CharField(max_length=255, blank=True, verbose_name='备注')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='最后更新时间')

    is_consume = models.BooleanField(default=False, verbose_name='是否为出货')

    def __unicode__(self):
        return u'%s * %s' % (self.product, self.normal_quantity)

    @property
    def category(self):
        return '采购' if self.is_consume else '出货'

    @property
    def normal_quantity(self):
        return normal_number(self.quantity)

    @property
    def kind(self):
        return self.product.kind

    @property
    def title(self):
        return self.product.title

    @property
    def unit(self):
        return self.product.unit

    @property
    def vendor(self):
        return self.product.vendor

    @property
    def supplier(self):
        return self.product.supplier

    class Meta:
        verbose_name = '采购记录'
        verbose_name_plural = '采购记录'


class Document(models.Model):
    file = models.FileField(verbose_name='文件')
    name = models.CharField(max_length=255, blank=True, verbose_name='名称')
    category = models.CharField(max_length=255, blank=True, verbose_name='分类')
    keywords = models.CharField(max_length=255, blank=True, verbose_name='关键词')
    remark = models.CharField(max_length=255, blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = '文档'
        verbose_name_plural = '文档'

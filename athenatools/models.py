# -*- coding: utf-8 -*-
import commands
import datetime
import json
import sys
import time

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from subprocess import Popen, PIPE


def getcmdoutput(cmd, timeout=5):
    p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    for i in range(timeout):
        code = p.poll()
        print(code)
        if None:
            time.sleep(1)
            continue
        if code == 0:
            return p.stdout.read()
        elif code == 1:
            return p.stderr.read()
        else:
            return p.stdout.read() + p.stderr.read()
    p.kill()
    return 'timeout'


def normal_number(number):
    number = round(number, 4)
    if int(number) == number:
        return int(number)
    return number


def get_normal_quantity(queryset):
    quantity = queryset.aggregate(Sum('quantity')).get('quantity__sum') or 0
    quantity = normal_number(quantity)
    return quantity


class CertReminder(models.Model):
    user = models.ForeignKey(User, blank=True, null=True)
    domain = models.CharField(max_length=100, help_text='不需要加 https')
    ahead_days = models.IntegerField(default=7, help_text='提前几天提醒')
    email = models.TextField(blank=True)
    expire_at = models.DateField(blank=True, null=True, help_text='过期时间')
    extra = models.TextField(blank=True)
    err = models.TextField(blank=True)

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
        try:
            return json.loads(self.extra)
        except:
            return {}

    def fetch(self):
        cmd = 'echo | openssl s_client -servername %s -connect %s:443 2>/dev/null | openssl x509 -noout -enddate' % (
            self.domain, self.domain)
        s = getcmdoutput(cmd)  # notAfter=Dec  5 02:18:56 2018 GMT
        if '=' not in s:
            self.err = s
            self.save()
            return
        s = s.split('=')[1].strip()
        t = datetime.datetime.strptime(s, '%b %d %H:%M:%S %Y %Z')
        t = timezone.make_aware(t)
        self.expire_at = t.date()

        if self.is_expiring:
            extra = self.extra_data
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

    title = models.CharField(max_length=255, verbose_name='名称', db_index=True, unique=True)
    kind = models.CharField(max_length=255, blank=True, verbose_name='类别')
    unit = models.CharField(max_length=255, blank=True, verbose_name='规格')

    vendor = models.CharField(max_length=255, blank=True, verbose_name='生产单位/进口代理商')
    supplier = models.CharField(max_length=255, blank=True, verbose_name='供应商')

    def __unicode__(self):
        return self.title

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
    group = models.CharField(max_length=255, blank=True, verbose_name='组别')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='最后更新时间')

    is_consume = models.BooleanField(default=False, verbose_name='是否为出货')

    def __unicode__(self):
        return u'%s * %s' % (self.product, self.normal_quantity)

    @property
    def category(self):
        return '出货' if self.is_consume else '采购'

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

    def save(self, *args, **kwargs):
        # 采购数量只能为正
        # 出货数量只能为负
        if self.is_consume != (self.quantity < 0):
            self.quantity = -self.quantity
        super(Purchase, self).save(*args, **kwargs)

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





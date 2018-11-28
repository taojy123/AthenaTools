# -*- coding: utf-8 -*-
import commands
import datetime
import json

from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone


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
        return self.email.strip().split('\n')

    def fetch(self):
        cmd = 'echo | openssl s_client -servername %s -connect %s:443 2>/dev/null | openssl x509 -noout -enddate' % (self.domain, self.domain)
        s = commands.getoutput(cmd)  # notAfter=Dec  5 02:18:56 2018 GMT
        if '=' not in s:
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

    title = models.CharField(max_length=255, blank=True, verbose_name='名称')
    unit = models.CharField(max_length=255, blank=True, verbose_name='规格')
    kind = models.CharField(max_length=255, blank=True, verbose_name='类别')

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = '原材料'
        verbose_name_plural = '原材料'


class Purchase(models.Model):

    user = models.ForeignKey(User, blank=True, null=True, verbose_name='录入者')
    day = models.DateField(null=True, blank=True, default=timezone.localdate, verbose_name='日期')

    product = models.ForeignKey(Product)
    quantity = models.FloatField(default=1, verbose_name='数量')
    vendor = models.CharField(max_length=255, blank=True, verbose_name='生产单位/进口代理商')
    produced_at = models.CharField(max_length=255, blank=True, verbose_name='生产日期')
    exp = models.CharField(max_length=255, blank=True, verbose_name='保质期')
    supplier = models.CharField(max_length=255, blank=True, verbose_name='供应商')
    receipt = models.CharField(max_length=255, blank=True, verbose_name='索证索票')
    expired_quantity = models.CharField(max_length=255, blank=True, verbose_name='过期处理数量')
    remark = models.CharField(max_length=255, blank=True, verbose_name='备注')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='最后更新时间')

    def __unicode__(self):
        return u'%s * %s' % (self.product, self.normal_quantity)

    @property
    def normal_quantity(self):
        if int(self.quantity) == self.quantity:
            return int(self.quantity)
        return self.quantity

    @property
    def kind(self):
        return self.product.kind

    @property
    def title(self):
        return self.product.title

    @property
    def unit(self):
        return self.product.unit

    class Meta:
        verbose_name = '采购记录'
        verbose_name_plural = '采购记录'


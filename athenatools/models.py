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
        return self.remain_days < self.ahead_days

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





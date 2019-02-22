# -*- coding: utf-8 -*-

import StringIO
import HTMLParser
import time

import BeautifulSoup
import dnode
import easyserializer
import xlrd
import xlwt
import json
import os
import urllib
import MySQLdb
import requests
import re
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Sum, F
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse, HttpResponseBadRequest
from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth
from django.utils import timezone

from lazypage.decorators import lazypage_decorator
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
from PIL import Image

from athenatools.models import CertReminder, Purchase, Product, get_normal_quantity, normal_number, Deployment
from athenatools.utils import InMemoryZip


def get_cell(sheet, row, col):
    try:
        return sheet.cell(row, col).value
    except:
        return None


def index(request):
    return render_to_response('index.html', locals())


def xls(request):
    data = request.GET.get('data') or request.POST.get('data') or request.body

    tips = """
    【XLS 云生成】服务，将数据命令以 data 参数形式传入，即可生成 xls 数据文件！
    数据命令为 json 格式数组，每一个数组元素对应一次单元格的写入操作，包含以下属性
    {
        row:    目标单元格行号(从0开始)
        col:    目标单元格列号
        row2:   如果合并单元格，合并区域右下角行号(可选)
        col2:   如果合并单元格，合并区域右下角列号(可选)
        value:  在单元格中填入的数据
    }

    数据示例:
    [{"row": 0, "col": 0, "value": "first"}, {"row": 1, "col": 2, "row2": 3, "col2": 2, "value": "second"}]

    用法示例:
    1. 直接浏览器 GET 请求
    https://tools.athenagu.com/xls/?data=[{"row": 0, "col": 0, "value": "first"}]
    
    2. POST 请求传递 data 参数 
    curl -X POST https://tools.athenagu.com/xls/ -d 'data=[{"row": 0, "col": 0, "value": "first"}]' -o data.xls
    
    3. POST 请求直接传递 json 数据
    curl -X POST https://tools.athenagu.com/xls/ -d '[{"row": 0, "col": 0, "value": "first"}]' -H "Content-Type:application/json" -o data.xls
    
    
    【小插件】
    在含有表格的页面中添加以下代码
    <script src="https://cdn.tslow.cn/AthenaTools/static/js/athena-output.js"></script>
    页面上就会出现 “导出” 按钮，点击后可自动下载当前页面上表格中的数据，生成 xls 文件
    例如这里: https://tools.athenagu.com/cert_reminder/
    更多使用参数可查看 https://cdn.tslow.cn/AthenaTools/static/js/athena-output.js 中的注释说明
    """
    try:
        rs = json.loads(data)
        assert isinstance(rs, list)
    except:
        return render_to_response('xls.html', locals())
        # return HttpResponse(tips, 'text/plain;charset=utf-8')

    wb = xlwt.Workbook()
    ws = wb.add_sheet('sheet1', cell_overwrite_ok=True)

    for r in rs:
        row = r.get('row', 0)
        col = r.get('col', 0)
        row2 = r.get('row2')
        col2 = r.get('col2')
        value = r.get('value', '')

        if row2 and col2:
            assert row <= row2
            assert col <= col2
            ws.write_merge(row, row2, col, col2, value)
        else:
            ws.write(row, col, value)

    s = StringIO.StringIO()
    wb.save(s)
    s.seek(0)
    data = s.read()

    response = HttpResponse(data)
    response['Content-Type'] = 'application/vnd.ms-excel'
    response['Content-Disposition'] = 'attachment;filename="data.xls"'

    return response


RSA_KEY_EXAMPLE = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAxgXY9AGI22MfQPe/VecLzNfga8czch6kNLtIPFO1+ZPPpY6i\n43D2dUKZ8zjpZ/QcOV4CALej19LfnhRWkU9iOomYpGAReevnhVRBcwu0+UHmIVn1\nk+ovjG8XdMY9jKKeWw2Yu8xsb/DIrxJvVO0gce1oN15dDi89cyE1sCeovAM8fXvx\nIxSDsdM4YZRlpxBxJEiCbMJ+gUEdUgQBJmOkuKsBGUfFVtjvjse+g49qcqa4vWq4\n/Ft6mHSYJMsBQAIaJmjNlGuav1ocE+4ryp7LL9OSootjntSIDzxo2VfVQFsOL3h8\nlSAyTr8j6pEDxy1xfIsNHvjuNHarF2h/r5z/UQIDAQABAoIBAH6iyK6quJHMXvVW\nOpc97W7vc0aZmo3ViJ9sUXK6+foEi9tNT1/yIrq0f+1qLOHc25vYQaGhzva7lWPr\nj7zXrnLPAb3E7ggxU9sRGdXv26k3emtDs2gHcKb3eGGmUUA50tlZ5Z3bylEAA+bp\n/Casin4xG9+kyg/DKCITT9k6U47/xsXvZ1KdPmAYHnUHIw0H3ntxVWNNscjOHz0K\nPKam6x9hC8DVmRDfRO25YGb3Aq1SQZHk8pADnEOYGkVJhe4E/Z8xG49nHXXTcdFr\nPApJm85pip2rsgZP1tP5DfAGs1UkU9jFUF9QYQuh3E+K558cdOpBd5O6zV/DXtad\nUAfgSBECgYEA5oxSCzVZzdkANiCMVmJ6N+trS3kcA6eyKlHMNwJRKhgP1+toYCg7\nvDR5vT7a1+LQKeyLOqFVX9JaaE77X6b/hovneZblb/K0Io6aLuFPXzc1EasGYhZ1\nmOkMGKnjM9T9QHJXIswMHZqArCmOohUABdGqW/YXS/KkI5OiON3DwH0CgYEA2+JO\nt3nOB9Q0FTBBOcLyfycdaBUDQBq6JvGfYVGvQlORlRlqCIMR4VtHuAd5dB9t/hmW\nd6xm75Z2XDJQiwffwYrEHEADfVVhbLvydj9I+JAkh4HnlOkuJCOISjeZmea0dFOd\n1zggb377MuAo4vguzQV9gJYTNQoUpyF7EZqlpmUCgYB8y4oBnTBuV79gjT/J5uaH\nbHyYzwbWB6lOdRaY1D1BDuNMmpXWLxEesD0RrnthjtnlR7CZ3QjMpJ3hhpdVUJ1S\npFp5G7A4Z+UQK6bUJ4wCW2zzkmMTJ1simUu98gAVZ35qqzn1kQQh5icuihQ2Mi3f\n+H1B6DT2HHKy+1A9ffVfNQKBgQCcDm0RuOgqFEh2tU3Fof+bkPZE9YzeBVoS46/b\nUS8S4t7TNDtWGTgqei9XhC6F5PyauCxbeUeBSYdtfeQ+GHONGGCBMEmJvXwswOOf\nWuD+UMcsSV1ECY7O5U0IZ5eja+KtIN9IbTRQDY5ZGFDMbZpBtmDRTzIIlcP8rj17\nTAe/JQKBgQCkcFdvvPKgWRhiMpTjo1klyeI2saXiN1C8wIF24P9aXPzGrS4+iFxC\niN7MGIL/AA6/Bo3DVrmPc5spAiFOn5M2URapOnm3RVTJPUWD5OzLk/6AlpOx2YaK\n+IUgKgPeZjBZhlOGPJD3WlxAy/xvPdDGhgBrSq8aXto8lTIk5eveBw==
-----END RSA PRIVATE KEY-----"""


def rsa(request):
    rsa_key = rsa_pub_key = ''

    if request.method == 'POST':
        rsa_key = request.POST.get('rsa_key', '').strip()
        submit = request.POST.get('submit')

        if submit == u'私钥示例':
            rsa_key = RSA_KEY_EXAMPLE
            return render_to_response('rsa.html', locals())
        elif submit == u'私钥提取公钥':
            if not rsa_key:
                msg = u'请填写私钥'
                return render_to_response('rsa.html', locals())
            open('/tmp/r.key', 'w').write(rsa_key)
        else:
            # rsa_key = os.popen('openssl genrsa -out').read()
            os.popen('openssl genrsa -out /tmp/r.key')
            rsa_key = open('/tmp/r.key').read()

        print 'rsa key:'
        print rsa_key

        rsa_pub_key = os.popen('openssl rsa -in /tmp/r.key -pubout').read()

        print 'rsa pub key'
        print rsa_pub_key

        if not rsa_pub_key:
            msg = u'私钥填写有误，请参考私钥示例'

    return render_to_response('rsa.html', locals())


def mysql(request):
    agent = request.META.get('HTTP_USER_AGENT', '')
    print agent

    if len(agent) < 60:
        default_format = 'json'
    else:
        default_format = 'html'

    if 'mozilla' in agent.lower():
        default_format = 'html'

    host = request.POST.get('host', 'taojy123.cn')
    port = int(request.POST.get('port', 3306))
    username = request.POST.get('username', 'test')
    password = request.POST.get('password', 'test')
    database = request.POST.get('database', 'testdb')
    charset = request.POST.get('charset', 'utf8mb4')
    
    sql = request.POST.get('sql', 'SELECT VERSION()')
    f = request.POST.get('format', default_format)  # html / json

    result = error = tips = db = ''

    if request.method == 'POST':
        try:
            db = MySQLdb.connect(
                host=host,
                port=port,
                user=username,
                passwd=password,
                db=database,
                charset=charset,
            )
            cursor = db.cursor()

            if sql.count(';') < 2:
                cursor.execute(sql)
            else:
                for sub_sql in sql.strip('').strip(';').split(';'):
                    cursor.execute(sub_sql)

            db.commit()
            result = cursor.fetchall()
            print(result)
        except Exception as e:
            error = str(e)
        finally:
            if db:
                db.close()
    else:
        tips = 'POST parameters: host, port, username, password, database, sql ...'

    if f == 'html':
        result = str(result)
        return render_to_response('mysql.html', locals())
    elif f == 'json':
        r = {
            'result': result,
            'error': error,
            'tips': tips
        }
        return JsonResponse(r)
    else:
        assert False, 'format must in [ html / json ]'


def pdf(request):
    tips = 'form-data: file - <file>, method - "merge"/"split"'

    file = request.FILES.get('file')
    files = request.FILES.getlist('file')
    method = request.POST.get('method')

    print(file)
    print(files)
        
    if file and method:

        if method == 'split':
            imz = InMemoryZip()
            pdf = PdfFileReader(file, strict=False)
            n = 0
            for page in pdf.pages:
                output = PdfFileWriter()
                output.addPage(page)
                s = StringIO.StringIO()
                output.write(s)
                s.seek(0)
                data = s.read()
                n += 1
                name = 'split/%d.pdf' % n
                imz.append(name, data)
            data = imz.read()
            response = HttpResponse(data)
            response['Content-Type'] = 'application/zip'
            response['Content-Disposition'] = 'attachment;filename="split.zip"'
            return response

        elif method == 'merge':
            merger = PdfFileMerger(strict=False)
            files.sort(key=lambda f:f.name)  # 虽然这里默认应该就是按照文件名排序的 但还是写一下保险一点
            for f in files:
                merger.append(f)
            s = StringIO.StringIO()
            merger.write(s)
            s.seek(0)
            data = s.read()
            response = HttpResponse(data)
            response['Content-Type'] = 'application/pdf'
            response['Content-Disposition'] = 'attachment;filename="merge.pdf"'
            return response

    return render_to_response('pdf.html', locals())


def cert_reminder(request):

    if request.GET.get('fetch'):
        for reminder in CertReminder.objects.all():
            reminder.fetch()

    user = request.user

    reminders = list(CertReminder.objects.filter(user__isnull=True).order_by('-id'))

    if user.is_authenticated():
        reminders += list(CertReminder.objects.filter(user=user).order_by('-id'))

    return render_to_response('cert_reminder.html', locals())


def cert_reminder_detail(request, reminder_id):

    reminder_id = int(reminder_id)

    if reminder_id:
        reminder = get_object_or_404(CertReminder, id=reminder_id)
    else:
        reminder = CertReminder()

    if reminder.is_private and reminder.user != request.user:
        return HttpResponseRedirect('/login/?next=/cert_reminder/%s/' % reminder_id)

    if request.method == 'POST':

        kind = request.POST.get('kind')
        domain = request.POST.get('domain')
        ahead_days = request.POST.get('ahead_days')
        email = request.POST.get('email')
        action = request.POST.get('action')

        if action == u'删除':
            reminder.delete()
            return HttpResponseRedirect('/cert_reminder/')

        if not reminder.id and kind == 'private':
            reminder.user = request.user

        domain = domain.strip().replace('https://', '').strip('/').split('/')[0]
        reminder.domain = domain
        reminder.ahead_days = int(ahead_days)
        reminder.email = email
        reminder.save()

        reminder.fetch()

        return HttpResponseRedirect('/cert_reminder/')

    return render_to_response('cert_reminder_detail.html', locals())


def slim(request):

    tips = 'form-data: img - <file>, size - <int>, kind - "img"/"url"'

    img = request.FILES.get('img')
    size = request.POST.get('size')
    kind = request.POST.get('kind', 'img')

    if not img:
        # return HttpResponse(u'<script>alert("未选择图片，请后退重试");location.href="/"</script>')
        return render_to_response('slim.html', locals())

    name = img.name

    ext = name.split('.')[-1].lower()

    if ext == 'jpg':
        ext = 'jpeg'

    im = Image.open(img)
    w, h = im.size

    try:
        size = int(float(size)) * 1000
    except:
        size = 1000 * 1000

    print 'target:', size

    s = StringIO.StringIO()

    for i in range(10, 0, -1):
        wt = int(w * i / 10)
        ht = int(h * i / 10)
        imt = im.resize((wt, ht), 1)
        s = StringIO.StringIO()

        try:
            imt.save(s, ext)
        except Exception as e:
            return HttpResponse(str(e))

        sizet = s.len

        print sizet

        if sizet < size:
            break

    s.seek(0)
    data = s.read()

    if kind == 'img':
        response = HttpResponse(data)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename="%s"' % name.encode('gbk')
        return response

    elif kind == 'url':
        name = '%s.%s' % (uuid.uuid4().hex, ext)
        open('./static/img/%s' % name, 'wb').write(data)
        url = '%s://%s/static/img/%s' % (request.scheme, request.get_host(), name)
        return HttpResponse(url)

    else:
        return HttpResponseBadRequest('invalid kind')


def wb(request):

    img = request.FILES.get('img')
    small = request.POST.get('small')

    pic_path = request.POST.get('pic_path')
    white = request.POST.get('white')

    if pic_path and white and os.path.exists(pic_path):
        im = Image.open(pic_path)
        wr = int(white.split(',')[0])
        wg = int(white.split(',')[1])
        wb = int(white.split(',')[2])

        w, h = im.size

        for i in range(w):
            for j in range(h):
                color = list(im.getpixel((i, j)))
                r = color[0]
                g = color[1]
                b = color[2]
                r2 = int(255 * r / wr)
                g2 = int(255 * g / wg)
                b2 = int(255 * b / wb)
                if r2 > 255:
                    r2 = 255
                if g2 > 255:
                    g2 = 255
                if b2 > 255:
                    b2 = 255
                color[0] = r2
                color[1] = g2
                color[2] = b2
                color = tuple(color)
                im.putpixel((i, j), color)

        im.save(pic_path)
        pic_url = pic_path.strip('.')
        pic_url_t = pic_url + '?t=' + str(time.time())
        name = pic_url.split('/')[-1]
        step = 3
        return render_to_response('wb.html', locals())

    if img:
        name = img.name.lower()
        name = name.encode('utf8')
        ext = name.split('.')[-1]
        if ext not in ['jpg', 'jpeg', 'png', 'gif']:
            return HttpResponseBadRequest('请上传正确的图片文件!')

        pic_path = './static/wb/' + name
        destination = open(pic_path, 'wb+')
        for chunk in img.chunks():
            destination.write(chunk)
        destination.close()

        pic_url = '/static/wb/' + name
        im = Image.open(pic_path)
        w, h = im.size
        if w > 600:
            pic_w = 600
            pic_h = int(h * 600 / w)
        else:
            pic_w = w
            pic_h = h

        if small:
            im = im.resize((pic_w, pic_h), 1)
            im.save(pic_path)

        step = 2
        return render_to_response('wb.html', locals())

    step = 1
    return render_to_response('wb.html', locals())


def purchase(request):
    return render_to_response('purchase.html', locals())


def purchase_statistics(request):
    error = request.GET.get('error', '')
    submit = request.GET.get('submit', '')
    begin = request.GET.get('begin', (timezone.localdate() - timezone.timedelta(days=30)).replace(day=16))  # 默认上月16日
    end = request.GET.get('end', timezone.localdate())
    product_ids = request.GET.getlist('product_id', [])
    kinds = request.GET.getlist('kind', [])

    product_ids = [int(n) for n in product_ids]
    kinds = [str(n) for n in kinds]

    products = Product.objects.order_by('kind', 'title')
    all_kinds = products.values_list('kind', flat=True).order_by('kind').distinct()

    purchases = Purchase.objects.select_related('product', 'user').filter(day__gte=begin, day__lte=end).order_by('-day', 'product__kind', 'product__title')

    if product_ids:
        purchases = purchases.filter(product__id__in=product_ids)

    if kinds:
        purchases = purchases.filter(product__kind__in=kinds)

    table = 0
    if submit == u'结存统计':
        table = 1

        wb = xlwt.Workbook()
        ws = wb.add_sheet(u'结存统计')

        ws.write(0, 0, u'统计时间')
        ws.write(0, 1, u'%s 至 %s' % (begin, end))
        ws.write(1, 0, u'结存数量统计')
        ws.write(2, 0, u'类别')
        ws.write(2, 1, u'原材料名称')
        ws.write(2, 2, u'规格')
        ws.write(2, 3, u'初始留存')
        ws.write(2, 4, u'采购数量')
        ws.write(2, 5, u'出货数量')
        ws.write(2, 6, u'结存数量小计')

        begin = timezone.datetime.strptime(str(begin), '%Y-%m-%d').date()
        end = timezone.datetime.strptime(str(end), '%Y-%m-%d').date()

        pids = purchases.values_list('product_id', flat=True)

        products = Product.objects.filter(id__in=pids).order_by('kind', 'title')

        # 将所有 purchase 通过一个 sql 查出来存下来
        # 这样就不用每次之后算库存执行一条 sql
        # 但是！随着系统中的 purchase 记录数量增多，这种方法的速度会逐渐下降
        # 就目前来看还是一种很好的优化方法
        purchases = Purchase.objects.filter(product_id__in=pids, day__lte=end).order_by('day')
        rs = {}
        for p in purchases:
            product_id = p.product_id
            if product_id not in rs:
                rs[product_id] = []
            r = (p.day, p.is_consume, p.quantity)
            rs[product_id].append(r)

        i = 3
        for product in products:

            # # 普通的取库存方法，每次都需要执行 sql
            # remain_count = get_normal_quantity(product.purchase_set.filter(day__lt=begin))
            # purchase_count = get_normal_quantity(product.purchase_set.filter(day__gte=begin, day__lte=end, is_consume=False))
            # consume_count = get_normal_quantity(product.purchase_set.filter(day__gte=begin, day__lte=end, is_consume=True))
            # stock = get_normal_quantity(product.purchase_set.filter(day__lte=end))

            remain_count = purchase_count = consume_count = stock = 0
            for day, is_consume, quantity in rs[product.id]:
                if day < begin:
                    remain_count += quantity
                elif is_consume:
                    consume_count += quantity
                else:
                    purchase_count += quantity
                stock += quantity

            assert normal_number(remain_count + purchase_count + consume_count) == normal_number(stock), (
                product, remain_count, purchase_count, consume_count, stock)

            product.remain_count = remain_count
            product.purchase_count = normal_number(purchase_count)
            product.consume_count = normal_number(consume_count)
            product.stock = normal_number(stock)

            ws.write(i, 0, product.kind)
            ws.write(i, 1, product.title)
            ws.write(i, 2, product.unit)
            ws.write(i, 3, remain_count)
            ws.write(i, 4, normal_number(purchase_count))
            ws.write(i, 5, normal_number(consume_count))
            ws.write(i, 6, normal_number(stock))

            i += 1

        del rs

        s = StringIO.StringIO()
        wb.save(s)
        s.seek(0)
        data = s.read()
        response = HttpResponse(data)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename="data2.xls"'
        # return response

    if submit == u'逐日统计':
        table = 2
        url = '/purchase/preview/?begin=%s&end=%s' % (begin, end)
        for product_id in product_ids:
            url += '&product_id=%d' % product_id
        print(url)
        return HttpResponseRedirect(url)

    return render_to_response('purchase_statistics.html', locals())


def purchase_statistics_groups(request):

    product_id = request.GET.get('product_id')
    begin = request.GET.get('begin')
    end = request.GET.get('end')

    product = Product.objects.get(id=product_id)
    purchases = product.purchase_set.filter(day__gte=begin, day__lte=end)

    lines = purchases.order_by('group').values('group').distinct()

    for line in lines:
        group = line['group']
        queryset = purchases.filter(group=group)
        line['purchase_count'] = get_normal_quantity(queryset.filter(is_consume=False))
        line['consume_count'] = get_normal_quantity(queryset.filter(is_consume=True))
        line['total_count'] = get_normal_quantity(queryset)
        line['purchases'] = queryset.filter(is_consume=False).order_by('day')

    return render_to_response('purchase_statistics_groups.html', locals())


def purchase_entry(request):
    u = request.GET.get('u', '')
    k = request.GET.get('k', '')
    msg = request.GET.get('msg', '')
    user = request.user
    if user.is_anonymous():
        user = None

    if u and k:
        u = auth.authenticate(username=u, password=k)
        if u and user.is_active:
            auth.login(request, u)
            user = u

    t = timezone.now() - timezone.timedelta(seconds=5)
    p = Purchase.objects.filter(user=user, created_at__gt=t).order_by('-id').first()
    if p:
        msg = u'%s 录入成功！' % p

    today = timezone.localdate()
    products = Product.objects.order_by('kind', 'title')

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = float(request.POST.get('quantity'))
        produced_at = request.POST.get('produced_at')
        exp = request.POST.get('exp')
        receipt = request.POST.get('receipt')
        expired_quantity = request.POST.get('expired_quantity')
        group = request.POST.get('group')
        day = request.POST.get('day')
        consume_quantity = request.POST.get('consume_quantity')

        if quantity < 0:
            return HttpResponseRedirect('/purchase/entry/?msg=数量必须大于0')

        if not product_id:
            return HttpResponseRedirect('/purchase/entry/?msg=请选择原材料')

        if not produced_at:
            return HttpResponseRedirect('/purchase/entry/?msg=请输入生产日期')

        if not exp:
            return HttpResponseRedirect('/purchase/entry/?msg=请输入保质期')

        if not group:
            return HttpResponseRedirect('/purchase/entry/?msg=请输入组别')

        if not day:
            return HttpResponseRedirect('/purchase/entry/?msg=请输入日期')

        if not consume_quantity:
            return HttpResponseRedirect('/purchase/entry/?msg=请输入随即出货数量，不出货请填0')

        Purchase.objects.create(
            user=user,
            product_id=product_id,
            quantity=quantity,
            produced_at=produced_at,
            exp=exp,
            receipt=receipt,
            expired_quantity=expired_quantity,
            group=group,
            day=day,
        )

        if consume_quantity:
            consume_quantity = float(consume_quantity)
            if consume_quantity > 0:
                consume_quantity = -consume_quantity
            Purchase.objects.create(
                user=user,
                product_id=product_id,
                quantity=consume_quantity,
                day=day,
                is_consume=True,
            )

        return HttpResponseRedirect('/purchase/entry/?t=%s' % int(time.time()))

    return render_to_response('purchase_entry.html', locals())


def purchase_list(request):
    all = request.GET.get('all', False)
    user = request.user
    if user.is_anonymous():
        user = None

    purchases = Purchase.objects.filter(user=user).order_by('id')

    delete_id = request.POST.get('delete_id')
    if delete_id:
        purchases.filter(id=delete_id).delete()
        return HttpResponseRedirect('/purchase/list/')

    if not all:
        count1 = purchases.count()
        purchases = purchases.filter(created_at__gt=timezone.localdate())
        count2 = purchases.count()
        has_remain = count1 > count2

    return render_to_response('purchase_list.html', locals())


def purchase_preview(request):

    output = request.GET.get('output', 0)
    begin = request.GET.get('begin')
    end = request.GET.get('end')
    product_ids = request.GET.getlist('product_id', [])
    kinds = request.GET.getlist('kind', [])

    product_ids = [int(n) for n in product_ids]
    kinds = [str(n) for n in kinds]

    purchases = Purchase.objects.filter(day__gte=begin, day__lte=end).order_by('day')

    if product_ids:
        purchases = purchases.filter(product__id__in=product_ids)

    if purchases.exists():
        begin = purchases.order_by('day').first().day
        end = purchases.order_by('day').last().day

    product_ids = purchases.values_list('product_id', flat=True).distinct()

    products = Product.objects.filter(id__in=product_ids).order_by('kind', 'title')

    purchases = Purchase.objects.filter(product_id__in=product_ids, day__lte=end).order_by('day')
    rs = {}
    for p in purchases:
        product_id = p.product_id
        if product_id not in rs:
            rs[product_id] = []
        r = (p.day, p.is_consume, p.quantity)
        rs[product_id].append(r)

    for product in products:
        queryset = Purchase.objects.filter(product=product)

        stock_begin = stock_end = 0
        for day, is_consume, quantity in rs[product.id]:
            if day < begin:
                stock_begin += quantity
            stock_end += quantity

        product.stock_begin = normal_number(stock_begin)
        product.stock_end = normal_number(stock_end)

        # product.stock_begin = get_normal_quantity(queryset.filter(day__lt=begin))
        # product.stock_end = get_normal_quantity(queryset.filter(day__lte=end))

    output_url = request.get_full_path()
    if "?" in output_url:
        output_url += '&output=1'
    else:
        output_url += '?output=1'

    if output:

        wb = xlwt.Workbook()

        if not products:
            ws = wb.add_sheet(u'暂无记录')

        for product in products:

            ws = wb.add_sheet(product.title)

            ws.write(0, 0, u'类别')
            ws.write(0, 1, product.kind)
            ws.write(0, 2, u'原材料名称')
            ws.write(0, 3, product.title)
            ws.write(0, 4, u'规格')
            ws.write(0, 5, product.unit)

            ws.write(1, 0, u'留存库存')
            ws.write(1, 1, product.stock_begin)

            ws.write(2, 0, u'日期')
            ws.write(2, 1, u'进货数量')
            ws.write(2, 2, u'出货数量')
            ws.write(2, 3, u'结存')
            ws.write(2, 4, u'摘要')
            ws.write(2, 5, u'组别')

            # purchases = Purchase.objects.filter(product=product, day__lte=end)

            day = begin
            i = 3
            while True:
                if day > end:
                    break

                purchase_count = consume_count = stock = 0
                for d, is_consume, quantity in rs[product.id]:
                    if d > day:
                        break
                    stock += quantity
                    if d == day:
                        if is_consume:
                            consume_count += quantity
                        else:
                            purchase_count += quantity

                # purchase_count = get_normal_quantity(purchases.filter(day=day, is_consume=False))
                # consume_count = get_normal_quantity(purchases.filter(day=day, is_consume=True))
                # stock = get_normal_quantity(purchases.filter(day__lte=day))

                if purchase_count == consume_count == 0:
                    day += timezone.timedelta(days=1)
                    continue

                ws.write(i, 0, str(day))
                ws.write(i, 1, normal_number(purchase_count))
                ws.write(i, 2, normal_number(consume_count))
                ws.write(i, 3, normal_number(stock))
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
        response['Content-Disposition'] = 'attachment;filename="data1.xls"'
        return response

    return render_to_response('purchase_preview.html', locals())


def purchase_preview_sub(request):

    begin = request.GET.get('begin')
    end = request.GET.get('end')
    product_id = request.GET.get('product_id')

    begin = timezone.datetime.strptime(str(begin), '%Y-%m-%d').date()
    end = timezone.datetime.strptime(str(end), '%Y-%m-%d').date()

    product = Product.objects.get(id=product_id)
    purchases = Purchase.objects.filter(product=product, day__lte=end).order_by('day')

    rs = []
    for p in purchases:
        r = (p.day, p.is_consume, p.quantity)
        rs.append(r)

    lines = []
    day = begin
    while True:
        if day > end:
            break

        purchase_count = consume_count = stock = 0
        for d, is_consume, quantity in rs:
            if d > day:
                break
            stock += quantity
            if d == day:
                if is_consume:
                    consume_count += quantity
                else:
                    purchase_count += quantity

        # purchase_count = get_normal_quantity(purchases.filter(day=day, is_consume=False))
        # consume_count = get_normal_quantity(purchases.filter(day=day, is_consume=True))
        # stock = get_normal_quantity(purchases.filter(day__lte=day))

        # if purchase_count == consume_count == 0:
        #     day += timezone.timedelta(days=1)
        #     continue

        line = {
            'day': day,
            'purchase_count': normal_number(purchase_count),
            'consume_count': normal_number(consume_count),
            'stock': normal_number(stock),
        }
        lines.append(line)
        day += timezone.timedelta(days=1)

    return render_to_response('purchase_preview_sub.html', locals())


def purchase_preview_modify(request):
    product_id = request.POST.get('product_id')
    day = request.POST.get('day')
    is_consume = int(request.POST.get('is_consume', 0))
    quantity = float(request.POST.get('quantity', 0))

    assert is_consume == (quantity <= 0), (product_id, day, is_consume, quantity)

    queryset = Purchase.objects.filter(product_id=product_id, day=day, is_consume=is_consume)
    old_quantity = queryset.aggregate(Sum('quantity')).get('quantity__sum') or 0
    diff = quantity - old_quantity

    ps = Purchase.objects.filter(product_id=product_id, day=day, is_consume=is_consume).order_by('-id')
    if not ps:
        product = Product.objects.get(id=product_id)
        p = product.purchase_set.create(day=day, quantity=0, is_consume=is_consume)
        ps = [p]

    for p in ps:
        p_quantity = p.quantity
        p.quantity = p.quantity + diff
        change = diff
        if (is_consume and p.quantity > 0) or (not is_consume and p.quantity < 0):
            p.quantity = 0
            change = -p_quantity
        diff = diff - change
        p.save()
        if diff == 0:
            break

    return HttpResponse('ok')


def nakedoor(request):

    doors = [
        {'id': 112, 'name': '南京路 4楼大门', 'latitude': '31.23073078', 'longitude': '121.45577079'},
        {'id': 72, 'name': '南京路 5楼大门', 'latitude': '31.23073078', 'longitude': '121.45577079'},
        {'id': 76, 'name': '南京路 3楼 储藏室', 'latitude': '31.23073078', 'longitude': '121.45577079'},
        {'id': 148, 'name': '南京路 3楼大门', 'latitude': '31.23073078', 'longitude': '121.45577079'},
        {'id': 80, 'name': '南京路 4楼 消防门', 'latitude': '31.23073078', 'longitude': '121.45577079'},
        {'id': 111, 'name': '南京路 4楼侧门 ', 'latitude': '31.23073078', 'longitude': '121.45577079'},
        {'id': 69, 'name': '南京路 5楼 消防门', 'latitude': '31.23073078', 'longitude': '121.45577079'},
        {'id': 73, 'name': '南京路 6楼天台门', 'latitude': '31.23073078', 'longitude': '121.45577079'},
        {'id': 471, 'name': '新天地 3楼大门', 'latitude': '31.22137423', 'longitude': '121.4704126'},
        {'id': 424, 'name': '新天地 5楼 运动房', 'latitude': '31.22137423', 'longitude': '121.4704126'},
        {'id': 435, 'name': '新天地 5楼 电梯门', 'latitude': '31.22137423', 'longitude': '121.4704126'},
        {'id': 456, 'name': '新天地 5楼 自动扶梯门', 'latitude': '31.22137423', 'longitude': '121.4704126'},
        {'id': 393, 'name': '新天地 储藏室', 'latitude': '31.22137423', 'longitude': '121.4704126'},
        {'id': 491, 'name': '新天地 6楼 电梯门', 'latitude': '31.22137423', 'longitude': '121.4704126'},
        {'id': 363, 'name': '复兴路 3楼大门', 'latitude': '31.21466431', 'longitude': '121.45363791'},
        {'id': 315, 'name': '复兴路 静音室', 'latitude': '31.21466431', 'longitude': '121.45363791'},
        {'id': 367, 'name': '复兴路 4楼大门', 'latitude': '31.21466431', 'longitude': '121.45363791'},
        {'id': 4142, 'name': '复兴路 5楼 露台入口', 'latitude': '31.21466431', 'longitude': '121.45363791'},
        {'id': 4143, 'name': '复兴路 5楼 主入口', 'latitude': '31.21466431', 'longitude': '121.45363791'},
        {'id': 3286, 'name': '北京路 2楼 大门', 'latitude': '31.23073174', 'longitude': '121.44673331'},
        {'id': 2972, 'name': '北京路 3楼 西大门 2', 'latitude': '31.23073174', 'longitude': '121.44673331'},
        {'id': 2987, 'name': '北京路 3楼 梨子 入口', 'latitude': '31.23073174', 'longitude': '121.44673331'},
        {'id': 2992, 'name': '北京路 3楼 香蕉 入口', 'latitude': '31.23073174', 'longitude': '121.44673331'},
        {'id': 2993, 'name': '北京路 3楼 大门', 'latitude': '31.23073174', 'longitude': '121.44673331'},
        {'id': 4205, 'name': '北京路 4楼 消防门', 'latitude': '31.23073174', 'longitude': '121.44673331'},
        {'id': 4206, 'name': '北京路 4楼 西大门 2', 'latitude': '31.23073174', 'longitude': '121.44673331'},
        {'id': 4207, 'name': '北京路 4楼 西大门 1', 'latitude': '31.23073174', 'longitude': '121.44673331'},
        {'id': 4208, 'name': '北京路 4楼 大门', 'latitude': '31.23073174', 'longitude': '121.44673331'},
        {'id': 149, 'name': '湖南路 1楼大门', 'latitude': '31.21047777', 'longitude': '121.43336395'},
        {'id': 152, 'name': '湖南路 1楼 2层入口门', 'latitude': '31.21047777', 'longitude': '121.43336395'},
        {'id': 160, 'name': '湖南路 1楼 消防门', 'latitude': '31.21047777', 'longitude': '121.43336395'},
        {'id': 168, 'name': '湖南路 1楼 花园 ', 'latitude': '31.21047777', 'longitude': '121.43336395'},
        {'id': 155, 'name': '湖南路 2楼 消防门', 'latitude': '31.21047777', 'longitude': '121.43336395'},
    ]

    door_id = request.POST.get('door_id')
    if door_id:
        door_id = int(door_id)

        url = "https://app.nakedhub.cn/nakedhub/api/opendoor/openOrCloseGateforApp"

        header_security_token = 'MTM0MDIxMTA3NTI6MTU0NTAxMzExNTc0NDpkYjQ0ZDM4YWNhNzZjMDY5ODFjYjg0MzQ2NmI0MzI4Zg'  # 关键
        deviceToken = '842be780821d5a05917c2991cadfac36e6453a577e7e2700b775a503ef5a5a18'  # 不重要
        cookie = 'CONTAINERID=94d027fb3a7c2938ffb675b72828b76c133ba6d93c003a51d56abedbed9e2758|W3TfS|W3TfO'  # 不重要

        latitude = '31.23115792407769'
        longitude = '121.4554129355787'

        for door in doors:
            if door['id'] == door_id:
                latitude = door.get('latitude', latitude)
                longitude = door.get('longitude', longitude)
                cookie = door.get('cookie', cookie)

        data = {
            'deviceToken': deviceToken,
            'doorIds': door_id,
            'latitude': latitude,
            'longitude': longitude,
            'locale': 'zh_CN',
            'openOrClose': '1',
        }
        headers = {
            'header_security_token': header_security_token,
            'cookie': cookie,
            'locale': "zh_CN",
            'user-agent': "naked Hub/2.4.0 (iPhone; iOS 11.4.1; Scale/2.00)",
            'host': "app.nakedhub.cn",
            'cache-control': "no-cache",
            'content-type': "application/x-www-form-urlencoded"
        }

        request.session['door_id'] = door_id

        try:
            response = requests.post(url, data=data, headers=headers)
            msg = response.text
            if '"code": 200' in msg:
                msg = 'Success!!! ' + msg
        except Exception as e:
            msg = str(e)

    return render_to_response('nakedoor.html', locals())


def wedoor(request):
    doors = [
        {
            "doorId": "148",
            "doorName": "3th Fl Main Entrance",
            "doorType": "NAKED",
            "canOpen": True
        },
        {
            "doorId": "112",
            "doorName": "4th Fl Main Entrance",
            "doorType": "NAKED",
            "canOpen": True
        },
        {
            "doorId": "76",
            "doorName": "3th Fl Member Storage",
            "doorType": "NAKED",
            "canOpen": True
        },
        {
            "doorId": "73",
            "doorName": "6th Fl Rooftop",
            "doorType": "NAKED",
            "canOpen": True
        },
        {
            "doorId": "72",
            "doorName": "5th Fl Main Entrance",
            "doorType": "NAKED",
            "canOpen": True
        }
    ]

    door_id = request.POST.get('door_id')
    if door_id:

        url = 'https://api.wework.cn/chinaos/doorService/api/v1/fe/door/openNakedDoor'
        data = {
            'doorId': door_id,
            'doorName': 'whatever',
        }
        headers = {
            'authorization': 'X-CAT eyJraWQiOiJFRjRGMjJDMC01Q0IwLTQzNDgtOTY3Qi0wMjY0OTVFN0VGQzgiLCJhbGciOiJFUzI1NiJ9.eyJpc3MiOiJ3d2NoaW5hIiwiYXVkIjoid3djaGluYS1pb3MiLCJzdWIiOiJmZTg2ZjIwMC1mMDZlLTAxMzYtNzYzNC0wMjQyYWMxMTJjMGQiLCJpYXQiOjE1NTA0NTg1OTQsImV4cCI6MTU1MDQ2NTc5NCwianRpIjoiMzM2ZGMyYjUtNzJlMi00ZGZkLWJmZWEtYTgwNzE4ZWZjZTA0IiwidWlkIjoxMzE5NTJ9.pR5KkIkKUtXoILltFqRqtMVa-HY3wTm0NZDBKjW4tusAzAj2fIz8xnQVEY4zlwEfJvWeVIcHRMQTCWmapFaWrw',
        }

        request.session['door_id'] = door_id

        try:
            response = requests.post(url, data=data, headers=headers)
            msg = response.text
            if '"data":true' in msg:
                msg = 'Success!!! ' + msg
        except Exception as e:
            msg = str(e)

    return render_to_response('wedoor.html', locals())


def gopro(request):
    email = request.GET.get('email', 'test@163.com')
    country = request.GET.get('country', 'CN')
    language = request.GET.get('language', 'ZH')

    url = 'https://zh.gopro.com/help/ContactUs'
    r = requests.get(url)
    html = r.text

    # print(html)

    deployment_id, org_id = re.findall(r"liveagent\.init\('.+?', '(.+?)', '(.+?)'\);", html)[0]
    sid = str(uuid.uuid4())
    print(deployment_id, org_id, sid)

    # url = 'https://d.la1-c2-ord.salesforceliveagent.com/chat/rest/Visitor/Availability.jsonp?sid=%s&r=983&Availability.prefix=Visitor&Availability.ids=[573o00000004IhQ,573o00000004IhR,573o00000004IhS,573o00000004IhV,573o00000004IhT,573o00000004IhU,573o00000004IhW,573o00000004IhX,573o00000004IhY,573o00000004IhZ,573o00000004Iha,573o00000004Ihb,573o00000004Ihc,573o00000004Ihi,573o00000004Ihj,573o00000004Ihk,573o00000004Ihd,573o00000004Ihe,573o00000004Ihf,573o00000004Ihg,573o00000004Ihh,573o00000004Ihl,573o00000004Ihm,573o00000004Ihp,573o00000004Ihq,573o00000004Ihn,573o00000004Iho,573o00000004Ihr,573o00000004Iht,573o00000004Ihs,573o00000004Ihu,573o00000004Ihw,573o00000004Ihv,573o00000004Ihx,573o00000004Ihy,573o00000004Ihz,573o00000004Ii0,573o00000004Ii1,573o00000004Ii2,573o00000004Ii3,573o00000004Ii4,573o00000004Ii5,573o00000004Ii8,573o00000004Ii6,573o00000004Ii7,573o00000004Ii9,573o00000004IiA,573o00000004IiD,573o00000004IiE,573o00000004IiB,573o00000004IiC]&callback=liveagent._.handlePing&deployment_id=%s&org_id=%s&version=41' % (sid, deployment_id, org_id)
    # r = requests.get(url)
    # print(r.text)

    vid = re.findall(r'"vid":"(.+?)"', html)[0]
    csrf = re.findall(r'{"name":"checkActiveEntitlement",.+?,"csrf":"(.+?)"}', html)[0]
    print(vid, csrf)

    url = 'https://zh.gopro.com/help/apexremote'
    data = {
        "action": "SupportContactusController",
        "method": "checkActiveEntitlement",
        "data": [email, country, language, "Technical Support"],
        "type": "rpc",
        "tid": 3,
        "ctx": {
            "csrf": csrf,
            "vid": vid,
            "ns": "",
            "ver": 34
        }
    }

    cookies = {
        # 'liveagent_ptid': sid,
        # 'liveagent_sid': sid,
    }

    headers = {
        'referer': 'https://zh.gopro.com/help/ContactUs'
    }

    r = requests.post(url, json=data, headers=headers, cookies=cookies)

    data = r.json()
    print(data)

    status = data[0]['result']['status']
    print(status)

    success = False
    url = ''
    if status == 'OpenFlag':
        button_id = data[0]['result']['id']
        print(button_id)

        success = True
        endpoint = 'https://gp.secure.force.com/liveagent/apex/SC_LiveAgentCustomChatForm?language=#deployment_id=%s&org_id=%s&button_id=%s&session_id=%s' % (
        deployment_id, org_id, button_id, sid)

        url = 'https://gp.secure.force.com/liveagent/apex/SC_LiveAgentPreChatForm?'
        url += urllib.urlencode({'endpoint': endpoint})

        print(url)

    return JsonResponse({'success': success, 'url': url, 'data': data})


def email(request):
    to = request.GET.get('to') or request.POST.get('to')
    title = request.GET.get('title') or request.POST.get('title') or 'AthenaTools'
    content = request.GET.get('content') or request.POST.get('content') or ''
    html = request.GET.get('html') or request.POST.get('html')
    if not to:
        return HttpResponseBadRequest('miss to address')
    to_list = to.split(',')
    r = send_mail(title, content, settings.SERVER_EMAIL, to_list, html_message=html)
    return HttpResponse(r)


def deploy(request, name):

    if name == 'jinns':
        data = json.loads(request.body)
        if 'jinns' not in data['name']:
            return HttpResponse()
        if data['build']['status'] != 'Success':
            return HttpResponse()
        time.sleep(120)

    deployment = get_object_or_404(Deployment, name=name)
    history = deployment.deploy()
    data = easyserializer.obj_to_dict(history, exclude_fields=['pk', 'objects'])
    return JsonResponse(data)


def chart1(request):
    # SYMBOLS = ['circle', 'rect', 'roundRect', 'triangle', 'diamond', 'pin', 'arrow', 'none']
    SYMBOLS = ['emptyCircle', 'emptyTriangle', 'emptyDiamond', 'emptyRoundRect',
               'circle', 'triangle', 'diamond', 'roundRect']

    TEXT1 = u"""
图表标题1	系列A	系列B	系列C
10楼	0.1	0.3	1/2
9楼	0.4	0.4	1/5
8楼	0.3	0.3	0.4
7楼	0.2	0.2	0.4
6楼	0.1	0.4	0.5
5楼	0.2	0.4	0.7
4楼	0.4	0.5	1/10
3楼	0.5	0.2	0.2
2楼	0.7	0.1	1/4
1楼	0.1	0.2	0.6
""".strip()

    text = request.POST.get('text') or TEXT1
    width = request.POST.get('width', 400)
    height = request.POST.get('height', 550)
    interval = request.POST.get('interval', '')

    if text.startswith('\t'):
        text = 'title' + text
    text = text.strip()

    chart = {
        'width': width,
        'height': height,
        'interval': interval,
        'title': '',
        'series': [],
        'categories': [],
    }
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        items = line.split('\t')
        if not chart['series']:
            chart['title'] = items[0]
            i = 0
            for item in items[1:]:
                chart['series'].append({
                    'name': item,
                    'data': [],
                    'symbol': SYMBOLS[i],
                })
                i = (i + 1) % 8
        else:
            chart['categories'].insert(0, items[0])
            items = items[1:]
            for i in range(0, len(items)):
                value = items[i]
                if len(chart['series']) > i:
                    chart['series'][i]['data'].insert(0, value)

    return render_to_response('chart1.html', locals())


def login(request):
    msg = ''
    next_url = request.GET.get('next', '/')
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', '/')
        user = auth.authenticate(username=username, password=password)
        print(username, password)
        if user is not None and user.is_active:
            auth.login(request, user)
            return HttpResponseRedirect(next_url)
        else:
            msg = u'用户名或密码错误'
    return render_to_response('login.html', locals())


def register(request):
    msg = ''
    next_url = request.GET.get('next', '/')
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not username or not password1 or not password2:
            msg = u'请输入用户及密码'

        if password1 != password2:
            msg = u'两次密码不匹配'

        if User.objects.filter(username=username).exists():
            msg = u'该用户名已存在'

        if not msg:
            user = User.objects.create(username=username)
            user.set_password(password1)
            user.save()
            msg = u'注册成功'

    return render_to_response('register.html', locals())


def logout(request):
    if request.user.is_authenticated():
        auth.logout(request)
    return HttpResponseRedirect("/")


@login_required
def password(request):
    msg = ''
    if request.method == 'POST':
        password = request.POST.get('password', '')
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        user = request.user

        if not user.check_password(password):
            msg = u'密码不正确'

        if password1 != password2:
            msg = u'两次密码不匹配'

        if not msg:
            user.set_password(password1)
            user.save()
            return HttpResponseRedirect('/login/')

    return render_to_response('password.html', locals())


def serialize_request(request):
    request_dict = easyserializer.serialize(request, limit_deep=2)
    return request_dict


def instantiate_request(request_dict):
    request = dnode.DNode(request_dict)
    return request


@lazypage_decorator(serialize_method=serialize_request, instantiate_method_path='athenatools.views.instantiate_request')
def test_slow_page(request):
    s = int(request.GET.get('s', 8))
    print('wait', s)
    time.sleep(s)
    page = """
    <html>
    <body>
        此页面需要至少 %s 秒的加载时间!!
    </body>
    </html>
    """ % s
    return HttpResponse(page)



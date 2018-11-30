# -*- coding: utf-8 -*-

import StringIO
import HTMLParser
import time

import BeautifulSoup
import xlrd
import xlwt
import json
import os
import urllib
import MySQLdb
import requests
import re
import uuid

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse, HttpResponseBadRequest
from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth
from django.utils import timezone

from lazypage.decorators import lazypage_decorator
from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger
from PIL import Image

from athenatools.models import CertReminder, Purchase, Product
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

    数据命令示例
    [{"row": 0, "col": 0, "value": "first"}, {"row": 1, "col": 2, "row2": 3, "col2": 2, "value": "second"}]

    请求示例:
    1. 直接浏览器 GET 请求
    https://tools.athenagu.com/xls/?data=[{"row": 0, "col": 0, "value": "first"}, {"row": 1, "col": 2, "row2": 3, "col2": 2, "value": "second"}]

    2. POST 请求传递 data 参数 
    curl -X POST https://tools.athenagu.com/xls/ -d 'data=[{"row": 0, "col": 0, "value": "first"}]' -o data.xls

    3. POST 请求直接传递 json 数据命令 
    curl -X POST https://tools.athenagu.com/xls/ -d '[{"row": 0, "col": 0, "value": "first"}]' -H "Content-Type:application/json" -o data.xls
    
    
    【小插件】
    在含有表格的页面中添加以下代码
    <script src="https://tools.athenagu.com/static/js/athena-output.js"></script>
    页面上就会出现 “导出” 按钮，点击后可自动下载表格数据至 xls 文件
    例如这里: https://tools.athenagu.com/cert_reminder/
    """
    try:
        rs = json.loads(data)
        assert isinstance(rs, list)
    except Exception as e:
        print(e)
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
        elif submit == u'提取公钥':
            if not rsa_key:
                msg = u'请填写私钥'
                return render_to_response('rsa.html', locals())
            open('/tmp/r.key', 'w').write(rsa_key)
        else:
            os.popen('openssl genrsa -out /tmp/r.key').read()
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

        step = 2
        return render_to_response('wb.html', locals())

    step = 1
    return render_to_response('wb.html', locals())


def purchase(request):
    return render_to_response('purchase.html', locals())


def purchase_statistics(request):
    error = request.GET.get('error', '')
    begin = request.GET.get('begin', '')
    end = request.GET.get('end', '')
    purchases = Purchase.objects.all().order_by('day')

    if begin:
        purchases = purchases.filter(day__gte=begin)
    if end:
        purchases = purchases.filter(day__lte=end)

    return render_to_response('purchase_statistics.html', locals())


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
        quantity = request.POST.get('quantity')
        produced_at = request.POST.get('produced_at')
        exp = request.POST.get('exp')
        receipt = request.POST.get('receipt')
        expired_quantity = request.POST.get('expired_quantity')
        remark = request.POST.get('remark')
        day = request.POST.get('day')
        is_consume = request.POST.get('is_consume')

        if is_consume:
            if float(quantity) < 0:
                return HttpResponseRedirect('/purchase/entry/?msg=数量必须大于0')
        else:
            if float(quantity) > 0:
                return HttpResponseRedirect('/purchase/entry/?msg=数量必须小于0')

        if not product_id:
            return HttpResponseRedirect('/purchase/entry/?msg=请选择原材料')

        Purchase.objects.create(
            user=user,
            product_id=product_id,
            quantity=quantity,
            produced_at=produced_at,
            exp=exp,
            receipt=receipt,
            expired_quantity=expired_quantity,
            remark=remark,
            day=day,
            is_consume=is_consume,
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


def nakedoor(request):
    doors = [
        {'id': 112, 'name': '南京路 4楼大门', 'latitude': '31.23115792407769', 'longitude': '121.4554129355787', 'cookie': 'CONTAINERID=94d027fb3a7c2938ffb675b72828b76c133ba6d93c003a51d56abedbed9e2758|W3TfS|W3TfO'},
        {'id': 72, 'name': '南京路 5楼大门', 'latitude': '31.23115792407769', 'longitude': '121.4554129355787', 'cookie': 'CONTAINERID=94d027fb3a7c2938ffb675b72828b76c133ba6d93c003a51d56abedbed9e2758|W3TfS|W3TfO'},
        {'id': 76, 'name': '南京路 3楼 储藏室', 'latitude': '31.23115792407769', 'longitude': '121.4554129355787', 'cookie': 'CONTAINERID=94d027fb3a7c2938ffb675b72828b76c133ba6d93c003a51d56abedbed9e2758|W3TfS|W3TfO'},
        {'id': 148, 'name': '南京路 3楼大门', 'latitude': '31.23115792407769', 'longitude': '121.4554129355787', 'cookie': 'CONTAINERID=94d027fb3a7c2938ffb675b72828b76c133ba6d93c003a51d56abedbed9e2758|W3TfS|W3TfO'},
        {'id': 80, 'name': '南京路 4楼 消防门', 'latitude': '31.23115792407769', 'longitude': '121.4554129355787', 'cookie': 'CONTAINERID=94d027fb3a7c2938ffb675b72828b76c133ba6d93c003a51d56abedbed9e2758|W3TfS|W3TfO'},
        {'id': 111, 'name': '南京路 4楼侧门 ', 'latitude': '31.23115792407769', 'longitude': '121.4554129355787', 'cookie': 'CONTAINERID=94d027fb3a7c2938ffb675b72828b76c133ba6d93c003a51d56abedbed9e2758|W3TfS|W3TfO'},
        {'id': 69, 'name': '南京路 5楼 消防门', 'latitude': '31.23115792407769', 'longitude': '121.4554129355787', 'cookie': 'CONTAINERID=94d027fb3a7c2938ffb675b72828b76c133ba6d93c003a51d56abedbed9e2758|W3TfS|W3TfO'},
        {'id': 73, 'name': '南京路 6楼天台门', 'latitude': '31.23115792407769', 'longitude': '121.4554129355787', 'cookie': 'CONTAINERID=94d027fb3a7c2938ffb675b72828b76c133ba6d93c003a51d56abedbed9e2758|W3TfS|W3TfO'},
        {'id': 471, 'name': '新天地 3楼大门', 'latitude': '31.22137423', 'longitude': '121.4704126'},
        {'id': 424, 'name': '新天地 5楼 运动房', 'latitude': '31.22137423', 'longitude': '121.4704126'},
        {'id': 435, 'name': '新天地 5楼 电梯门', 'latitude': '31.22137423', 'longitude': '121.4704126'},
        {'id': 456, 'name': '新天地 5楼 自动扶梯门', 'latitude': '31.22137423', 'longitude': '121.4704126'},
        {'id': 393, 'name': '新天地 储藏室', 'latitude': '31.22137423', 'longitude': '121.4704126'},
        {'id': 491, 'name': '新天地 6楼 电梯门', 'latitude': '31.22137423', 'longitude': '121.4704126'},
        {'id': 363, 'name': '复兴路 3楼大门', 'latitude': '31.21438791512625', 'longitude': '121.4534790628789', 'cookie': 'CONTAINERID=961c34f8b13aaf6bb4793bc24fc7a31b2871b6ea12ce2c302a06f8f3cdad167e|XACnH|XACkS'},
        {'id': 315, 'name': '复兴路 静音室', 'latitude': '31.21438791512625', 'longitude': '121.4534790628789', 'cookie': 'CONTAINERID=961c34f8b13aaf6bb4793bc24fc7a31b2871b6ea12ce2c302a06f8f3cdad167e|XACnH|XACkS'},
        {'id': 367, 'name': '复兴路 4楼大门', 'latitude': '31.21438791512625', 'longitude': '121.4534790628789', 'cookie': 'CONTAINERID=961c34f8b13aaf6bb4793bc24fc7a31b2871b6ea12ce2c302a06f8f3cdad167e|XACnH|XACkS'},
        {'id': 4142, 'name': '复兴路 5楼 露台入口', 'latitude': '31.21438791512625', 'longitude': '121.4534790628789', 'cookie': 'CONTAINERID=961c34f8b13aaf6bb4793bc24fc7a31b2871b6ea12ce2c302a06f8f3cdad167e|XACnH|XACkS'},
        {'id': 4143, 'name': '复兴路 5楼 主入口', 'latitude': '31.21438791512625', 'longitude': '121.4534790628789', 'cookie': 'CONTAINERID=961c34f8b13aaf6bb4793bc24fc7a31b2871b6ea12ce2c302a06f8f3cdad167e|XACnH|XACkS'},
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

    door_id = int(request.POST.get('door_id'))
    if door_id:

        url = "https://app.nakedhub.cn/nakedhub/api/opendoor/openOrCloseGateforApp"

        latitude = '31.23115792407769'
        longitude = '121.4554129355787'
        cookie = 'CONTAINERID=94d027fb3a7c2938ffb675b72828b76c133ba6d93c003a51d56abedbed9e2758|W3TfS|W3TfO'

        for door in doors:
            if door['id'] == door_id:
                cookie = door.get('latitude', latitude)
                cookie = door.get('longitude', longitude)
                cookie = door.get('cookie', cookie)

        data = {
            'deviceToken': '842be780821d5a05917c2991cadfac36e6453a577e7e2700b775a503ef5a5a18',
            'doorIds': door_id,
            'latitude': latitude,
            'longitude': longitude,
            'locale': 'zh_CN',
            'openOrClose': '1',
        }
        headers = {
            'locale': "zh_CN",
            'user-agent': "naked Hub/2.4.0 (iPhone; iOS 11.4.1; Scale/2.00)",
            'cookie': cookie,
            'host': "app.nakedhub.cn",
            'header_security_token': "MTM0MDIxMTA3NTI6MTUxODc0MzI2MDg4MDo1NGIzYmMzN2NhYmY3OTIzM2Y4NGI3ZWYwMTZmZDc1Zg",
            'cache-control': "no-cache",
            'postman-token': "39372dc5-3d46-d62c-f678-bdbea1952217",
            'content-type': "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(url, data=data, headers=headers)
            msg = response.text
            if '"code": 200' in msg:
                msg = 'Success!!! ' + msg
        except Exception as e:
            msg = str(e)

    return render_to_response('nakedoor.html', locals())


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


def output(request):
    data = request.POST.get('data')
    begin_index = int(request.POST.get('begin_index', 0))
    end_index = int(request.POST.get('end_index', 999))

    html_parser = HTMLParser.HTMLParser()

    wb = xlwt.Workbook()
    ws = wb.add_sheet('output')

    soup = BeautifulSoup.BeautifulSoup(data)

    thead_soup = soup.find('thead')
    th_soups = thead_soup.findAll(['th', 'td'])
    th_soups = th_soups[begin_index:end_index]

    j = 0
    for th_soup in th_soups:
        th = th_soup.getText()
        th = html_parser.unescape(th).strip()
        ws.write(0, j, th)
        j += 1

    tbody_soup = soup.find('tbody')
    tr_soups = tbody_soup.findAll('tr')

    i = 1
    for tr_soup in tr_soups:
        td_soups = tr_soup.findAll(['td', 'th'])
        td_soups = td_soups[begin_index:end_index]

        j = 0
        for td_soup in td_soups:
            td = td_soup.getText()
            td = html_parser.unescape(td).strip()
            ws.write(i, j, td)
            j += 1

        i += 1

    s = StringIO.StringIO()
    wb.save(s)
    s.seek(0)
    data = s.read()
    response = HttpResponse(data)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="output.xls"'

    return response


@lazypage_decorator
def test_slow_page(request):
    s = int(request.GET.get('s', 8))
    print(s)
    time.sleep(s)
    page = """
    <html>
    <body>
        此页面是在请求发起后 %s 秒, 才出现!
    </body>
    </html>
    """ % s
    return HttpResponse(page)



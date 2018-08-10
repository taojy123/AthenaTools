# -*- coding: utf-8 -*-

import StringIO
import HTMLParser
import BeautifulSoup
import xlwt
import json
import os
import urllib

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth

import MySQLdb


import requests
import re
import uuid


def index(request):
    return render_to_response('index.html', locals())


def xls(request):

    data = request.GET.get('data') or request.POST.get('data') or request.body

    tips = """
    【xls 云生成】服务，将数据命令以 data 参数形式传入，即可生成 xls 数据文件！
    数据命令为 json 格式数组，每一个数组元素对应一次单元格的写入操作，包含以下属性
    {
        row:    目标单元格行号(0开始)
        col:    目标单元格列号
        row2:   如果合并单元格，合并区域右下角行号(可选)
        col2:   如果合并单元格，合并区域右下角列号(可选)
        value:  在单元格中填入的数据
    }

    数据命令示例
    [{"row": 0, "col": 0, "value": "first"}, {"row": 1, "col": 2, "row2": 3, "col2": 2, "value": "second"}]

    请求示例:
    1. 直接浏览器 GET 请求
    http://tools.athenagu.com/xls/?data=[{"row": 0, "col": 0, "value": "first"}, {"row": 1, "col": 2, "row2": 3, "col2": 2, "value": "second"}]

    2. POST 请求传递 data 参数 
    curl -X POST http://tools.athenagu.com/xls/ -d 'data=[{"row": 0, "col": 0, "value": "first"}]' -o data.xls

    2. POST 请求直接传递 json 数据命令 
    curl -X POST http://tools.athenagu.com/xls/ -d '[{"row": 0, "col": 0, "value": "first"}]' -H "Content-Type:application/json" -o data.xls
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
    response['Content-Type'] = 'application/octet-stream'
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
        "action":"SupportContactusController",
        "method":"checkActiveEntitlement",
        "data":[email,country,language,"Technical Support"],
        "type":"rpc",
        "tid":3,
        "ctx":{
            "csrf":csrf,
            "vid":vid,
            "ns":"",
            "ver":34
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
        endpoint = 'https://gp.secure.force.com/liveagent/apex/SC_LiveAgentCustomChatForm?language=#deployment_id=%s&org_id=%s&button_id=%s&session_id=%s' % (deployment_id, org_id, sid, button_id)
        
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
            msg = u'username or password error'
    return render_to_response('login.html', locals())


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
            msg = u'old password error'

        if password1 != password2:
            msg = u'two passwords not the same'

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

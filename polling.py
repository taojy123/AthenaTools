import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "athenatools.settings")

import django
django.setup()

import urllib2
import time
from django.utils import timezone

# HOST = 'http://127.0.0.1:8000'
HOST = 'https://tools.athenagu.com'

print('begin run...')

while True:
    print('fetch cert')
    url = '%s/cert_reminder/?fetch=1' % HOST
    print(url)
    p = urllib2.urlopen(url).read()
    print(p)
    print('sleeping')
    print(timezone.now())
    time.sleep(3600 * 5)


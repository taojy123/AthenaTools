FROM python:2.7

#RUN apt-get update && apt-get -y install vim && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

RUN cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime

RUN echo Asia/Shanghai > /etc/timezone

COPY requirements.txt /workspace/requirements.txt

# RUN pip install -r requirements.txt 
RUN pip install -r requirements.txt -i https://pypi.douban.com/simple/

ADD . /workspace

EXPOSE 8000

CMD python manage.py runserver 0.0.0.0:8000


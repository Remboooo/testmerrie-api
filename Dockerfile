FROM tiangolo/uwsgi-nginx:python3.8

ENV UWSGI_INI /app/uwsgi.ini

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

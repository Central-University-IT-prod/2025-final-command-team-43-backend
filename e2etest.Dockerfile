FROM python:3.12.1-alpine

WORKDIR /app

STOPSIGNAL SIGKILL

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY tests/e2e /app

ENTRYPOINT ["py.test"]
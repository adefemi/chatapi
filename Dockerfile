FROM python:3.6

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /chatapi

WORKDIR /chatapi

COPY . /chatapi/

RUN pip install --upgrade pip && pip install pip-tools && pip install -r requirements.txt 
FROM python:3.12-slim-bookworm
LABEL authors="chris"

WORKDIR /app

copy . .

RUN apt-get update
RUN apt-get -y install python3-dev libcups2-dev gcc fontconfig

RUN pip3 install -r requirements.txt

EXPOSE 8013

ENTRYPOINT ["python3", "brother_ql_web.py"]
FROM python:slim-bookworm
LABEL authors="chris"

WORKDIR /app

COPY -exclude=*.lbl -exclude=*.md -exclude=*ignore . .

RUN apt-get update
RUN apt-get -y install python3-dev libcups2-dev gcc fontconfig libdmtx-dev

RUN pip3 install -r requirements.txt

EXPOSE 8013

HEALTHCHECK --interval=120s --timeout=30s --start-period=30s CMD healthyurl http://localhost:8013/health

ENTRYPOINT ["python3", "brother_ql_web.py"]
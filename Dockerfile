FROM python:slim-bookworm
LABEL authors="chris"

WORKDIR /app

# System dependencies for CUPS, fonts, libdmtx and treepoem (requires ghostscript)
RUN apt-get update \
    && apt-get -y install --no-install-recommends \
        python3-dev \
        libcups2-dev \
        gcc \
        fontconfig \
        libdmtx-dev \
        ghostscript \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 8013

HEALTHCHECK --interval=120s --timeout=30s --start-period=30s CMD healthyurl http://localhost:8013/health

ENTRYPOINT ["python3", "brother_ql_web.py"]
FROM python:3.11-slim

WORKDIR /workspace

RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt /workspace/requirements.txt
RUN pip install --no-cache-dir -r /workspace/requirements.txt

EXPOSE 8000

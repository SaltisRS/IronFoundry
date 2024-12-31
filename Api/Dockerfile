FROM python:3.13.1-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /

COPY . /

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["py", "main.py"]
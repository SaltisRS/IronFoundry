FROM python:3.13.1-slim

EXPOSE 443 80

WORKDIR /

COPY . /

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["uvicorn", "app:app"]
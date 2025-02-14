FROM python:3.13.1-slim

EXPOSE 5050:80 4040:80

WORKDIR /Api

COPY . /Api

RUN pip install --no-cache-dir --upgrade -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
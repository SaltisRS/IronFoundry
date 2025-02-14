FROM python:3.13.1-slim
WORKDIR /Bot

COPY . /Bot

RUN pip install --no-cache-dir --upgrade -r requirements.txt


CMD [ "python", "app/main.py" ]
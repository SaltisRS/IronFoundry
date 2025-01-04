FROM python:3.13.1-slim

WORKDIR /ironfoundry

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD [ "python", "app/main.py" ]
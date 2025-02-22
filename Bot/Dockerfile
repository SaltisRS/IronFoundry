FROM python:3.13.1-slim

WORKDIR /Bot


COPY requirements.txt .

# Install dependencies while caching packages
RUN pip install --upgrade pip && \
    pip install --cache-dir /root/.cache/pip -r requirements.txt

# Copy the rest of the application
COPY . .

CMD [ "python", "app/main.py" ]

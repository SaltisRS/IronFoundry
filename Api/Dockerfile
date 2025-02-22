FROM python:3.13.1-slim

EXPOSE 80

WORKDIR /Api

# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install dependencies while caching packages
RUN pip install --upgrade pip && \
    pip install --cache-dir /root/.cache/pip -r requirements.txt

# Copy the rest of the application
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]

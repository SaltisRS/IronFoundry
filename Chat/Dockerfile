FROM python:3.13-alpine


WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --cache-dir /root/.cache/pip -r requirements.txt

# Copy the app code
COPY . .

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

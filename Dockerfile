# Simple container to run the Flask app
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 5050
ENV PYTHONUNBUFFERED=1
CMD ["python", "app.py"]
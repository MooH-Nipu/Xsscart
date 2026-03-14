FROM python:3.11-slim

WORKDIR /xsscart

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && playwright install chromium \
 && playwright install-deps chromium

RUN mkdir -p /var/www/html

COPY . .

EXPOSE 5000
CMD ["python", "run.py"]

FROM python:3.12-slim

WORKDIR /app
COPY . /app

# No pip install needed — this app is pure Python standard library.
# (If you ever add a requirements.txt, uncomment the next line.)
# RUN pip install --no-cache-dir -r requirements.txt

ENV PORT=8000
EXPOSE 8000

CMD ["python", "app.py"]

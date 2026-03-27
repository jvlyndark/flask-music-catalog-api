FROM python:3.11-slim

WORKDIR /app

# Install dependencies before copying source so Docker can cache this layer
# independently of code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# gunicorn binds to 0.0.0.0 so it is reachable from outside the container.
# The worker count is kept at 2 for a dev/demo context; tune for production.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "run:app"]

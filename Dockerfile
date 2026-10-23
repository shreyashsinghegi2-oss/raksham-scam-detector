# The model is trained during this build, so data/raksham_scam_dataset.csv must be present (it is not in the repository).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY data ./data

# Editable install keeps the package in /app/src, which is where the code looks for data/ and models/.
RUN pip install -e ".[serve]"

# Train at build time so the image carries its own model (about 30 seconds).
RUN raksham-train

RUN useradd --create-home app && chown -R app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/health', timeout=4)"
CMD ["uvicorn", "raksham.api:app", "--host", "0.0.0.0", "--port", "8000"]

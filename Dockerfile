FROM python:3.12-slim

WORKDIR /fia_api

# Install fia_api to the container
COPY . /fia_api
RUN apt-get update \
    && apt-get -y install --no-install-recommends libpq-dev gcc \
    && python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir .

CMD ["opentelemetry-instrument", "uvicorn", "fia_api.fia_api:app", "--host", "0.0.0.0", "--port", "80"]

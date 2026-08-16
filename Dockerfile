FROM python:3.13-slim@sha256:ffb752e139c0a19692a43af8d8523b274222dd68eebad5d583b45c2201c6e30a

RUN useradd -ms /bin/bash app

WORKDIR /home/app

ENV PYTHONUNBUFFERED=1 \
	PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app . .
USER app

CMD ["python3", "./app.py"]

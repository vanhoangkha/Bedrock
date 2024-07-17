FROM python:3.10-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*


FROM base AS dependencies

COPY requirements.txt ./app

RUN python --version
RUN pip --version
RUN pip install --upgrade pip
RUN pip --version
RUN pip install -r requirements.txt

FROM dependencies AS deploy

COPY . /app

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]

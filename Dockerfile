FROM python:3.9-slim

RUN echo 'APT::Install-Suggests "0";' >> /etc/apt/apt.conf.d/00-docker
RUN echo 'APT::Install-Recommends "0";' >> /etc/apt/apt.conf.d/00-docker

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# RUN mkdir /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY mass_image_converter.py .
COPY helpers.py .
COPY config.yaml .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "mass_image_converter.py", "--server.port=8501", "--server.address=0.0.0.0"]
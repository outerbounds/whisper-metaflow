FROM --platform=linux/amd64 python:3.10
USER root
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y ffmpeg
USER user
RUN pip install jiwer git+https://github.com/openai/whisper.git pytube==12.1.0 ffmpeg-python==0.2.0 python-dotenv==0.20.0 pydantic==1.10.2


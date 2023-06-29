FROM --platform=linux/amd64 python:3.10
USER root
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install jiwer git+https://github.com/openai/whisper.git pytube==15.0.0 ffmpeg-python==0.2.0 python-dotenv==0.20.0 pydantic==1.10.2 yt-dlp==2023.06.22


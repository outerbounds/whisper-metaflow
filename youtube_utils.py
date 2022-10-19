from pytube import YouTube
import unicodedata
import re
from pydantic import BaseModel
from platform import platform
import torch
import datetime as dt
from metaflow.cards import MetaflowCard

def filenameify(value, allow_unicode=False):
    """
    Adapted from https://github.com/django/django/blob/master/django/utils/text.py.
    Convert to ASCII if 'allow_unicode' is False. 
    Convert spaces or repeated dashes to single underscores. 
    Remove characters that aren't alphanumerics, underscores, or hyphens. 
    Convert to lowercase. 
    Strip leading and trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '_', value).strip('-_')

class YouTubeTranscriptionTask(BaseModel):
    url: str
    filename: str
    model_type: str
    title: str
    author: str
    views: int
    length: int # seconds
    description: str
    id: str
    publish_date: dt.datetime

def make_task(video_url, model_type):
    video = YouTube(video_url)
    return YouTubeTranscriptionTask.parse_obj({
        'url': video.watch_url, 
        'filename': filenameify(video.title), 
        'model_type': model_type,
        'title': video.title,
        'author': video.author,
        'views': video.views,
        'length': video.length,
        'description': video.description,
        'id': video.video_id,
        'publish_date': video.publish_date
    })

from pytube import YouTube
import unicodedata
import re
from pydantic import BaseModel
from platform import platform
import torch
import datetime as dt

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

def get_default_device():
    
    if torch.cuda.is_available():
        return torch.device("cuda")
    
    # elif torch.backends.mps.is_built() :
    #     # https://pytorch.org/blog/introducing-accelerated-pytorch-training-on-mac/
    #     _p = platform()
    #     if _p.startswith('macOS') and float(_p.split('-')[1]) >= 12.3:
    #         return torch.device("mps")
    # this would be nice. still breaks for me :'\
    
    return torch.device("cpu")

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
    transcription_text: str = ''

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

def transcribe_video(transcription_task, output_path = './youtube-audio-files/', quiet=False, device = torch.device('cpu')):
    """
    Extract the audio from the YouTube watch `url` in the `transcription_task`. 
    The audio will be saved locally to `output_path/transcription_task.filename`. 
    Load OpenAI's `whisper` model on `device` and use its automatic transcription capability.
        Note: there are `result` we are not returning that could be added to the flow versioning.
    """
    import whisper
    if not quiet:
        print("Extracting audio from video at {}...".format(transcription_task.url))
    audio = YouTube(transcription_task.url).streams.get_audio_only()
    audio.download(output_path = output_path, filename = transcription_task.filename)
    audio_filename = output_path + transcription_task.filename
    if not quiet:
        print("Loading {} model...".format(transcription_task.model_type))
    model = whisper.load_model(transcription_task.model_type, device = device)
    if not quiet:
        print("Model loaded successfully...")
        print("Transcribing {}...".format(audio_filename))
    result = model.transcribe(audio_filename)
    return result['text']
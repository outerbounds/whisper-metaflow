from metaflow import FlowSpec, step, Parameter, batch, kubernetes, retry
from flow_utils import remote_compute_config
import os
from dotenv import load_dotenv
load_dotenv('.env')

class YouTubeVideoTranscription(FlowSpec):

    url = Parameter(
        'url', type = str, 
        default = os.getenv('DEFAULT_VIDEO_URL', 'https://www.youtube.com/watch?v=OH0Y_DUZu4Y'),
        help = """The watch url of a YouTube video (starting with https://www.youtube.com/watch),
                  or a url to a Playlist (starting with https://www.youtube.com/playlist)."""
    )
    url_filename = Parameter(
        'urls', type = str, 
        default = os.getenv('MANY_URL_FILENAME_DEFAULT', ''),
        help = "A file containing a list of watch urls for YouTube videos."
    )
    model_type = Parameter(
        'model', type = str, 
        default = os.getenv('DEFAULT_MODEL_TYPE', 'tiny'),
        help = """The size of the Whisper variant. 
                  See the current options at https://github.com/openai/whisper/blob/main/whisper/__init__.py#L17-L27"""
    )
 
    @step
    def start(self):

        from pytube import Playlist
        from youtube_utils import make_task

        if self.url_filename == os.getenv('MANY_URL_FILENAME_DEFAULT', ''):

            # single video watch urls look like:
            # 'https://www.youtube.com/watch?v=<VIDEO ID>'
            if self.url.startswith('https://www.youtube.com/watch'):
                self.pending_transcription_task = [
                    make_task(self.url, self.model_type)
                ]

            # playlist urls look like: 
            # 'https://www.youtube.com/playlist?list=<PLAYLIST ID>'
            elif self.url.startswith('https://www.youtube.com/playlist'):
                self.pending_transcription_task = [
                    make_task(video_url, self.model_type)
                    for video_url in Playlist(self.url)
                ]
              
        else: # user passed a list of urls
            self.pending_transcription_task = []
            with open(self.url_filename, 'r') as file:
                self.pending_transcription_task = [
                    make_task(url_line.strip(), self.model_type)
                    for url_line in file
                ]

        self.next(self.transcribe, foreach='pending_transcription_task')

    @remote_compute_config(
        kubernetes if os.getenv('REMOTE_BACKEND', 'batch') == 'kubernetes' else batch, 
        flag = (os.getenv('IS_REMOTE', '0') == '1') or (os.getenv('IS_GPU', '0') == '1')
    )
    @step
    def transcribe(self):
        import whisper
        from youtube_utils import transcribe_video
        self.transcription = self.input
        print("Transcribing video at {}...".format(self.transcription.url))
        self.transcription.transcription_text = transcribe_video(self.transcription)
        self.next(self.postprocess_transcription)

    @step
    def postprocess_transcription(self, parent_steps):
        import pandas as pd
        self.results = pd.DataFrame([_step.transcription.dict() for _step in parent_steps])
        self.next(self.end)

    @step
    def end(self):
        msg = 'Recorded {} transcription(s) in the run.data.results dataframe.'
        print(msg.format(self.results.shape[0]))
    
if __name__ == '__main__':
    YouTubeVideoTranscription()

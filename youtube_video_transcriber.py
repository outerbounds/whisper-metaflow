from metaflow import FlowSpec, step, Parameter, batch, kubernetes, retry
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
                for url_line in file:
                    if url_line.strip().startswith('https://www.youtube.com/playlist'):
                        self.pending_transcription_task.extend([
                            make_task(video_url, self.model_type)
                            for video_url in Playlist(url_line.strip())
                        ])
                    else:
                        self.pending_transcription_task.append(
                            make_task(url_line.strip(), self.model_type)
                        )

        self.next(self.transcribe, foreach='pending_transcription_task')

    @batch(
        cpu = 8, # gpu = 1, 
        memory = int(os.getenv('MEMORY_REQUIRED', '10000')),
        image = os.getenv('CPU_IMAGE', 'eddieob/whisper-cpu:latest'),
        queue = os.getenv('BATCH_QUEUE_CPU')
    )
    @step
    def transcribe(self):
        from youtube_utils import transcribe_video
        self.transcription = self.input
        self.transcription.transcription_text = transcribe_video(self.transcription)
        self.next(self.postprocess)

    @step
    def postprocess(self, parent_steps):
        import pandas as pd
        self.results = pd.DataFrame([_step.transcription.dict() for _step in parent_steps])
        self.next(self.end)

    @step
    def end(self):
        msg = 'Recorded {} transcription(s) in the run.data.results dataframe.'
        print(msg.format(self.results.shape[0]))
    
if __name__ == '__main__':
    YouTubeVideoTranscription()

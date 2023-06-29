from nlp_utils import Mixin
from metaflow import FlowSpec, step, Parameter, kubernetes, card, current
import os
import shutil
import subprocess


class YouTubeVideoTranscription(FlowSpec, Mixin):

    URL = Parameter(
        "url",
        type=str,
        default=os.getenv(
            "DEFAULT_VIDEO_URL", "https://www.youtube.com/watch?v=OH0Y_DUZu4Y"
        ),
        help="""The watch url of a YouTube video (starting with https://www.youtube.com/watch),
                  or a url to a Playlist (starting with https://www.youtube.com/playlist).""",
    )

    URL_FILENAME = Parameter(
        "urls",
        type=str,
        default=os.getenv("MANY_URL_FILENAME_DEFAULT", ""),
        help="A file containing a list of watch urls for YouTube videos.",
    )

    MODEL_TYPE = Parameter(
        "model",
        type=str,
        default=os.getenv("DEFAULT_MODEL_TYPE", "tiny"),
        help="""The size of the Whisper variant.
                  See the current options at https://github.com/openai/whisper/blob/main/whisper/__init__.py#L17-L27""",
    )

    TITLE = Parameter(
        "title",
        type=str,
        default="Metaflow",
        help="The title to be displayed at the top the post processing step's card.",
    )

    MIN_COUNT_W2V = Parameter(
        "min-ct",
        type=int,
        default=1,
        help="The amount of occurences of a term to be included in word2vec embedding visualization.",
    )

    @step
    def start(self):

        from pytube import Playlist, YouTube
        from pytube.exceptions import LiveStreamError
        from youtube_utils import make_task

        if self.URL_FILENAME == os.getenv("MANY_URL_FILENAME_DEFAULT", ""):

            # single video watch urls look like:
            # 'https://www.youtube.com/watch?v=<VIDEO ID>'
            if self.URL.startswith("https://www.youtube.com/watch"):
                _pending_transcription_task = [make_task(self.URL, self.MODEL_TYPE)]

            # playlist urls look like:
            # 'https://www.youtube.com/playlist?list=<PLAYLIST ID>'
            elif self.URL.startswith("https://www.youtube.com/playlist"):
                _pending_transcription_task = [
                    make_task(video_url, self.MODEL_TYPE)
                    for video_url in Playlist(self.URL)
                ]

        else:  # user passed a list of urls
            _pending_transcription_task = []
            with open(self.URL_FILENAME, "r") as file:
                for url_line in file:
                    if url_line.strip().startswith("https://www.youtube.com/playlist"):
                        _pending_transcription_task.extend(
                            [
                                make_task(video_url, self.MODEL_TYPE)
                                for video_url in Playlist(url_line.strip())
                            ]
                        )
                    else:
                        _pending_transcription_task.append(
                            make_task(url_line.strip(), self.MODEL_TYPE)
                        )

        # data validation
        _live_streams = []
        for _transcription_task in _pending_transcription_task:
            try:
                # audio = YouTube(_transcription_task.url).streams.get_audio_only()
                # audio.download(
                #     output_path=self.AUDIO_OUTPUT, filename=_transcription_task.filename
                # )
                audio_filename = self.AUDIO_OUTPUT + _transcription_task.filename
                if not os.path.exists(self.AUDIO_OUTPUT):
                    os.mkdir(self.AUDIO_OUTPUT)
                os.mkdir("tmp")
                os.chdir("tmp")
                subprocess.run(
                    [
                        "yt-dlp",
                        _transcription_task.url,
                        "--extract-audio",
                        "--audio-format",
                        "mp3",
                    ]
                )
                os.chdir("..")
                tmp_filename = os.listdir("tmp")[0]
                shutil.move(f"tmp/{tmp_filename}", audio_filename)
                os.rmdir("tmp")
            except LiveStreamError:
                msg = "{} is a coming live stream, removing it from the pending transcription list."
                print(msg.format(_transcription_task.url))
                _live_streams.append(_transcription_task)

        self.pending_transcription_task = []
        for _task in _pending_transcription_task:
            if _task not in _live_streams:
                self.pending_transcription_task.append(_task)

        self.next(self.transcribe, foreach="pending_transcription_task")

    @kubernetes(cpu=2, memory=12288, image="registry.hub.docker.com/eddieob/whisper")
    @step
    def transcribe(self):
        self.transcription = self.input
        self.transcription_text = self.transcribe_video(self.transcription)
        self.next(self.postprocess)

    @card
    @step
    def postprocess(self, transcribe_steps):
        import pandas as pd
        from metaflow.cards import Image, Table, Markdown
        import matplotlib.pyplot as plt

        # gather documents
        self.documents = []
        task_data = []
        for _step in transcribe_steps:
            task_data.append(_step.transcription.dict())
            self.documents.append(_step.transcription_text)
        self.results = pd.DataFrame(task_data)
        _joined_document = " ".join(document.strip() for document in self.documents)

        # create visualizations
        self.fig, ax = plt.subplots(1, 2, figsize=(16, 8))
        self.fig.suptitle(
            "{} - Wordcloud and Word2vec Embedding".format(self.TITLE), fontsize=32
        )
        _ = self.get_wordcloud_figure(document=_joined_document, fig=self.fig, ax=ax[0])
        _ = self.get_w2v_figure(document=_joined_document, fig=self.fig, ax=ax[1])
        current.card.append(Table([[Image.from_matplotlib(self.fig)]]))

        # show transcription in Metaflow card
        md = [Markdown("# Transcriptions from Whisper {}".format(self.MODEL_TYPE))]
        for i, document in enumerate(self.documents):
            md.extend(
                [
                    Markdown("## *Video Name:* {}".format(task_data[i]["title"])),
                    Markdown(document),
                ]
            )
        current.card.extend(md)
        self.next(self.end)

    @step
    def end(self):
        msg = """
            Fetch the run object from a notebook or script using:
                from metaflow import Flow
                run = Flow('YouTubeVideoTranscription').latest_successful_run
            This flow recorded metadata for {} transcription(s) in the run.data.results dataframe.
            You can access the list of transcriptions using run.data.documents.
            """
        print(msg.format(self.results.shape[0]))


if __name__ == "__main__":
    YouTubeVideoTranscription()

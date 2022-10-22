EXTRA_STOPWORDS = [
    'know', 'think', 'well', 'Yeah', 'way', "I've", 'way', 'type', 'dont',
    'much', 'like', 'oh', 'stuff', "they're", "I'm", 'didnt', "didn't",
    'everyone', 'thinking', 'today', 'um', "we're", 'uh', 'sense', 'did',
    "going", "right", "saying", "sure", "lot", "okay", 'bit', 'ive', 'doesnt'
    "time", "bye bye", 'oftentimes', 'said', 'key', 'right', 'wrong', 'year',
    'hey', 'yeah', 'ill', 'weve', 'nowadays', 'have', 'interestingly', 'years',
    'interesting', 'I', 'pretty', 'question', 'questions', 'good', 'bad', 
    'kind', 'kinds', 'easy', 'start', 'started', 'common', 'want', 'wanted',
    'absolutely', 'day', 'night', 'couple', 'totally', 'set', 'level', "doesn't",
    'point', 'easy', 'hard', 'essential', 'essentially', 'called', 'case',
    'gonna', 'Hugo', 'hugo', 'basically', 'mentioned', 'great', 'fantastic', 'chip',
    'type', 'types', 'happen', 'happening', 'youve', 'ways', 'question', 'answer',
    'coming', 'understand', 'super', ''
]

class Mixin:
    
    SEED = 33
    PCA_COMPONENTS = 2 # plotting for > 2 dim isn't implemented in make_w2v.
    W2V_FIG_FILENAME = './w2v.png'
    AUDIO_OUTPUT = './youtube-audio-files/'
    YELLOW_PURPLE_RECOLOR = False
    WORDCLOUD_FIG_FILENAME = './wordcloud.png'

    def aggregate_stopwords(self, words = EXTRA_STOPWORDS):
        """
        Return a list of stop words. Aggregate across packages
            that are currently installed, text_files, and EXTRA_STOPWORDS. 
        """
        try:
            with open('stop_words_english.txt') as f:
                words += [s.split('\n')[0] for s in f.readlines()]
        except:
            pass
        try:
            from nltk.corpus import stopwords
            words += list(stopwords.words('english'))
        except LookupError:
            pass
        try:
            from gensim.parsing.preprocessing import remove_stopwords, STOPWORDS
            words += list(STOPWORDS)
        except:
            pass
        try:
            import spacy
            words += spacy.load('en_core_web_lg').Defaults.stop_words
        except:
            pass
        return list(set(map(lambda w: w.strip().lower(), words)))

    def get_wordcloud_figure(self, document, fig = None, ax = None, title = ''):
        """
        Make a wordcloud from a document represented as one string.
        Return it as a matplotlib figure.
        """
        import matplotlib.pyplot as plt
        from wordcloud_utils import GroupedColorFunc
        from wordcloud import WordCloud
        wordcloud = WordCloud(
            max_words = 70, 
            max_font_size = 40, 
            background_color='white',
            stopwords = self.aggregate_stopwords(),
            random_state = self.SEED
        ).generate(document)
        if fig is None or ax is None:
            fig, ax = plt.subplots(1,1)
        plt.axis("off")
        
        if self.YELLOW_PURPLE_RECOLOR:
            color_to_words = {
                '#ecca40': ['engineer', 'infrastructure', 'deployment', 'production', 'workflow',
                            'reliability', 'responsiblity', 'building', 'product', 'tool', 'stack',
                            'systems', 'system', 'build', 'built'],
                '#8e2f73': ['data scientist', 'machine learning', 'data science', 'data',
                            'idea', 'model', 'errors', 'learn', 'ambiguity', 'guess', 'machine learning']
            }
            default_color = '#333333'
            grouped_color_func = GroupedColorFunc(color_to_words, default_color)
            wordcloud.recolor(color_func=grouped_color_func)
        
        ax.imshow(wordcloud, interpolation="bilinear")
        ax.spines[['top', 'right', 'left', 'bottom']].set_visible(False)
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(title, y = 1.04)
        self.wordcloud_fig = fig
        fig.tight_layout()
        fig.savefig(self.WORDCLOUD_FIG_FILENAME)
        return fig

    def get_sentences(self, document):
        "Return list of lists with inner list as each word in a sentence."
        import string
        return [
            list(map(
                lambda s: s.lower(),
                sentence.strip().translate(
                    str.maketrans('', '', string.punctuation)
                ).split()
            ))
            for sentence in document.split('.')
        ]

    def get_w2v_figure(self, document, fig = None, ax = None, title = ''):
        """
        Make a word2vec embedding and PCA visualization from a document represented as one string.
        Return the visualization as a matplotlib figure if the PCA dimensions = 2.
        """
        from gensim.models import Word2Vec
        from sklearn.decomposition import PCA

        # filter text for stopwords
        document = self.get_sentences(document)
        stopwords = self.aggregate_stopwords()
        stopwordless_document = [
            list(filter(lambda word: word.lower() not in stopwords, sentence))
            for sentence in document
        ]

        # fit word2vec transform
        self.w2v_model = Word2Vec(stopwordless_document, min_count=self.MIN_COUNT_W2V, seed=self.SEED)
        words = list(self.w2v_model.wv.index_to_key) # vocabulary
        # model.save('model.bin')
        # new_model = Word2Vec.load('model.bin')
        X = self.w2v_model.wv[self.w2v_model.wv.index_to_key] # embeddings are these X vectors

        # reduce word2vec embeddings to PCA_COMPONENTS dimensions
        pca = PCA(n_components=self.PCA_COMPONENTS, random_state=self.SEED) # dim reduction
        result = pca.fit_transform(X)

        if self.PCA_COMPONENTS == 2:
            from matplotlib import pyplot
            if fig is None or ax is None:
                fig, ax = pyplot.subplots(1,1)
            ax.scatter(result[:, 0], result[:, 1])
            for i, word in enumerate(list(self.w2v_model.wv.index_to_key)):
                ax.annotate(word, xy=(result[i, 0] + 5e-4, result[i, 1] + 5e-4), rotation=0)
            ax.spines[['top', 'right', 'left', 'bottom']].set_visible(False)
            ax.set_title(title, y = 1.04)
            self.w2v_fig = fig
            fig.tight_layout()
            fig.savefig(self.W2V_FIG_FILENAME)
            return fig
        else: 
            return result # make a higher dim visualization!
        
    def get_default_device(self):
        import torch
        if torch.cuda.is_available():
            return torch.device("cuda")

        # elif torch.backends.mps.is_built() :
        #     # https://pytorch.org/blog/introducing-accelerated-pytorch-training-on-mac/
        #     _p = platform()
        #     if _p.startswith('macOS') and float(_p.split('-')[1]) >= 12.3:
        #         return torch.device("mps")

        return torch.device("cpu")

    def transcribe_video(self, transcription_task, quiet=False):
        """
        Extract the audio from the YouTube watch `url` in the `transcription_task`. 
        The audio will be saved locally to `output_path/transcription_task.filename`. 
        Load OpenAI's `whisper` model on `device` and use its transcription model.
        """
        import whisper
        from pytube import YouTube
        if not quiet:
            print("Extracting audio from video at {}...".format(transcription_task.url))
        audio = YouTube(transcription_task.url).streams.get_audio_only()
        audio.download(output_path = self.AUDIO_OUTPUT, filename = transcription_task.filename)
        audio_filename = self.AUDIO_OUTPUT + transcription_task.filename
        device = self.get_default_device()
        if not quiet:
            print("Loading {} model on {}...".format(transcription_task.model_type, device))
        model = whisper.load_model(transcription_task.model_type, device = device)
        if not quiet:
            print("Model downloaded. Beginning Inference...")
            print("Transcribing {}...".format(audio_filename))
        result = model.transcribe(audio_filename)
        return result['text']





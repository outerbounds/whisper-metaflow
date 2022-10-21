# Run Whisper With Metaflow 👋

![](/fs-chat-cloud.png)

This repository offers you a way to transcribe YouTube videos from only their URLs. 
OpenAI's [Whisper model](https://github.com/openai/whisper) is used with Metaflow to transcribe the audio from many videos in parallel. To run the code in this repository in the cloud you will need access to a Metaflow deployment. You can also run locally if you prefer, but it may take a long time to use the larger versions of Whisper. If you want to learn more about Metaflow or need help getting set up, find us in the #ask-metaflow channel on [Slack](http://slack.outerbounds.co/)!

# README.md Contents
* (Cloud is optional) [Operate Metaflow in the Cloud](#operate-metaflow-in-the-cloud)
* [Install Dependencies](#install-dependencies)
* [Run the Code](#run-the-code)
    * [Transcribe One Video](#transcribe-one-video)
    * [Transcribe each Video in a Playlist](#transcribe-each-video-in-a-playlist)
    * [Transcribe a List of Videos](#transcribe-a-list-of-videos)
    * [Visualize Results in a Metaflow Card](#visualize-results-in-a-metaflow-card)
    * (Cloud is optional) [Cloud Compute and GPU Access](#cloud-compute-and-gpu-access)

# Operate Metaflow in the Cloud
Note: You can skip this section if you are not interested in running on the cloud.

Before running the flow ensure that Metaflow-related infrastructure is [deployed](https://outerbounds.com/docs/aws-deployment-guide/) and [configured](https://outerbounds.com/docs/configure-metaflow/) on your cloud account and GPU's are configured for the compute environment. See the documentation to learn about each supported platform:
* [AWS Batch](https://outerbounds.com/engineering/deployment/aws-managed/introduction/)
* [AWS EKS](https://outerbounds.com/engineering/deployment/aws-k8s/deployment/)
* [Azure AKS](https://outerbounds.com/engineering/deployment/azure-k8s/deployment/)

If you don't have infrastructure setup, you can set up AWS infrastructure with this [cloudformation template](https://github.com/outerbounds/metaflow-tools/blob/master/aws/cloudformation/metaflow-cfn-template.yml). To deploy the GPU infrastructure on AWS, change the [ComputeEnvInstanceTypes](https://github.com/outerbounds/metaflow-tools/blob/d0da1fa4f9aa6845f8091d06a1b7a99962986c98/aws/cloudformation/metaflow-cfn-template.yml#L42) in the Cloudformation template or the Cloudformation UI. More detailed instructions on setting up infrastructure can be found [here](https://outerbounds.com/docs/cloudformation/). 

# Install Dependencies

## Get the Code
```
git clone https://github.com/outerbounds/whisper-metaflow.git
cd whisper-metaflow
```

## Install Whisper Dependencies
If you do not already have it, you will need [ffmpeg](https://ffmpeg.org/) installed on your machine for Whisper to work. See these [instructions](https://github.com/openai/whisper#setup) to install on your machine.

## Use `env.yml` with `conda`

You can install dependencies of this code using `conda`. There are three options for installing conda if you do not already have it:
* [Anaconda distribution](https://www.anaconda.com/download/) of Python 3
* [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
* [Mamba](https://mamba.readthedocs.io/en/latest/)

This repository includes a conda environment in `env.yml` file for you to use. You can install and activate the environment by running the following commands from the root of this repository in your terminal:
```
conda env create -f env.yml
conda activate youtube-transcription
```

# Run the Code
Before running the flow ensure you have the necessary AWS infrastructure setup for Metaflow. If you want to run steps remotely you need to configure Metaflow storage in S3. 

## Transcribe one Video

To run the model locally with default parameters (such as using the `tiny` Whisper model), you can run the following:
```sh
python youtube_video_transcriber.py run
```

To specify a specific YouTube video, find the watch URL starting with `https://www.youtube.com/watch` and pass it to the flow's `--url` parameter.
```sh
python youtube_video_transcriber.py run --url 'https://www.youtube.com/watch?v=OH0Y_DUZu4Y'
```

## Transcribe each Video in a Playlist
You can also pass a playlist starting with `https://www.youtube.com/playlist` to the `--url` parameter. 
This command will run the `transcribe` step in parallel for each video in the playlist.
```sh
python youtube_video_transcriber.py run --url 'https://www.youtube.com/playlist?list=PLUsOvkBBnJBc1fcDQEOPJ77pMcE4CnNxc'
```

## Transcribe a List of Videos
You can also pass a list of watch URLs in a file. For example, you can paste URLs in a `.txt.` file like `science_video_urls.txt` and then run the `transcribe` step in parallel for each video in the list.
```sh
python youtube_video_transcriber.py run --urls 'science_video_urls.txt'
```

## Visualize Results in a Metaflow Card
You can visualize the results of your flow by accessing the Metaflow card attached to the `postprocess` step:
```
python youtube_video_transcriber.py card view postprocess
```

## Access Results in a Notebook
You can access results from a Jupyter notebook, the Python interpreter, or any script using the [Metaflow Client API])(https://docs.metaflow.org/api/client).
```python
from metaflow import Flow
run = Flow('YouTubeVideoTranscription').latest_run
# access results in run.data
```

## Cloud Compute and GPU Access

### Accessing Remote Compute

To run this code remotely you will need access to a [Metaflow deployment](#operate-metaflow-on-aws-infrastructure). 

If you look at the [flow script](./youtube_video_transcriber.py) you will see a `@batch` decorator commented out above the `transcribe` step. 
```
@batch(
    cpu = 8, 
    gpu = 1,
    memory = 16000,
    image = 'eddieob/whisper-gpu:latest', # An image in Docker Hub to start the container that runs the step remotely.
    queue = os.getenv('METAFLOW_BATCH_JOB_QUEUE') # An AWS Batch queue with access to compute environments running GPU instances.
)

```
You can uncomment this decorator in `youtube_video_transcriber.py` and then run:

```sh
python youtube_video_transcriber.py run --model large
```

The Docker image we leave as the default is available in [Docker Hub](https://hub.docker.com/repository/docker/eddieob/whisper-gpu).

The batch queue will be unique based on how your Metaflow deployment is configured. You can set batch queue in your Metaflow config, the `METAFLOW_BATCH_JOB_QUEUE` environment variable, or the `queue` argument from the `@batch()` decorator in `youtube_video_transcriber.py`. You could also change the `@batch` decorator to [`@kubernetes`](https://docs.metaflow.org/api/step-decorators/kubernetes), if you opt to use [Metaflow with Kubernetes](https://github.com/valayDave/metaflow-on-kubernetes-docs).



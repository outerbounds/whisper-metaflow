# Run Whisper With Metaflow 👋

This repository offers you a way to transcribe YouTube videos from only their URLs. 
OpenAI's [Whisper model](https://github.com/openai/whisper) is used with Metaflow to transcribe the audio from many videos in parallel. To run the code in this repository in the cloud you will need access to a Metaflow deployment. You can also run locally if you prefer, but it may take a long time to use the larger versions of Whisper. If you want to learn more about Metaflow or need help getting set up, find us in the #ask-metaflow channel on [Slack](http://slack.outerbounds.co/)!

# Operate Metaflow in the Cloud
Note: You can skip this section if you are not interested in running on the cloud.

Before running the flow ensure that Metaflow-related infrastructure is [deployed](https://outerbounds.com/docs/aws-deployment-guide/) and [configured](https://outerbounds.com/docs/configure-metaflow/) on your cloud account and GPU's are configured for the compute environment. See the documentation to learn about each supported platform:
* [AWS Batch](https://outerbounds.com/engineering/deployment/aws-managed/introduction/)
* [AWS EKS](https://outerbounds.com/engineering/deployment/aws-k8s/deployment/)
* [Azure AKS](https://outerbounds.com/engineering/deployment/azure-k8s/deployment/)

If you don't have infrastructure setup, you can set up AWS infrastructure with this [cloudformation template](https://github.com/outerbounds/metaflow-tools/blob/master/aws/cloudformation/metaflow-cfn-template.yml). To deploy the GPU infrastructure on AWS, change the [ComputeEnvInstanceTypes](https://github.com/outerbounds/metaflow-tools/blob/d0da1fa4f9aa6845f8091d06a1b7a99962986c98/aws/cloudformation/metaflow-cfn-template.yml#L42) in the Cloudformation template or the Cloudformation UI. More detailed instructions on setting up infrastructure can be found [here](https://outerbounds.com/docs/cloudformation/). 

# Install Dependencies

## Use `env.yml` with `conda`

We have included a conda environment in the form of a `env.yml` file for you to use. You can install and activate the environemnent by running the following commands from your terminal:
```
conda env create -f env.yml
conda activate youtube-transcription
```

# Run the Code
Before running the flow ensure you have the necessary AWS infrastructure setup for Metaflow. If you wany to run steps remotely you need to configure Metaflow storage in S3. 

## Transcribe one Video

To run the model locally with default parameters (such as using the `tiny` Whisper model), you can run the following:
```sh
python youtube_video_transcriber.py run
```

To specify a specific YouTube video, find the watch url starting with `https://www.youtube.com/watch` and pass it to the flow's `--url` parameter.
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
You can also pass a list of watch urls in a file. For example you can paste URLs in a `.txt.` file like `science_video_urls.txt` and then run the `transcribe` step in parallel for each video in the list.
```sh
python youtube_video_transcriber.py run --urls 'science_video_urls.txt'
```

## Cloud Compute and GPU Access

### Accessing Remote Compute

To run this code remotetly you will need access to a [Metaflow deployment](#operate-metaflow-on-aws-infrastructure). Inside of a `.env` file you can configure the following items. 

```.env
DEFAULT_MODEL_TYPE="small"
BATCH_QUEUE_CPU="<YOUR AWS BATCH QUEUE>"
CPU_IMAGE="eddieob/whisper:latest"
BATCH_QUEUE_GPU="<YOUR GPU-ENABLED AWS BATCH QUEUE>"
GPU_IMAGE="eddieob/whisper-gpu:latest"
```

The images are available via [Docker Hub](https://hub.docker.com/repository/docker/eddieob/whisper-gpu), and the batch queue's will be unique to your cloud deployment.
If you want to use a default queue, you can remove the `queue` argument from the `@batch()` decorator in `youtube_video_transcriber.py`. 

### Telling Metaflow to Run Steps Remotely

If you look at the code you will see a `@batch` decorator commented out above the `transcribe` step. 
Note that you will need to pick compute instances with enough memory to hold the version of Whisper you selected.
We were able to run the large model with the following settings:
```
@batch(
    cpu = 8, 
    gpu = 1,
    memory = 16000,
    image = 'eddieob/whisper-gpu:latest', # An image in Docker Hub to start the container that runs the step remotely.
    queue = os.getenv('BATCH_QUEUE_GPU')  # An AWS Batch queue with access to compute environments running P3 instances.
)
```
You can uncomment this decorator in `youtube_video_transcriber.py` and then run:

```sh
python youtube_video_transcriber.py run --model large
```

You could also changed the `@batch` decorator to `@kubernetes`, if you opted for [Metaflow with Kubernetes](https://github.com/valayDave/metaflow-on-kubernetes-docs).



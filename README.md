# Run Whisper With Metaflow 👋

This repository offers you a way to transcribe YouTube videos from only their URLs. 
OpenAI's [Whisper model](https://github.com/openai/whisper) is integrated into a Metaflow workflow that will help you scale horizontally or vertically to quickly produce as many images as you need. To run the code in this repository in the cloud you will need access to a Metaflow deployment configured with S3 storage. You can also run locally if you prefer, but it may take a long time to use the larger versions of Whisper. If you want to learn more about Metaflow or need help getting set up, find us on [Slack](http://slack.outerbounds.co/)!

# Operate Metaflow on AWS Infrastructure
Note: You can skip this section if you are not interested in running on the cloud.

Before running the flow ensure that Metaflow-related infrastructure is [deployed](https://outerbounds.com/docs/aws-deployment-guide/) and [configured](https://outerbounds.com/docs/configure-metaflow/) on your AWS account and GPU's are configured for the compute environment (AWS Batch / EKS). 

If you don't have infrastructure setup, you can set it up with this [cloudformation template](https://github.com/outerbounds/metaflow-tools/blob/master/aws/cloudformation/metaflow-cfn-template.yml). To deploy the GPU infrastructure on AWS, change the [ComputeEnvInstanceTypes](https://github.com/outerbounds/metaflow-tools/blob/d0da1fa4f9aa6845f8091d06a1b7a99962986c98/aws/cloudformation/metaflow-cfn-template.yml#L42) in the Cloudformation template or the Cloudformation UI. More detailed instructions on setting up infrastructure can be found [here](https://outerbounds.com/docs/cloudformation/)


# Install Dependencies

## Use `env.yml` with `conda`

We have included a conda environment in the form of a `env.yml` file for you to use. You can install and activate the environemnent by running the following commands from your terminal:
```
conda env create -f env.yml
conda activate youtube-transcription
```

# Run the Code
Before running the flow ensure you have the necessary AWS infrastructure setup for Metaflow. If you wany to run steps remotely you need to configure Metaflow storage in S3. 

## Accessing Remote Compute

To run this code remotetly you will need access to a [Metaflow deployment](#operate-metaflow-on-aws-infrastructure). Inside of a `.env` file you can configure the following items based on your AWS 

```.env
DEFAULT_MODEL_TYPE="small"
BATCH_QUEUE_CPU="<YOUR AWS BATCH QUEUE>"
CPU_IMAGE="eddieob/whisper:latest"
BATCH_QUEUE_GPU="<YOUR GPU-ENABLED AWS BATCH QUEUE>"
GPU_IMAGE="eddieob/whisper-gpu:latest"
```

### Local
```sh
python youtube_video_transcriber.py run
```

### Remote
If you look at the code you will see a `@batch` decorator commented out above the `transcribe` step. 
You can uncomment this and then run:

```sh
python youtube_video_transcriber.py run
```

You could also changed the `@batch` decorator to `@kubernetes`, if you opted for [Metaflow with Kubernetes](https://github.com/valayDave/metaflow-on-kubernetes-docs).

### Accessing GPUs
To run on GPU, simply change the `gpu` argument in your batch decorator like `@batch(gpu=1, ...)`. 
Note that you will need your AWS Batch configuration set up with a compute environment that has access to GPU instances.

## Transcribe one Video
```sh
python youtube_video_transcriber.py run
```

```sh
python youtube_video_transcriber.py run --url 'https://www.youtube.com/watch?v=OH0Y_DUZu4Y'
```

## Transcribe each Video in a Playlist
```sh
python youtube_video_transcriber.py run --url 'https://www.youtube.com/playlist?list=PLUsOvkBBnJBc1fcDQEOPJ77pMcE4CnNxc'
```

## Transcribe a List of Videos
```sh
python youtube_video_transcriber.py run --urls 'science_video_urls.txt'
```
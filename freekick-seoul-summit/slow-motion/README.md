# Slow Motion Video Generator

Generates slow-motion replay videos from free kick recordings using the FILM (Frame Interpolation for Large Motion) model deployed on Amazon SageMaker Async Inference.

## How It Works

1. A free kick video is uploaded to S3, triggering an SNS notification
2. A Lambda function extracts frames from the video and uploads them to S3
3. SageMaker Async Inference runs the FILM model to interpolate additional frames between originals
4. The Lambda function downloads the interpolated frames and assembles them into a slow-motion video
5. The resulting video is stored in S3 and the player record is updated in DynamoDB

## Project Structure

```
slow-motion/
├── source/
│   ├── slow-mo.ipynb              # Notebook for deploying the SageMaker endpoint
│   ├── helper.py                  # Helper utilities for the notebook
│   └── slow_mo_generator/         # Model serving code for DJL container
│       ├── interpolator.py        # FILM frame interpolation logic
│       ├── model.py               # DJL model handler
│       ├── utils.py               # Utility functions
│       ├── serving.properties     # DJL serving configuration
│       └── requirements.txt       # Python dependencies
├── lambda/
│   ├── lambda_function.py         # Lambda handler for video processing pipeline
│   └── utils.py                   # Lambda utility functions
└── deployment/
    └── cfn_template.yaml          # CloudFormation template for SageMaker Studio
```

## Deployment

### Step 1: Deploy SageMaker Studio (Optional)

Deploy the CloudFormation template in `deployment/cfn_template.yaml` to set up a SageMaker Studio environment.

### Step 2: Deploy the SageMaker Endpoint

Open `source/slow-mo.ipynb` in SageMaker Studio (recommended instance: `ml.g4dn.xlarge`) and follow the notebook steps to:

1. Download pretrained FILM model weights
2. Package the model for DJL Serving
3. Deploy a SageMaker Async Inference endpoint (`ml.g5.4xlarge`)
4. (Optional) Configure autoscaling policies

### Step 3: Deploy the Lambda Function

Deploy the Lambda function from the `lambda/` directory. Ensure the function has:

- Access to the S3 buckets for input/output videos
- Permission to invoke the SageMaker endpoint
- SNS trigger configured for new video uploads
- `ffmpeg` layer attached (see below)

### FFmpeg Lambda Layer

The Lambda function requires an FFmpeg binary packaged as a layer:

1. Download the static build from [johnvansickle.com/ffmpeg](https://johnvansickle.com/ffmpeg/)
2. Create a zip with the structure: `ffmpeg/bin/ffmpeg`
3. Upload as a Lambda layer

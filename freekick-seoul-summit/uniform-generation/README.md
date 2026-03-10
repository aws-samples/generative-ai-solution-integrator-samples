# Uniform Generation

Generates personalized soccer uniforms on player photos using clothes segmentation (SegFormer on SageMaker) and image inpainting (Amazon Titan Image Generator on Bedrock).

## How It Works

1. A player photo is uploaded to S3, triggering the Lambda function
2. The image is sent to a SageMaker real-time endpoint running a SegFormer model for pixel-level clothes segmentation
3. Upper-clothes and pants masks are extracted and combined into an inpainting mask
4. The original image and mask are sent to Amazon Titan Image Generator (`amazon.titan-image-generator-v1`) with a prompt describing a soccer uniform in a randomly selected color
5. The generated image is saved back to S3

## Project Structure

```
uniform-generation/
├── clothes_segmentation_endpoint.ipynb  # Notebook for deploying SegFormer on SageMaker
└── lambda_function.py                   # Lambda handler for the generation pipeline
```

## Prerequisites

- **SageMaker Endpoint**: Deploy the SegFormer model using `clothes_segmentation_endpoint.ipynb`
- **Amazon Bedrock**: Enable access to Amazon Titan Image Generator in `us-west-2`
- **OpenCV Lambda Layer**: Required for image processing in Lambda
  - Build guide: [awslabs/lambda-opencv](https://github.com/awslabs/lambda-opencv)
  - Pre-built layers: [076923/aws-lambda-python-opencv-layer](https://github.com/076923/aws-lambda-python-opencv-layer)

## Configuration

Update the following placeholders in `lambda_function.py` before deployment:

- `YOUR_ENDPOINT_NAME` - Name of the deployed SageMaker SegFormer endpoint
- `YOUR_TABLE_NAME` - DynamoDB table name for player information

## Region Configuration

- SageMaker endpoint and DynamoDB: `ap-northeast-2` (Seoul)
- Amazon Bedrock (Titan Image Generator): `us-west-2` (Oregon)

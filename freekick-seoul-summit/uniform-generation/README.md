## Prerequisites (OpenCV layer)

1. You can refer to the OpenCV layer creation guide in the link below.
https://github.com/awslabs/lambda-opencv

2. If you find a pre-built OpenCV layer for a specific python version, you can refer to the link below.
https://github.com/076923/aws-lambda-python-opencv-layer

## Source Code Description

### clothes_segmentation_endpoint.ipynb

The above file is an example of distributing a segformer model for classification using sagemaker. The sagemaker endpoint performs real-time inference. The segformer model generates a mask image that fits the previously specified label through pixel-level segmentation from the input image.

### lambda_function.py

The above file is a combination of the input image obtained through the camera and the mask image inferred through the Seformer model, and performs image inpainting through the Amazon Titan image generator.
By entering the two images and a prompt to create a soccer uniform, the area designated as a mask is converted into a soccer uniform that matches the set prompt, and the image is stored in amazon S3.

To use Lambda code, you must add the sagemaker endpoint name specified as 'YOUR_ENDPOINT_NAME' and 'YOUR_TABLE_NAME' must specify the name of the table where your information is stored.

The Lambda function in the source code uses settings related to ap-northeast-2 region, and uses us-west-2 region with additional configuration variables set for bedrock use.


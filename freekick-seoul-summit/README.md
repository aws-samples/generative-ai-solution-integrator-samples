# Free Kick Challenge - AWS Seoul Summit 2024

An interactive soccer free kick challenge demo presented at AWS Seoul Summit 2024. This project combines multiple AI/ML services to create an engaging experience where participants take free kick shots and receive AI-generated content in real time.

## Architecture Overview

The solution consists of three AI-powered components that work together:

1. **Slow Motion Replay** - Generates cinematic slow-motion replays of each free kick using frame interpolation
2. **Uniform Generation** - Creates personalized soccer uniforms on player photos using image segmentation and inpainting
3. **Live Commentary** - Produces real-time multilingual commentary for each shot using large language models

## Components

| Component | AWS Services | Description |
|-----------|-------------|-------------|
| [Slow Motion](slow-motion/) | SageMaker (Async Inference), Lambda, S3, DynamoDB, SNS | FILM model-based frame interpolation for slow-motion video generation |
| [Uniform Generation](uniform-generation/) | SageMaker (Real-time Inference), Bedrock (Titan Image Generator), Lambda, S3, DynamoDB | SegFormer-based clothes segmentation + Titan Image Generator inpainting |
| [Live Commentary](live-commentary/) | Bedrock (Claude) | LLM-powered soccer commentary generation in multiple languages |

## Prerequisites

- AWS Account with access to Amazon SageMaker, Amazon Bedrock, and related services
- Python 3.x
- AWS CLI configured with appropriate permissions
- SageMaker Studio or Jupyter environment (for notebook-based components)

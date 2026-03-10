# Live Commentary

Generates real-time soccer commentary for free kick shots using Amazon Bedrock (Claude models). Supports multiple languages and writing styles.

## How It Works

1. Shot data (player name, shot speed, distance, goal result, leaderboard ranking) is passed as input
2. A prompt is constructed based on the selected language and writing style
3. Amazon Bedrock (Claude) generates engaging, contextual commentary in a single sentence

## Supported Languages

English, German, French, Spanish, Arabic, Traditional Chinese, Turkish, Dutch

## Writing Styles

- **Commentator** - Professional soccer commentator style
- **Twitter** - Social media tweet format with emojis

## Project Structure

```
live-commentary/
└── CommentaryFreeKick.ipynb  # Notebook demonstrating commentary generation
```

## Usage

Open `CommentaryFreeKick.ipynb` in a Jupyter environment and run through the cells. The notebook demonstrates:

- Prompt construction for different languages and styles
- Commentary generation using Claude Instant, Claude v1, and Claude v2

## Prerequisites

- AWS account with Amazon Bedrock access
- Claude models enabled in Bedrock (Claude Instant, Claude v1, Claude v2)
- `boto3` with Bedrock runtime support

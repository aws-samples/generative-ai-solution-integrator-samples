import json
import io
import base64
import json
import logging
import boto3
import urllib
import numpy as np
import cv2
import random
from botocore.config import Config
from botocore.exceptions import ClientError
from PIL import Image
from boto3.dynamodb.conditions import Key, Attr

my_config_west = Config(
    region_name = 'us-west-2',
    retries = {
        'max_attempts': 10,
        'mode': 'standard'
        }
    )
my_config_northeast = Config(
    region_name = 'ap-northeast-2',
    retries = {
        'max_attempts': 10,
        'mode': 'standard'
        }
    )

def base64_to_cv2(image_base64):
    # base64 image to cv2
    image_bytes = base64.b64decode(image_base64)
    np_array = np.fromstring(image_bytes, np.uint8)
    image_cv2 = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    return image_cv2

def cv2_to_base64(image_cv2):
    # cv2 image to base64
    image_bytes = cv2.imencode('.jpg', image_cv2)[1].tostring()
    #image_base64 = base64.b64encode(image_bytes).decode()
    return image_bytes

def image_to_base64(img) -> str:
    """Converts a PIL Image or local image file path to a base64 string"""
    if isinstance(img, str):
        if os.path.isfile(img):
            print(f"Reading image from file: {img}")
            with open(img, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        else:
            raise FileNotFoundError(f"File {img} does not exist")
    elif isinstance(img, Image.Image):
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    else:
        raise ValueError(f"Expected str (filename) or PIL Image. Got {type(img)}")

def save_mask_image(segment_results):
    for segment_result in segment_results:
        if segment_result['label'] == 'Upper-clothes':
            pred_decoded_byte = base64.decodebytes(bytes(segment_result['mask'], encoding="utf-8"))
            nparr = np.fromstring(pred_decoded_byte, np.uint8)
            upper_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR) # cv2.IMREAD_COLOR in OpenCV 3.1
            #cv2.imwrite('test-result.png', img_np)
        elif segment_result['label'] == 'Pants':
            pred_decoded_byte = base64.decodebytes(bytes(segment_result['mask'], encoding="utf-8"))
            nparr = np.fromstring(pred_decoded_byte, np.uint8)
            lower_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR) # cv2.IMREAD_COLOR in OpenCV 3.1
    
    result = ()
    #if upper_img is not None and lower_img is not None:
    #    upper_img = 255-upper_img
    #    lower_img = 255-lower_img
    result = (upper_img, lower_img)
    return result

def segment_clothes(image):
    sagemaker_runtime = boto3.client('sagemaker-runtime', config=my_config_northeast)
    
    response = sagemaker_runtime.invoke_endpoint(
        EndpointName='YOUR_ENDPOINT_NAME',
        ContentType='image/x-image',
        Body=image
    )
    
    return response['Body'].read().decode('utf-8')
    
def generate_image(model_id, body):
    
    bedrock = boto3.client(service_name='bedrock-runtime', config=my_config_west)

    accept = "application/json"
    content_type = "application/json"

    response = bedrock.invoke_model(
        body=body, modelId=model_id, accept=accept, contentType=content_type
    )
    
    response_body = json.loads(response.get("body").read())

    base64_image = response_body.get("images")[0]
    base64_bytes = base64_image.encode('ascii')
    image_bytes = base64.b64decode(base64_bytes)

    finish_reason = response_body.get("error")

    if finish_reason is not None:
        raise ImageError(f"Image generation error. Error is {finish_reason}")

    return image_bytes

def lambda_handler(event, context):
    # TODO implement
    s3 = boto3.client('s3', config=my_config_northeast)
    dynamodb = boto3.resource('dynamodb', config=my_config_northeast)
    
    table_name = 'YOUR_TABLE_NAME'
    table = dynamodb.Table(table_name)
    
    response_table = table.query(
        KeyConditionExpression=Key('pk').eq('ACTIVE_PLAYER') & Key('sk').eq('ACTIVE_PLAYER'),
    )
    
    
    print(event)
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        print("CONTENT TYPE: " + response['ContentType'])
        print(response)
        
        image = response['Body'].read()
        
        result = segment_clothes(image)
        result = json.loads(result)

        mask_images = save_mask_image(result)
        
        mask_image = 255 - ( mask_images[0] + mask_images[1] )

        color_converted = cv2.cvtColor(mask_image, cv2.COLOR_BGR2RGB)
        pil_image=Image.fromarray(color_converted)

        mask_bytes = image_to_base64(pil_image)#response_mask['Body'].read()
        color = ['black', 'white', 'red', 'blue', 'green', 'yellow', 'orange', 'purple', 'pink', 'brown', 'gray']
        random.shuffle(color)

        model_id = 'amazon.titan-image-generator-v1'
        
        print(mask_bytes)
        
        gender = None
        if len(response_table['Items']) != 0:
            print('dynamodb response : ', response_table['Items'][0]['gender'])
            gender = response_table['Items'][0]['gender']
        
        if gender is not None and gender != 'none':
            #prompt = f"{color[0]} color soccer uniform shorts"
            prompt = f"{gender}'s soccer uniform shorts of {color[0]} color"
        else:
            prompt = f"{color[0]} color soccer uniform shorts"
        body = json.dumps({
            "taskType": "INPAINTING",
            "inPaintingParams": {
                "text": prompt,
                "negativeText": "bad quality, low res",
                "image": base64.b64encode(image).decode('utf8'),
                "maskImage": mask_bytes
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "height": 512,
                "width": 512,
                "cfgScale": 8.0
            }
        })

        image_bytes = generate_image(model_id=model_id, body=body)
        
        save_key = key.split(".")[0] + ".jpeg"
        save_key = "uniform-generated-photos/"+save_key.split("/")[-1]
        
        s3.put_object(Bucket=bucket, Body=image_bytes, Key=save_key, ContentType= 'image/jpeg')
        
        return {
            'headers': { "Content-Type": "image/png" },
            'statusCode': 200,
            'body': base64.b64encode(image),
            'isBase64Encoded': True
        }
    
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

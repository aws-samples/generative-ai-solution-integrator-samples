import json
import boto3
import os
import tempfile
import time
import urllib.parse
import shutil
from utils import extract_frames, make_tar, check_s3_file_exists, delete_temp_files, load_json_file, sync_s3_buckets, create_video
from boto3.dynamodb.conditions import Key, Attr

sm_runtime = boto3.client('sagemaker-runtime')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

#slow_mo_inference_endpoint_name = 'slow-mo-2024-05-02-01-58-10-203'
slow_mo_inference_endpoint_name = 'slow-mo-2024-05-13-04-55-29-493'
origin_bucket_name = 'seoul-2024-free-kick-challenge-downloadable-contents'
slow_mo_bucket_name = 'slow-motion-free-kick-summit-2024'
output_bucket_name = 'seoul-2024-free-kick-challenge-downloadable-contents'
output_file = "/tmp/output.json"
output_frames = "/tmp/slow_mo_frames"

def lambda_handler(event, context):
    print("Received event:", event)
    message = json.loads(event['Records'][0]['Sns']['Message'])
    origin_input_bucket_name = message['Records'][0]['s3']['bucket']['name']
    tmp_origin_input_source_key = urllib.parse.unquote_plus(message['Records'][0]['s3']['object']['key'], encoding='utf-8')
    origin_input_source_index = tmp_origin_input_source_key.rfind('/')
    origin_input_source_key = tmp_origin_input_source_key[origin_input_source_index+1:-4]
    upload_tar_key_name = f"slow-mo/input/{origin_input_source_key}.tar.gz"
    input_s3_loc = f"s3://{slow_mo_bucket_name}/{upload_tar_key_name}"
    ouput_video = f"/tmp/{origin_input_source_key}.mp4"
    slow_mo_result_key = f"slowmotion-videos/{origin_input_source_key}.mp4"

    table_name = 'free-kick-challenge-summitseoul24'
    table = dynamodb.Table(table_name)
    
    response_table = table.query(
        KeyConditionExpression=Key('pk').eq('ACTIVE_PLAYER') & Key('sk').eq('ACTIVE_PLAYER'),
    )
    print('dynamodb response : ', response_table['Items'][0]['id'])
    
    print("bucket name:", origin_input_bucket_name)
    print("source key:", origin_input_source_key)
    print("upload tar key name:", upload_tar_key_name)
    print("input_s3_loc", input_s3_loc)
    
    response = s3_client.get_object(Bucket=origin_bucket_name, Key=tmp_origin_input_source_key)
    file_content = response['Body'].read()
    
    print("response")
    print(response)
    
    # 로컬 파일 전부 제거
    delete_temp_files()
    
    # 로컬에 임시 파일 저장
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(file_content)
        video_path = tmp_file.name
    
    frame_dir = extract_frames(video_path)
   
    config = {
      "align": 64,
      "block_height": 1, 
      "block_width": 1,
      "time_to_interpolate": 2  
    }

    with open(f"{frame_dir}/config.json", "w") as f:
      json.dump(config, f, indent=4)
      
    files = os.listdir(frame_dir)
    print(files)
    
    frames_tarfile = make_tar(frame_dir)
    s3_client.upload_file(frames_tarfile, slow_mo_bucket_name, upload_tar_key_name)
    
    response = sm_runtime.invoke_endpoint_async(
        EndpointName=slow_mo_inference_endpoint_name,
        InputLocation=input_s3_loc,
        InvocationTimeoutSeconds=3600)
        
    print('result')
    print(response)
    
    s3_tmp_path = response['OutputLocation']
    status = "Processing"
    max_wait_time = 60 * 25 # 25 minutes
    current_wait_time = 0
    
    while status == "Processing":
        time.sleep(10)
        print("Status: " + status)
        if check_s3_file_exists(s3_tmp_path):
            status = "Complete"
        current_wait_time += 10
        if current_wait_time > max_wait_time:
            status = "Failed - Model did not complete in the expected time. Check the endpoint CloudWatch logs for more information."
            raise Exception("Final Status: " + status)

    print("Final Status: " + status)

    # Remove all files and folders
    if os.path.exists(output_frames):
        shutil.rmtree(output_frames)

    # Recreate empty directory 
    os.makedirs(output_frames)
    
    s3_client.download_file(slow_mo_bucket_name, s3_tmp_path.split(f"s3://{slow_mo_bucket_name}/", 1)[-1], output_file)

    output_results = load_json_file(output_file)
    print("output_results : ")
    print(output_results)
    
    sync_s3_buckets(slow_mo_bucket_name, output_frames, output_results['output_location'].split(f"s3://{slow_mo_bucket_name}/", 1)[-1])
    
    print(f"Slow-Mo frames downloaded here: {output_frames}")

    create_video(output_frames, #slow-mo frames
                    ouput_video,   #generated video
                    fr=25)         #frame rate of the video
                    
    s3_client.upload_file(ouput_video, output_bucket_name, slow_mo_result_key)
    
    if len(response_table['Items']) != 0:
        print(response_table['Items'][0]['id'])
        
        try:
            table.update_item(
                Key = {
                    'pk':'LATEST_VIDEO',
                    'sk':'LATEST_VIDEO'
                },
                AttributeUpdates={'playerId': {'Value': response_table['Items'][0]['id'], 'Action': 'PUT'}}
            )
        except ClientError as e:
            print(e)
            return {
                'statusCode': 500,
                'body': json.dumps('Error writing to DynamoDB')
            }
        
    
    return {
        'statusCode': 200,
        'body': json.dumps('Finished creating slow motion video')
    }

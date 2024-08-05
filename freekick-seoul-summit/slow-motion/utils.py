from pathlib import Path
import random
import subprocess
import tarfile
import os
import boto3
import tempfile
from io import BytesIO
import json

s3 = boto3.client('s3')
#
# load json file
#
def load_json_file(file_name):
    with open(file_name) as f:
        return json.load(f)

#
# sync with S3 buckets
#
def sync_s3_buckets(source_bucket, destination_bucket, Prefix):
    # S3 버킷 간에 동기화 수행
    
    print("source_bucket: ", source_bucket)
    print("destination_bucket: ", destination_bucket)
    print("Prefix: ", Prefix)
    
    response = s3.list_objects_v2(Bucket=source_bucket, Prefix=Prefix)

    for obj in response.get('Contents', []):
        key = obj['Key']
        local_file = os.path.join(destination_bucket, os.path.basename(key))
        s3.download_file(source_bucket, key, local_file)
        print(f"다운로드 완료: s3://{source_bucket}/{key} -> {local_file}")

#
# delete temp files
#
def delete_temp_files():
    tmp_dir = tempfile.gettempdir()  # 임시 디렉토리 경로 가져오기
    for filename in os.listdir(tmp_dir):  # 임시 디렉토리의 파일 목록을 가져옴
        file_path = os.path.join(tmp_dir, filename)  # 파일의 전체 경로 생성
        try:
            if os.path.isfile(file_path):  # 파일인지 확인
                os.remove(file_path)  # 파일 삭제
                print(f"{filename} deleted successfully.")
        except Exception as e:
            print(f"Error deleting {filename}: {e}")

#
# check if S3 file exists
#
def check_s3_file_exists(s3_path):
    # Split the S3 path into its components
    s3_components = s3_path.replace("s3://", "").split("/")
    bucket_name = s3_components[0]
    file_key = "/".join(s3_components[1:])
    
    # Check if the object exists
    try:
        s3.head_object(Bucket=bucket_name, Key=file_key)
        return True
    except:
        return False

#
# make tar.gz file
#
def make_tar(folder_path):
    output_path = "/tmp/input_frames.tar.gz"
    
    # tar the files
    with tarfile.open(output_path, "w:gz") as tar:
        for filename in os.listdir(folder_path):
            file = os.path.join(folder_path, filename)
            tar.add(file, arcname=os.path.basename(file))

    return output_path

#
# use ffmpeg to extract frames from video
#
def extract_frames(video_path):
    
    output_dir = Path(f"/tmp/{random.randint(0, 1000000)}")
    while output_dir.exists():
        output_dir = Path(f"/tmp/{random.randint(0, 1000000)}")
        
    output_dir.mkdir(parents=True, exist_ok=False)
    
    output_pattern = output_dir / "frame-%07d.jpg"
    print(output_pattern)
    
    ffmpeg_cmd = ["ffmpeg", "-i", video_path, 
                  "-qmin", "1", "-q:v", "1", str(output_pattern)]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True)
    except subprocess.CalledProcessError as err:
        print(f"Error running ffmpeg: {err}")
        
    return output_dir

#
# use ffmpeg to create video from frames
#
def create_video(input_frame_dir, output_file, fr=60):
    
    ffmpeg_cmd = [
    "ffmpeg", 
    "-y", 
    "-framerate", str(fr),
    "-pattern_type", "glob",
    "-i", f"{input_frame_dir}/frame*.jpg", 
    "-c:v", "libx264",
    "-pix_fmt", "yuvj420p",
    output_file
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True)
    except subprocess.CalledProcessError as err:
        print(f"Error running ffmpeg: {err}")
import boto3
import json
import os
import json
import base64
import io
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import boto3
import base64
import json
from werkzeug.security import check_password_hash, generate_password_hash
from database.database_models import add_generated_content, add_new_user
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from botocore.config import Config
from PIL import Image

boto_config = Config(
    region_name=os.environ.get('AWS_REGION', 'us-east-1'),
    retries = {'max_attempts': 3}
)

sagemaker_runtime = boto3.client(
    "sagemaker-runtime",
    config=boto_config
)

endpoint_name = "blogify-endpoint-v1"

image_path = "C:\\Users\\lilil\\OneDrive\\Documents\\school\\MSML650 Cloud Computing\\BlogifyAI\\E910F7EC-B117-4329-8648-EC73BE441D63.jpg"
sample_image = Image.open(image_path)

# sample_image =  sample_image.resize((512, 512)) 

buffer = io.BytesIO()
sample_image.save(buffer, format="PNG")
input_image_base64 = base64.b64encode(buffer.getvalue()).decode()

payload = {
    "mode": "img2img",
    "input_image": input_image_base64,
    "prompt": "A lady, red eyes",
    "negative_prompt": "blurry, low quality",
    "num_inference_steps": 50,
    "guidance_scale": 7.5,
    "strength": 0.9,
    "height": 512,
    "width": 512,
    "seed": 42,
    "lora": "lingsha"
}

response = sagemaker_runtime.invoke_endpoint(
    EndpointName=endpoint_name,
    Body=json.dumps(payload),
    ContentType="application/json"
)
response_body = json.loads(response["Body"].read())
generated_image_base64 = response_body['image']
image_data = base64.b64decode(generated_image_base64)


output_image_path = "generated_image.png"
with open(output_image_path, "wb") as file:
    file.write(image_data)


# from PIL import Image
# import io


# image = Image.open(io.BytesIO(image_data))
# image.show()  

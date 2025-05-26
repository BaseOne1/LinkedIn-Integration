import json
import boto3
import logging

s3 = boto3.client('s3')
BUCKET_NAME = 'falaiposting'
METADATA_KEY = 'images/approved/metadata.json'

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        params = event.get("queryStringParameters", {})
        file_name = params.get("file")
        image_url = params.get("url")
        action = params.get("action")

        if not file_name or not image_url or action != "approve":
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing or invalid parameters"})
            }

        logger.info(f"Received params: file={file_name}, url={image_url}, action={action}")

        seed = file_name.rsplit('.', 1)[0]
        metadata_obj = s3.get_object(Bucket=BUCKET_NAME, Key=METADATA_KEY)
        metadata = json.loads(metadata_obj["Body"].read().decode("utf-8"))

        if file_name not in metadata:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "File not found in metadata"})
            }

        result_json = {
            "seed": seed,
            "file_name": file_name,
            "image_url": image_url,
            "text": metadata[file_name]["text"]
        }

        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=f"approved/{seed}.json",
            Body=json.dumps(result_json),
            ContentType="application/json"
        )

        logger.info(f"Successfully uploaded approved/{seed}.json")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Approved JSON uploaded successfully."})
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

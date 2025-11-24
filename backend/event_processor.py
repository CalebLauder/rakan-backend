import boto3, json, os, uuid
from datetime import datetime

ddb = boto3.client("dynamodb")
iot = boto3.client("iot-data", region_name="us-east-1")
lam = boto3.client("lambda")

class EventProcessor:
    def handle_event(self, event):

        # 1. Log incoming event
        ddb.put_item(
            TableName=os.environ["EVENT_TABLE"],
            Item={
                "id": {"S": str(uuid.uuid4())},
                "timestamp": {"S": datetime.utcnow().isoformat()},
                "event": {"S": json.dumps(event)}
            }
        )

        # 2. Call LAM to get a decision
        lam_response = lam.invoke(
            FunctionName=os.environ["LAM_FUNCTION_NAME"],
            Payload=json.dumps(event)
        )

        decision = json.loads(lam_response["Payload"].read())

        device_id = decision["deviceId"]
        action = decision["action"]
        value = decision["value"]

        # 3. Publish resulting command
        iot.publish(
            topic=f"rakan/commands/{device_id}",
            qos=1,
            payload=json.dumps(decision)
        )

        # 4. Update device state table
        ddb.update_item(
            TableName=os.environ["STATE_TABLE"],
            Key={"deviceId": {"S": device_id}},
            UpdateExpression="SET #s = :new",
            ExpressionAttributeNames={"#s": "state"},
            ExpressionAttributeValues={":new": {"S": json.dumps(decision)}}
        )

        return decision

def lambda_handler(event, context):
    processor = EventProcessor()
    return processor.handle_event(event)

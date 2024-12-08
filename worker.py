import os
import json
import time
import logging
from datetime import datetime
from google.cloud import pubsub_v1
from google.cloud import storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pub/Sub Configuration
SUBSCRIPTION_NAME = os.getenv('PUBSUB_SUBSCRIPTION', 'signage-queue-sub')
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(os.getenv('GCP_PROJECT'), SUBSCRIPTION_NAME)

# GCS Configuration
GCS_BUCKET = os.getenv('GCS_BUCKET', 'digitalcast-bucket')
storage_client = storage.Client()
bucket = storage_client.bucket(GCS_BUCKET)

def callback(message):
    try:
        logger.info(f"Received message: {message.data}")
        data = json.loads(message.data)
        filename = data['filename']
        schedule_time = datetime.fromisoformat(data['schedule_time'])
        logger.info(f"Processing message for file {filename} scheduled at {schedule_time}.")

        # Wait until the scheduled time
        now = datetime.now()
        if now < schedule_time:
            wait_time = (schedule_time - now).total_seconds()
            logger.info(f"Waiting {wait_time} seconds until scheduled time...")
            time.sleep(wait_time)

        # Confirm media display
        logger.info(f"Media {filename} is ready for display at {datetime.now()}.")
        message.ack()

    except Exception as e:
        logger.error(f"Failed to process message: {e}", exc_info=True)
        message.nack()

subscriber.subscribe(subscription_path, callback=callback)
logger.info(f"Listening for messages on subscription {SUBSCRIPTION_NAME}...")

while True:
    time.sleep(60)
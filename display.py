import os
import psycopg2
import logging
from flask import Flask, render_template, jsonify, request
from google.cloud import storage
from datetime import datetime
import pytz

app = Flask(__name__)

# Logger Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
db_config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': 5432,
    'database': os.getenv('DB_NAME'),
}

# GCS Configuration
GCS_BUCKET = os.getenv('GCS_BUCKET', 'digitalcast-bucket')
storage_client = storage.Client()

# Timezone for Mountain Time (Colorado)
MOUNTAIN_TZ = pytz.timezone('America/Denver')

# Log Incoming Requests
@app.before_request
def log_request():
    logger.info(f"Incoming request: {request.method} {request.url} from {request.remote_addr}")

# Filter Non-HTTP Traffic
@app.before_request
def filter_invalid_requests():
    if not request.url.startswith("http"):
        logger.warning(f"Invalid request detected: {request.url} from {request.remote_addr}")
        return "Invalid request", 400

@app.route('/')
def display_media():
    try:
        # Current time in Mountain Time
        now_mt = datetime.now(MOUNTAIN_TZ)

        # Fetch scheduled media from SQL
        with psycopg2.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT filename, username, scheduled_start_time, scheduled_end_time
                    FROM signage
                    WHERE %s BETWEEN scheduled_start_time AND scheduled_end_time
                    ORDER BY scheduled_start_time ASC
                """
                cursor.execute(query, (now_mt,))
                rows = cursor.fetchall()

        media_data = []
        for row in rows:
            filename, username, start_time, end_time = row
            blob = storage_client.bucket(GCS_BUCKET).blob(filename)

            # Ensure the file exists in GCS
            if not blob.exists():
                logger.warning(f"File {filename} does not exist in GCS. Skipping...")
                continue

            media_data.append({
                "url": blob.public_url,
                "username": username,
                "start_time": start_time,
                "end_time": end_time,
            })

        if media_data:
            logger.info(f"Displaying media: {media_data}")
            return render_template('display.html', media_data=media_data)
        else:
            logger.info("No media currently scheduled for display.")
            return render_template('display.html', media_data=[])

    except Exception as e:
        logger.error(f"Failed to fetch/display media: {e}", exc_info=True)
        return f"<h1>Error: {e}</h1>", 500

@app.route('/api/media')
def api_media():
    try:
        now_mt = datetime.now(MOUNTAIN_TZ)

        with psycopg2.connect(**db_config) as conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT filename, username
                    FROM signage
                    WHERE %s BETWEEN scheduled_start_time AND scheduled_end_time
                    ORDER BY scheduled_start_time ASC
                """
                cursor.execute(query, (now_mt,))
                rows = cursor.fetchall()

        media_data = []
        for row in rows:
            filename, username = row
            blob = storage_client.bucket(GCS_BUCKET).blob(filename)

            # Ensure the file exists in GCS
            if not blob.exists():
                logger.warning(f"File {filename} does not exist in GCS. Skipping...")
                continue

            media_data.append({
                "url": blob.public_url,
                "username": username,
            })

        return jsonify({"media_data": media_data})

    except Exception as e:
        logger.error(f"Error in API media endpoint: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting display server on port 8081...")
    app.run(host='0.0.0.0', port=8081)

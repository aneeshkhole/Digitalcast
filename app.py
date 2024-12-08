import os
import psycopg2
import json
import logging
from flask import Flask, request, render_template
from google.cloud import storage
from google.cloud import pubsub_v1
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'jpeg', 'png', 'jpg', 'gif', 'mp4'}

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

# Pub/Sub Configuration
PUBSUB_TOPIC = os.getenv('PUBSUB_TOPIC', 'signage-queue')
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(os.getenv('GCP_PROJECT'), PUBSUB_TOPIC)


def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def upload_page():
    logger.info("Accessed upload page.")
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        logger.info("File upload request received.")
        username = request.form['username']
        file = request.files['file']
        scheduled_start_time = request.form['scheduled_start_time']
        scheduled_end_time = request.form['scheduled_end_time']

        if not file or not allowed_file(file.filename):
            logger.error("Invalid file type or no file uploaded.")
            return "Invalid file type! Allowed types: jpeg, png, jpg, gif, mp4", 400

        filename = secure_filename(file.filename)
        logger.info(f"Uploading file {filename} for user {username} to GCS bucket {GCS_BUCKET}...")

        # Upload file to GCS
        bucket = storage_client.bucket(GCS_BUCKET)
        blob = bucket.blob(filename)
        blob.upload_from_file(file)
        logger.info(f"File {filename} uploaded successfully to GCS.")

        # Save metadata to Cloud SQL
        logger.info("Saving metadata to Cloud SQL...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("""
            ALTER TABLE signage 
            ADD COLUMN IF NOT EXISTS username VARCHAR(255),
            ADD COLUMN IF NOT EXISTS scheduled_start_time TIMESTAMP,
            ADD COLUMN IF NOT EXISTS scheduled_end_time TIMESTAMP;
        """)
        query = """
            INSERT INTO signage (filename, username, scheduled_start_time, scheduled_end_time) 
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (filename, username, scheduled_start_time, scheduled_end_time))
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Metadata saved to Cloud SQL for user {username}.")

        # Publish message to Pub/Sub
        logger.info(f"Publishing message to Pub/Sub topic {PUBSUB_TOPIC}...")
        message = {
            "filename": filename,
            "username": username,
            "scheduled_start_time": scheduled_start_time,
            "scheduled_end_time": scheduled_end_time
        }
        publisher.publish(topic_path, json.dumps(message).encode("utf-8"))
        logger.info(f"Message published to Pub/Sub: {message}")

        # Display success message
        return (
            f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <meta http-equiv="refresh" content="5; url=/" />
                <title>Upload Success</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 0;
                        background-color: #f4f4f9;
                        color: #333;
                    }}
                    header {{
                        background-color: #445cb4;
                        color: white;
                        text-align: center;
                        padding: 1.5rem;
                    }}
                    main {{
                        margin: 2rem auto;
                        padding: 2rem;
                        background-color: white;
                        border-radius: 8px;
                        max-width: 600px;
                        text-align: center;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    }}
                    h1 {{
                        color: #445cb4;
                        margin-bottom: 1rem;
                    }}
                    p {{
                        margin-bottom: 1rem;
                        font-size: 1.1rem;
                    }}
                </style>
            </head>
            <body>
                <header>
                    <h1>Digitalcast</h1>
                    <p>Your seamless solution for digital signage and media display</p>
                </header>
                <main>
                    <h1>Upload Successful!</h1>
                    <p>File <strong>{filename}</strong> has been uploaded successfully to GCS and queued for scheduling.</p>
                    <p>You will be redirected back to the upload page in 5 seconds...</p>
                </main>
            </body>
            </html>
            """,
            200,
        )

    except Exception as e:
        logger.error(f"Exception occurred: {e}", exc_info=True)
        return f"An error occurred: {e}", 500


if __name__ == '__main__':
    logger.info("Starting Flask application on port 8080...")
    app.run(host='0.0.0.0', port=8080)
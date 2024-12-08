# Digitalcast: A Cloud-Based Digital Signage Solution
Datacenter Scale Computing (Fall 2024) - CSCI 5253-872

Instructor: Prof. Eric Keller

Fall 2024

Team 71 members:
- Aneesh Khole
- Uttara Ketkar

## Overview
Digitalcast is a scalable, cloud-based digital signage solution designed to facilitate media upload, scheduling, and display. It leverages Google Cloud Platform (GCP) services, including Google Cloud Storage (GCS), Pub/Sub, and Kubernetes, to provide a robust and user-friendly platform for managing digital signage content.

## Features
- User-friendly interface for media upload and scheduling.
- Support for images (JPEG, PNG, GIF) and videos (MP4).
- Real-time scheduling and display of media.
- Attribution of uploaded media to individual users.
- Scalability and fault tolerance using Kubernetes.

## System Components
### Frontend
- **`upload.html`**: A web interface for uploading media files and specifying scheduling details.
- **`display.html`**: A dynamic web interface for displaying scheduled media in real time.

### Backend
- **`app.py`**: Handles media uploads, validates input, stores metadata in PostgreSQL, and publishes messages to Pub/Sub.
- **`display.py`**: Fetches scheduled media metadata from PostgreSQL, retrieves media from GCS, and renders them on the display interface.
- **`worker.py`**: Processes Pub/Sub messages to ensure media readiness for display.

### Database
- **PostgreSQL**: Stores metadata, including filenames, usernames, and schedule times.

### Cloud Services
- **Google Cloud Storage (GCS)**: Stores uploaded media files.
- **Google Pub/Sub**: Manages message queuing between upload and display workflows.
- **Kubernetes**: Orchestrates and scales containerized services.

## System Workflow
1. **Media Upload**:
   - User uploads media via the `/upload` endpoint.
   - Media is validated and stored in GCS.
   - Metadata is saved in PostgreSQL and published to a Pub/Sub topic.

2. **Media Display**:
   - The `display.py` service queries PostgreSQL for media scheduled for the current time.
   - Media files are fetched from GCS and rendered on `display.html`.
   - The display updates periodically to reflect new or updated schedules.

3. **Asynchronous Processing**:
   - The `worker.py` service processes Pub/Sub messages, ensuring media is ready for display at the scheduled times.

## Deployment
### Prerequisites
- Python 3.9 or higher
- Google Cloud Platform account
- Docker
- Kubernetes (Minikube or GKE recommended)

NOTE: 
You need to have a service account setup in order to run this project. Store its credentials in the `digitalcast-ui` directory and grant it permissions for cloud SQL admin and  Object storage admin.

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/cu-csci-4253-datacenter-fall-2024/finalproject-final-project-team-71.git
   cd digitalcast
   ```
2. Set up environment variables for database and GCP credentials.
3. Build Docker images:
   ```bash
   docker build -t digitalcast-app -f Dockerfile .
   docker build -t digitalcast-display -f Dockerfile-display .
   docker build -t digitalcast-worker -f Dockerfile-worker .
   ```
4. Deploy the application to Kubernetes:
   ```bash
   kubectl apply -f k8s-deployment.yaml
   ```
5. Access the application via the provided LoadBalancer IP or port-forwarding.

## Usage
### Upload Media
1. Navigate to the `/upload` endpoint.
2. Enter your username, select a media file, and provide scheduling details.
3. Submit the form to upload your media.

### View Media
1. Navigate to the `/display` endpoint.
2. View media scheduled for the current time, along with the uploader's username.

## Debugging and Testing
### Debugging
- Enable logging to capture detailed events and errors.
- Check PostgreSQL database integrity for metadata consistency.
- Verify GCS file uploads and Pub/Sub message acknowledgments.

### Testing
- Unit tests for Flask endpoints to validate functionality.
- Integration tests to simulate the upload-to-display workflow.
- Kubernetes deployment testing to ensure scalability.

## Architecture
- **Frontend**: `upload.html` and `display.html`.
- **Backend**: Flask applications (`app.py`, `display.py`, `worker.py`).
- **Cloud Services**: GCS, Pub/Sub.
- **Database**: PostgreSQL.
- **Orchestration**: Kubernetes.


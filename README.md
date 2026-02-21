# Real-Time-Microphone-Transcription-Web-Application
Develop a fully functional, real-time speech-to-text application where audio captured from the user’s browser is streamed to the backend for transcription. All processing must operate on CPU-only using open-source speech recognition models.

### Video: [Watch the Video](https://www.youtube.com/watch?v=fudp5YaH9HA)

## Setup Instructions
### Local Development
#### 1. Clone the Repository

```bash
git clone https://github.com/FaysalMahmudSajan/Real-Time-Microphone-Transcription-Web-Application.git
cd Real-Time-Microphone-Transcription-Web-Application
```
#### 2. Create a Virtual Environment
Windows:
```bash
python -m venv .venv
.venv\Scripts\activate
```
macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```


Install Dependencies
backend:
```bash
pip install -r backend/requirements.txt
```
frontend:

*Prerequisite install Node.JS*
```bash
cd frontend
npm install
```

#### 3. Run the Application
- frontend
```bash
npm run dev
```
This will:
1. Start the development server
2. Make the API available at http://localhost:3000
- backecd backend
```bash
cd backend
uvicorn main:app --port 8000 --reload
```
This will:

1. Start the development server
2. Enable auto-reload for code changes
3. Make the API available at http://localhost:8000
Access the API documentation at http://localhost:8000/docs

### Docker Setup
Running the Docker Compose
Run the container from your locally built image:

```bash
docker compose up --build
```

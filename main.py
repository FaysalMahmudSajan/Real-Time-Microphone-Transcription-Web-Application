from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base, TranscriptionSession
from faster_whisper import WhisperModel
import asyncio
import json
import os
import time
import tempfile
from concurrent.futures import ThreadPoolExecutor

# Initialize Database
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Model (CPU-friendly settings)
# int8 quantization significantly reduces CPU usage with minimal accuracy loss
model = WhisperModel("tiny", device="cpu", compute_type="int8")

# Thread pool for running blocking transcription tasks
executor = ThreadPoolExecutor(max_workers=1)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def transcribe_file(file_path: str) -> str:
    """Runs transcription on a file path using Faster Whisper."""
    segments, _ = model.transcribe(file_path, beam_size=5)
    # Combine segments into a single string
    text = " ".join([segment.text for segment in segments])
    return text.strip()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    
    # Create a temp file to accumulate audio stream
    # We use a file because faster-whisper/ffmpeg handles file headers (WebM) robustly
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    temp_filename = temp_file.name
    temp_file.close()
    
    start_time = time.time()
    
    try:
        while True:
            # Receive audio chunk from browser
            data = await websocket.receive_bytes()
            
            # Append to the temporary file
            with open(temp_filename, "ab") as f:
                f.write(data)
            
            # Run transcription in a separate thread to keep WebSocket responsive
            loop = asyncio.get_event_loop()
            partial_transcript = await loop.run_in_executor(executor, transcribe_file, temp_filename)
            
            # Send partial result back to client
            await websocket.send_json({"type": "partial", "text": partial_transcript})
            
    except WebSocketDisconnect:
        # Session ended
        end_time = time.time()
        duration = end_time - start_time
        
        # Final transcription pass
        final_transcript = transcribe_file(temp_filename)
        word_count = len(final_transcript.split()) if final_transcript else 0
        
        # Persist to Database
        db_session = TranscriptionSession(
            transcript=final_transcript,
            duration=duration,
            word_count=word_count,
            created_at=start_time
        )
        db.add(db_session)
        db.commit()
        
        # Cleanup
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
            
    except Exception as e:
        print(f"Error: {e}")
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

@app.get("/sessions")
def get_sessions(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(TranscriptionSession).order_by(TranscriptionSession.id.desc()).offset(skip).limit(limit).all()

@app.get("/sessions/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(TranscriptionSession).filter(TranscriptionSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
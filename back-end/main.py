from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import AsyncSessionLocal, engine, Base, TranscriptionSession
from faster_whisper import WhisperModel
import asyncio
import os
import time
import tempfile
from concurrent.futures import ThreadPoolExecutor

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
# model = WhisperModel("small", device="cpu", compute_type="int8")

# Thread pool for running blocking transcription tasks
executor = ThreadPoolExecutor(max_workers=2)

async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db
        
@app.on_event("startup")
async def startup_event():
    await startup()

def transcribe_file(file_path: str) -> str:
    """Runs transcription on a file path using Faster Whisper."""
    segments, info = model.transcribe(
        file_path,
        language="en",
        # vad_filter=True,
        # vad_parameters=dict(min_silence_duration_ms=500), 
        beam_size=1
        )
    # Combine segments into a single string
    text = " ".join([segment.text for segment in segments])
    print(f"Transcription: {text}")
    return text.strip()

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
#     await websocket.accept()
    
#     # Create a temp file to accumulate audio stream
#     # We use a file because faster-whisper/ffmpeg handles file headers (WebM) robustly
#     temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
#     temp_filename = temp_file.name
#     temp_file.close()
    
#     start_time = time.time()
    
#     try:
#         while True:
#             # Receive audio chunk from browser
#             data = await websocket.receive_bytes()
            
#             # Append to the temporary file
#             with open(temp_filename, "ab") as f:
#                 f.write(data)
            
#             # Run transcription in a separate thread to keep WebSocket responsive
#             loop = asyncio.get_event_loop()
#             partial_transcript = await loop.run_in_executor(executor, transcribe_file, temp_filename)
            
#             # Send partial result back to client
#             await websocket.send_json({"type": "partial", "text": partial_transcript})
            
#     except WebSocketDisconnect:
#         # Session ended
#         end_time = time.time()
#         duration = end_time - start_time
        
#         # Final transcription pass
#         final_transcript = transcribe_file(temp_filename)
#         word_count = len(final_transcript.split()) if final_transcript else 0
        
#         # Persist to Database
#         db_session = TranscriptionSession(
#             transcript=final_transcript,
#             duration=duration,
#             word_count=word_count,
#             created_at=start_time
#         )
#         db.add(db_session)
#         await db.commit()
        
#         # Cleanup
#         if os.path.exists(temp_filename):
#             os.remove(temp_filename)
            
#     except Exception as e:
#         print(f"Error: {e}")
#         if os.path.exists(temp_filename):
#             os.remove(temp_filename)


CHUNK_TRANSCRIBE_INTERVAL = 3  # seconds

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".webm")
    temp_filename = temp_file.name
    temp_file.close()
    
    start_time = time.time()
    last_transcribe_time = time.time()
    
    try:
        while True:
            data = await websocket.receive_bytes()
            
            with open(temp_filename, "ab") as f:
                f.write(data)
            
            current_time = time.time()
            
            # Transcribe every few seconds instead of every chunk
            if current_time - last_transcribe_time >= CHUNK_TRANSCRIBE_INTERVAL:
                
                loop = asyncio.get_event_loop()
                partial_transcript = await loop.run_in_executor(
                    executor,
                    transcribe_file,
                    temp_filename
                )
                
                await websocket.send_json({
                    "type": "partial",
                    "text": partial_transcript
                })
                
                last_transcribe_time = current_time

    except WebSocketDisconnect:
        end_time = time.time()
        duration = end_time - start_time

        # Final transcription
        loop = asyncio.get_event_loop()
        final_transcript = await loop.run_in_executor(
            executor,
            transcribe_file,
            temp_filename
        )

        word_count = len(final_transcript.split()) if final_transcript else 0

        db_session = TranscriptionSession(
            transcript=final_transcript,
            duration=duration,
            word_count=word_count,
            created_at=start_time
        )

        db.add(db_session)
        await db.commit()

    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)





@app.get("/sessions")
async def get_sessions(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TranscriptionSession).order_by(TranscriptionSession.id.desc()).offset(skip).limit(limit))
    return result.scalars().all()

@app.get("/sessions/{session_id}")
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TranscriptionSession).filter(TranscriptionSession.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

if __name__ == "__main__":
    import uvicorn
    uvicorn.run('main:app',port=8000,host='0.0.0.0',reload=True)
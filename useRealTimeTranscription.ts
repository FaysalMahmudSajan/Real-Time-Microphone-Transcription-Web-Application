import { useState, useRef, useCallback } from 'react';

interface TranscriptionState {
  isRecording: boolean;
  transcript: string;
  isConnected: boolean;
}

export function useRealTimeTranscription() {
  const [state, setState] = useState<TranscriptionState>({
    isRecording: false,
    transcript: '',
    isConnected: false,
  });

  const socketRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Connect to Backend WebSocket
      const socket = new WebSocket('ws://localhost:8000/ws');
      socketRef.current = socket;

      socket.onopen = () => {
        setState(prev => ({ ...prev, isConnected: true, isRecording: true, transcript: '' }));
        
        // Initialize MediaRecorder
        const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
        mediaRecorderRef.current = mediaRecorder;

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0 && socket.readyState === WebSocket.OPEN) {
            socket.send(event.data);
          }
        };

        // Send chunks every 1 second (balance between latency and overhead)
        mediaRecorder.start(1000);
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'partial') {
          setState(prev => ({ ...prev, transcript: data.text }));
        }
      };

      socket.onclose = () => {
        setState(prev => ({ ...prev, isConnected: false, isRecording: false }));
      };

    } catch (error) {
      console.error("Error accessing microphone:", error);
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
    
    if (socketRef.current) {
      socketRef.current.close();
    }
    
    setState(prev => ({ ...prev, isRecording: false }));
  }, []);

  return {
    ...state,
    startRecording,
    stopRecording
  };
}
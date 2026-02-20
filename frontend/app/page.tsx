"use client";

import React, { useEffect, useState } from 'react';
import { useRealTimeTranscription } from '../hooks/useRealTimeTranscription';

interface Session {
  id: number;
  transcript: string;
  duration: number;
  word_count: number;
  created_at: number;
}

export default function Home() {
  const { isRecording, isConnected, transcript, startRecording, stopRecording } = useRealTimeTranscription();
  const [sessions, setSessions] = useState<Session[]>([]);

  const fetchSessions = async () => {
    try {
      const res = await fetch('http://localhost:8000/sessions');
      const data = await res.json();
      setSessions(data);
    } catch (err) {
      console.error("Failed to fetch sessions", err);
    }
  };

  // Refresh sessions when recording stops
  useEffect(() => {
    if (!isRecording) {
      // Add a delay to allow the backend to save the session before fetching
      const timer = setTimeout(() => {
        fetchSessions();
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [isRecording]);

  // Initial fetch
  useEffect(() => {
    fetchSessions();
  }, []);

  return (
    <main className="min-h-screen p-8 bg-gray-50 text-gray-900 font-sans">
      <div className="max-w-4xl mx-auto">
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-bold mb-2">Real-Time Live Transcription</h1>
        </header>

        {/* Recording Controls */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8 text-center">
          <div className="mb-4">
            {!isRecording ? (
              <button
                onClick={startRecording}
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-full transition-colors"
              >
                Start Recording
              </button>
            ) : (
              <button
                onClick={stopRecording}
                className="bg-red-600 hover:bg-red-700 text-white font-bold py-3 px-6 rounded-full transition-colors animate-pulse"
              >
                Stop Recording
              </button>
            )}
          </div>
          <div className="text-sm text-gray-500">
            Status: {isConnected ? <span className="text-green-600 font-semibold">Connected</span> : "Disconnected"}
          </div>
        </div>

        {/* Live Transcript Area */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8 min-h-[200px]">
          <h2 className="text-xl font-semibold mb-4 border-b pb-2">Live Transcript</h2>
          <div className="whitespace-pre-wrap text-lg leading-relaxed text-gray-800">
            {transcript || <span className="text-gray-400 italic">Speak to see transcription...</span>}
          </div>
        </div>

        {/* Past Sessions */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Previous Sessions</h2>
            <button onClick={fetchSessions} className="text-blue-600 text-sm hover:underline">Refresh</button>
          </div>
          
          <div className="space-y-4">
            {sessions.map((session) => (
              <div key={session.id} className="border rounded p-4 hover:bg-gray-50 transition">
                <div className="flex justify-between text-sm text-gray-500 mb-2">
                  <span>ID: {session.id}</span>
                  <span>{new Date(session.created_at * 1000).toLocaleString()}</span>
                </div>
                <p className="text-gray-800 mb-2 line-clamp-2">{session.transcript}</p>
                <div className="flex gap-4 text-xs font-medium text-gray-600">
                  <span>Duration: {session.duration.toFixed(1)}s</span>
                  <span>Words: {session.word_count}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}
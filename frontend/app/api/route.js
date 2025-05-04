import { NextResponse } from 'next/server';
import { spawn } from 'child_process';

// Option 1: Utiliser child_process pour démarrer le backend
let backendProcess = null;

export async function GET(request) {
  // Démarrer le backend s'il n'est pas déjà en cours d'exécution
  if (!backendProcess) {
    backendProcess = spawn('python', ['backend/app.py']);
    
    backendProcess.stdout.on('data', (data) => {
      console.log(`Backend stdout: ${data}`);
    });
    
    backendProcess.stderr.on('data', (data) => {
      console.error(`Backend stderr: ${data}`);
    });
    
    // Attendre le démarrage du backend
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
  
  // Rediriger la requête vers le backend
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  const response = await fetch(`${backendUrl}${request.url.pathname}`);
  const data = await response.json();
  
  return NextResponse.json(data);
}

export async function POST(request) {
  const body = await request.json();
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
  
  const response = await fetch(`${backendUrl}${request.url.pathname}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  
  const data = await response.json();
  return NextResponse.json(data);
}
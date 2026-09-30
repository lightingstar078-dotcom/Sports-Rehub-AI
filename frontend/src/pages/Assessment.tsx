import { useEffect, useRef, useState } from 'react';
import { AlertTriangle, Camera, CheckCircle2, Loader2, PauseCircle, Play, Upload } from 'lucide-react';
import { api } from '../services/api';
import { useAppStore } from '../store/appStore';

const tests = [
  { id: 'squat', name: 'Squat', desc: 'Assess knee/hip control, ROM and symmetry.' },
  { id: 'single_leg_hop', name: 'Single-Leg Hop', desc: 'Assess landing control and unilateral stability.' },
  { id: 'single_leg_balance', name: 'Single-Leg Balance', desc: 'Assess postural stability and consistency.' },
];
const questions = [
  'I feel confident performing this movement.', 'I trust my recovering body part.', 'I feel ready to increase activity.',
  'I am worried about reinjury.', 'I can perform sport-specific movements comfortably.', 'I understand my current recovery status.',
];

export function Assessment({ onDone }: { onDone: (page: string) => void }) {
  const athlete = useAppStore(s => s.athlete);
  const mode = useAppStore(s => s.network);
  const setCurrent = useAppStore(s => s.setCurrent);
  const [test, setTest] = useState('squat'); const [step, setStep] = useState(1); const [file, setFile] = useState<File | null>(null);
  const [pain, setPain] = useState(3); const [answers, setAnswers] = useState<number[]>(questions.map(() => 4));
  const [state, setState] = useState<any>(null); const [result, setResult] = useState<any>(null); const [busy, setBusy] = useState(false); const [recording, setRecording] = useState(false); const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null); const canvasRef = useRef<HTMLCanvasElement>(null); const timerRef = useRef<number | undefined>(undefined);
  const streamRef = useRef<MediaStream | null>(null); const chunks = useRef<Blob[]>([]); const recorder = useRef<MediaRecorder | null>(null);
  // The reinjury-fear item is negative, therefore it is reverse scored.
  const psychologicalReadiness = Math.round((answers.reduce((sum, answer, index) => sum + (index === 3 ? 6 - answer : answer), 0) / (answers.length * 5)) * 100);

  function stopCamera() { if (timerRef.current) { window.clearInterval(timerRef.current); timerRef.current = undefined; } (streamRef.current || cameraStream)?.getTracks().forEach(track => track.stop()); streamRef.current = null; setCameraStream(null); }
  async function openCamera() {
    stopCamera();
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      setState({ status: 'ERROR', message: 'Camera access needs localhost or HTTPS. Open the app at http://localhost:5173, or use an HTTPS deployment.' });
      setStep(2); return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: { ideal: 1280 } }, audio: false });
      // The effect below attaches this only after React has rendered <video>.
      streamRef.current = stream; setCameraStream(stream); setState(null); setStep(2);
    } catch (error: any) {
      stopCamera();
      const message = error?.name === 'NotAllowedError' ? 'Camera permission was denied. Allow camera access in your browser settings, then try again.' : error?.name === 'NotFoundError' ? 'No camera was found on this device.' : `Camera could not start${error?.name ? ` (${error.name})` : ''}. ${error?.message || 'Check that no other app is using it.'}`;
      setState({ status: 'ERROR', message });
    }
  }
  function startRecording() {
    if (!streamRef.current) return;
    try {
      chunks.current = []; const mimeType = MediaRecorder.isTypeSupported('video/webm;codecs=vp8') ? 'video/webm;codecs=vp8' : undefined;
      const activeRecorder = mimeType ? new MediaRecorder(streamRef.current, { mimeType }) : new MediaRecorder(streamRef.current);
      activeRecorder.ondataavailable = event => { if (event.data.size) chunks.current.push(event.data); };
      activeRecorder.onstop = () => { const blob = new Blob(chunks.current, { type: activeRecorder.mimeType || 'video/webm' }); setFile(new File([blob], 'webcam.webm', { type: blob.type })); setRecording(false); stopCamera(); setStep(3); };
      activeRecorder.start(); recorder.current = activeRecorder; setRecording(true);
    } catch { setState({ status: 'ERROR', message: 'This browser cannot record from the selected camera.' }); }
  }
  async function submit() {
    if (!file || !athlete) return; setBusy(true); const body = new FormData();
    body.append('athlete_id', String(athlete.id)); body.append('exercise', test); body.append('pain', String(pain));
    body.append('psychological_readiness', String(psychologicalReadiness));
    body.append('psychology_json', JSON.stringify(questions.map((question, index) => ({ question, response: answers[index] }))));
    body.append('file', file);
    try { const assessment = await api<any>('/api/assessment', { method: 'POST', body }, mode); setCurrent(assessment); setResult(assessment); setStep(6); }
    catch (error: any) { setState({ status: 'ERROR', message: error.message || 'Assessment failed' }); setStep(5); } finally { setBusy(false); }
  }
  useEffect(() => {
    if (step !== 2 || !cameraStream || !videoRef.current) return;
    const video = videoRef.current;
    let cancelled = false;
    video.srcObject = cameraStream;
    const startPreview = async () => {
      try {
        await video.play();
        if (cancelled) return;
        timerRef.current = window.setInterval(async () => {
          const canvas = canvasRef.current; if (!canvas || video.readyState < 2) return;
          canvas.width = video.videoWidth; canvas.height = video.videoHeight;
          canvas.getContext('2d')?.drawImage(video, 0, 0);
          canvas.toBlob(async blob => {
            if (!blob) return;
            const body = new FormData(); body.append('file', blob, 'frame.jpg');
            try { setState(await api('/api/vision/detect-human', { method: 'POST', body }, mode)); }
            catch (error: any) { setState({ status: 'ERROR', message: error.message || 'Human validation is unavailable.' }); }
          }, 'image/jpeg', 0.75);
        }, 1100);
      } catch (error: any) { setState({ status: 'ERROR', message: `Camera preview could not play. ${error?.message || ''}` }); }
    };
    void startPreview();
    return () => { cancelled = true; if (timerRef.current) { window.clearInterval(timerRef.current); timerRef.current = undefined; } if (video.srcObject === cameraStream) video.srcObject = null; };
  }, [cameraStream, mode, step]);
  useEffect(() => () => { streamRef.current?.getTracks().forEach(track => track.stop()); }, []);
  const stateText = step === 3 && file ? 'Video selected. Full-body validation runs before analysis.' : state?.message || 'Checking human and full-body visibility…';

  return <div className="assessment">
    <div className="stepper">{['Test', 'Human Validation', 'Video', 'Pain + Mind', 'AI + ML', 'Result'].map((label, index) => <div className={step === index + 1 ? 'step active' : step > index + 1 ? 'step done' : 'step'} key={label}><span>{index + 1}</span>{label}</div>)}</div>
    {step === 1 && <section className="card"><div className="card-head"><div><h2>Choose Functional Test</h2><p>Select one test and follow the camera positioning guidance.</p></div></div><div className="test-cards">{tests.map(item => <button onClick={() => setTest(item.id)} className={test === item.id ? 'test-card selected' : 'test-card'} key={item.id}><b>{item.name}</b><span>{item.desc}</span></button>)}</div><div className="actions"><button className="primary" onClick={openCamera}>Open Camera <Camera size={17} /></button><label className="secondary file-btn"><Upload size={17} /> Upload Video<input type="file" accept="video/*" hidden onChange={event => { const selected = event.target.files?.[0]; if (selected) { stopCamera(); setState(null); setFile(selected); setStep(3); } }} /></label></div></section>}
    {(step === 2 || step === 3) && <section className="card camera-card"><div className="video-shell"><video ref={videoRef} muted playsInline /><div className="overlay"><div className={`human-state ${state?.full_body_visible ? 'ok' : 'wait'}`}>{state?.full_body_visible ? <><CheckCircle2 size={17} /> Human + Full Body Ready</> : <><AlertTriangle size={17} />{stateText}</>}</div></div></div><canvas ref={canvasRef} hidden /><div className="camera-controls">{step === 2 && state?.full_body_visible && <button className="primary" onClick={recording ? () => recorder.current?.stop() : startRecording}>{recording ? <><PauseCircle size={17} /> Stop Recording</> : <><Play size={17} /> Start Movement Test</>}</button>}{step === 3 && file && <><div className="file-chip">{file.name}</div><button className="primary" onClick={() => setStep(4)}>Continue <CheckCircle2 size={17} /></button></>}</div></section>}
    {step === 4 && <section className="card form-card"><div className="card-head"><div><h2>Athlete Report</h2><p>These values are athlete-reported and remain separate from video-derived features.</p></div></div><label className="range-label"><span>Pain: <b>{pain}/10</b></span><input type="range" min="0" max="10" value={pain} onChange={event => setPain(Number(event.target.value))} /></label><div className="psych"><h3>Psychological Readiness</h3>{questions.map((question, index) => <label key={question}><span>{index + 1}. {question}</span><select value={answers[index]} onChange={event => setAnswers(values => values.map((value, itemIndex) => itemIndex === index ? Number(event.target.value) : value))}>{[1, 2, 3, 4, 5].map(value => <option key={value} value={value}>{value}</option>)}</select></label>)}<div className="psych-score">Normalized score <b>{psychologicalReadiness}/100</b></div></div><div className="actions"><button className="primary" onClick={submit} disabled={busy || !file}>{busy ? <><Loader2 className="spin" size={17} /> Analyzing…</> : <>Run AI + ML Analysis</>}</button></div></section>}
    {step === 5 && state?.status === 'ERROR' && <section className="card error-card"><AlertTriangle /><h2>Assessment could not finish</h2><p>{state.message}</p><button className="primary" onClick={() => setStep(4)}>Go Back</button></section>}
    {step === 6 && <section className="card"><div className="success-result"><CheckCircle2 size={42} /><div><div className="eyebrow">ASSESSMENT SAVED</div><h2>{result?.readiness_score}/100 · {result?.status}</h2><p>{result?.analysis_json?.guidance?.[0] || 'The result was stored with compressed video metadata and assessment features.'}</p><div className="actions"><button className="primary" onClick={() => onDone('dashboard')}>View Dashboard</button></div></div></div></section>}
  </div>;
}

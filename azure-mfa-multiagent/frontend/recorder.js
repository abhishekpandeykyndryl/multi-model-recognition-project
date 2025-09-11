// very small recorder using MediaRecorder to capture 16kHz WAV is non-trivial in-browser
// For demo we record as webm/ogg and send to backend which should accept and convert.

let mediaRecorder, audioChunks
const startRec = async (secs=4)=>{
  const s = await navigator.mediaDevices.getUserMedia({audio:true})
  mediaRecorder = new MediaRecorder(s)
  audioChunks = []
  mediaRecorder.ondataavailable = e=> audioChunks.push(e.data)
  mediaRecorder.start()
  return new Promise(res=> setTimeout(async ()=>{
    mediaRecorder.stop()
    mediaRecorder.onstop = async ()=>{
      const blob = new Blob(audioChunks, {type: audioChunks[0].type})
      res(blob)
    }
  }, secs*1000))
}

// example usage wired in index.html
document.getElementById('rec-voice').onclick = async ()=>{
  const email = document.getElementById('email').value
  const blob = await startRec(4)
  const fd = new FormData(); fd.append('email', email); fd.append('file', blob, 'voice.webm')
  const r = await fetch('/enroll/voice', {method:'POST', body: fd})
  alert(await r.text())
}

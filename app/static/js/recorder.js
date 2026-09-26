/**
 * Audio Transcription Studio - Live Voice Recorder
 * Canvas Oscilloscope adapts to light & dark theme dynamically.
 */
class VoiceRecorder {
  constructor(options = {}) {
    this.canvas = document.getElementById("visualizer-canvas");
    this.canvasCtx = this.canvas ? this.canvas.getContext("2d") : null;
    this.timerEl = document.getElementById("recording-timer");
    this.liveSpeechText = document.getElementById("live-speech-text");
    this.recordBtn = document.getElementById("record-toggle-btn");
    this.recordBtnText = document.getElementById("record-btn-text");
    this.cancelBtn = document.getElementById("record-cancel-btn");
    this.recDot = document.getElementById("rec-dot");

    this.onRecordingComplete = options.onRecordingComplete || null;

    this.mediaStream = null;
    this.mediaRecorder = null;
    this.recordedChunks = [];
    this.audioContext = null;
    this.analyser = null;
    this.sourceNode = null;
    this.animFrameId = null;

    this.isRecording = false;
    this.timerInterval = null;
    this.secondsElapsed = 0;

    // Web Speech API for immediate feedback
    this.recognition = null;
    this.initSpeechRecognition();

    this.bindEvents();
    this.drawIdleVisualizer();
  }

  initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;

      this.recognition.onresult = (event) => {
        let interimTranscript = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          interimTranscript += event.results[i][0].transcript;
        }
        if (interimTranscript.trim() && this.liveSpeechText) {
          this.liveSpeechText.textContent = interimTranscript;
        }
      };

      this.recognition.onerror = (err) => {
        console.warn("Live speech recognition notice:", err.error);
      };
    } else {
      if (this.liveSpeechText) {
        this.liveSpeechText.textContent = "Live microphone capture ready. Whisper will transcribe in full upon stop.";
      }
    }
  }

  bindEvents() {
    if (this.recordBtn) {
      this.recordBtn.addEventListener("click", () => this.toggleRecording());
    }
    if (this.cancelBtn) {
      this.cancelBtn.addEventListener("click", () => this.cancelRecording());
    }
    window.addEventListener("resize", () => this.resizeCanvas());
    this.resizeCanvas();
  }

  resizeCanvas() {
    if (!this.canvas) return;
    this.canvas.width = this.canvas.parentElement.clientWidth || 500;
  }

  async toggleRecording() {
    if (this.isRecording) {
      await this.stopRecording();
    } else {
      await this.startRecording();
    }
  }

  async startRecording() {
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      let mimeType = "audio/webm;codecs=opus";
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = MediaRecorder.isTypeSupported("audio/mp4") ? "audio/mp4" : "";
      }

      this.recordedChunks = [];
      this.mediaRecorder = mimeType
        ? new MediaRecorder(this.mediaStream, { mimeType })
        : new MediaRecorder(this.mediaStream);

      this.mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          this.recordedChunks.push(e.data);
        }
      };

      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.recordedChunks, {
          type: this.mediaRecorder.mimeType || "audio/webm"
        });
        if (this.onRecordingComplete) {
          this.onRecordingComplete(audioBlob);
        }
      };

      this.mediaRecorder.start(250);

      // Web Audio API
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.audioContext = new AudioCtx();
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream);
      this.sourceNode.connect(this.analyser);

      this.drawLiveVisualizer();

      if (this.recognition) {
        try { this.recognition.start(); } catch (e) {}
      }

      this.isRecording = true;
      this.recordBtn.classList.add("recording");
      this.recordBtnText.textContent = "Stop Recording";
      this.cancelBtn.classList.remove("hidden");
      if (this.recDot) this.recDot.classList.add("active");
      if (this.liveSpeechText) {
        this.liveSpeechText.textContent = "Listening... Speak naturally.";
      }

      this.secondsElapsed = 0;
      this.updateTimerDisplay();
      this.timerInterval = setInterval(() => {
        this.secondsElapsed++;
        this.updateTimerDisplay();
      }, 1000);

    } catch (err) {
      console.error("Microphone access error:", err);
      alert("Could not access microphone. Please check browser microphone permissions.");
    }
  }

  async stopRecording() {
    if (!this.isRecording) return;
    this.isRecording = false;

    if (this.mediaRecorder && this.mediaRecorder.state !== "inactive") {
      this.mediaRecorder.stop();
    }
    if (this.recognition) {
      try { this.recognition.stop(); } catch (e) {}
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((t) => t.stop());
    }
    if (this.audioContext && this.audioContext.state !== "closed") {
      await this.audioContext.close();
    }

    clearInterval(this.timerInterval);
    cancelAnimationFrame(this.animFrameId);

    this.recordBtn.classList.remove("recording");
    this.recordBtnText.textContent = "Record Again";
    this.cancelBtn.classList.add("hidden");
    if (this.recDot) this.recDot.classList.remove("active");

    this.drawIdleVisualizer();
  }

  cancelRecording() {
    this.isRecording = false;
    this.recordedChunks = [];
    if (this.mediaRecorder && this.mediaRecorder.state !== "inactive") {
      this.mediaRecorder.stop();
    }
    if (this.recognition) {
      try { this.recognition.stop(); } catch (e) {}
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((t) => t.stop());
    }
    if (this.audioContext && this.audioContext.state !== "closed") {
      await this.audioContext.close();
    }
    clearInterval(this.timerInterval);
    cancelAnimationFrame(this.animFrameId);

    this.recordBtn.classList.remove("recording");
    this.recordBtnText.textContent = "Start Recording";
    this.cancelBtn.classList.add("hidden");
    if (this.recDot) this.recDot.classList.remove("active");
    this.secondsElapsed = 0;
    this.updateTimerDisplay();
    if (this.liveSpeechText) {
      this.liveSpeechText.textContent = "Recording cancelled.";
    }
    this.drawIdleVisualizer();
  }

  updateTimerDisplay() {
    const hrs = String(Math.floor(this.secondsElapsed / 3600)).padStart(2, "0");
    const mins = String(Math.floor((this.secondsElapsed % 3600) / 60)).padStart(2, "0");
    const secs = String(this.secondsElapsed % 60).padStart(2, "0");
    if (this.timerEl) {
      this.timerEl.textContent = `${hrs}:${mins}:${secs}`;
    }
  }

  getThemeColor() {
    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    return isLight ? "#1d4ed8" : "#3b82f6";
  }

  drawLiveVisualizer() {
    if (!this.analyser || !this.canvasCtx || !this.canvas) return;

    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    const width = this.canvas.width;
    const height = this.canvas.height;

    const render = () => {
      if (!this.isRecording) return;
      this.animFrameId = requestAnimationFrame(render);

      this.analyser.getByteTimeDomainData(dataArray);

      this.canvasCtx.clearRect(0, 0, width, height);

      this.canvasCtx.lineWidth = 2;
      this.canvasCtx.strokeStyle = this.getThemeColor();
      this.canvasCtx.beginPath();

      const sliceWidth = width / bufferLength;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * height) / 2;

        if (i === 0) {
          this.canvasCtx.moveTo(x, y);
        } else {
          this.canvasCtx.lineTo(x, y);
        }

        x += sliceWidth;
      }

      this.canvasCtx.lineTo(width, height / 2);
      this.canvasCtx.stroke();
    };

    render();
  }

  drawIdleVisualizer() {
    if (!this.canvasCtx || !this.canvas) return;
    const width = this.canvas.width;
    const height = this.canvas.height;

    this.canvasCtx.clearRect(0, 0, width, height);

    const isLight = document.documentElement.getAttribute("data-theme") === "light";
    this.canvasCtx.strokeStyle = isLight ? "#cbd2de" : "#2d3546";
    this.canvasCtx.lineWidth = 1.5;
    this.canvasCtx.beginPath();
    this.canvasCtx.moveTo(0, height / 2);
    this.canvasCtx.lineTo(width, height / 2);
    this.canvasCtx.stroke();
  }
}

window.VoiceRecorder = VoiceRecorder;

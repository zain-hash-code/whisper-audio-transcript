/**
 * Audio Transcription Studio - Application Controller
 * Handles dual themes (Light & Dark), audio playback synchronization,
 * and manuscript timeline navigation.
 */
document.addEventListener("DOMContentLoaded", () => {
  // Theme Management
  const themeToggle = document.getElementById("theme-toggle");
  const themeLabel = document.getElementById("theme-label");
  const sunIcon = document.querySelector(".sun-icon");
  const moonIcon = document.querySelector(".moon-icon");

  function initTheme() {
    const savedTheme = localStorage.getItem("studio_theme");
    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const initialTheme = savedTheme || (systemPrefersDark ? "dark" : "light");
    applyTheme(initialTheme);
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("studio_theme", theme);
    if (theme === "light") {
      themeLabel.textContent = "Light";
      sunIcon.classList.add("hidden");
      moonIcon.classList.remove("hidden");
    } else {
      themeLabel.textContent = "Dark";
      moonIcon.classList.add("hidden");
      sunIcon.classList.remove("hidden");
    }
    if (window.studioRecorder) {
      window.studioRecorder.drawIdleVisualizer();
    }
  }

  themeToggle.addEventListener("click", () => {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
    const nextTheme = currentTheme === "dark" ? "light" : "dark";
    applyTheme(nextTheme);
  });

  initTheme();

  // Mode Tabs
  const tabUpload = document.getElementById("tab-upload");
  const tabRecord = document.getElementById("tab-record");
  const uploadPanel = document.getElementById("upload-panel");
  const recordPanel = document.getElementById("record-panel");

  // Upload & File Elements
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const browseBtn = document.getElementById("browse-btn");
  const filePreviewCard = document.getElementById("file-preview-card");
  const previewFilename = document.getElementById("preview-filename");
  const previewFormatBadge = document.getElementById("preview-format-badge");
  const previewFilemeta = document.getElementById("preview-filemeta");
  const removeFileBtn = document.getElementById("remove-file-btn");

  // Configuration & Actions
  const modelSelect = document.getElementById("model-select");
  const languageSelect = document.getElementById("language-select");
  const taskSelect = document.getElementById("task-select");
  const qualitySelect = document.getElementById("quality-select");
  const transcribeBtn = document.getElementById("transcribe-btn");
  const transcribeBtnText = document.getElementById("transcribe-btn-text");
  const progressContainer = document.getElementById("progress-container");
  const progressLabel = document.getElementById("progress-label");

  // Player Elements
  const audioPlayerCard = document.getElementById("audio-player-card");
  const audioPlayback = document.getElementById("audio-playback");
  const playerPlayBtn = document.getElementById("player-play-btn");
  const playIcon = document.getElementById("play-icon");
  const pauseIcon = document.getElementById("pause-icon");
  const playerJumpBack = document.getElementById("player-jump-back");
  const playerJumpFwd = document.getElementById("player-jump-fwd");
  const scrubberTrack = document.getElementById("scrubber-track");
  const scrubberProgress = document.getElementById("scrubber-progress");
  const scrubberThumb = document.getElementById("scrubber-thumb");
  const playerCurTime = document.getElementById("player-cur-time");
  const playerTotalTime = document.getElementById("player-total-time");
  const speedBtn = document.getElementById("speed-btn");
  const speedMenu = document.getElementById("speed-menu");
  const muteBtn = document.getElementById("mute-btn");
  const volSlider = document.getElementById("vol-slider");

  // Results Elements
  const resultsSection = document.getElementById("results-section");
  const statDuration = document.getElementById("stat-duration");
  const statTime = document.getElementById("stat-time");
  const statLang = document.getElementById("stat-lang");
  const statWords = document.getElementById("stat-words");

  // View Toggles & Search
  const viewSegmentsBtn = document.getElementById("view-segments-btn");
  const viewTextBtn = document.getElementById("view-text-btn");
  const segmentsContainer = document.getElementById("segments-container");
  const plainTextContainer = document.getElementById("plain-text-container");
  const fullTranscriptBody = document.getElementById("full-transcript-body");
  const copyDocBtn = document.getElementById("copy-doc-btn");
  const searchInput = document.getElementById("search-input");
  const searchCount = document.getElementById("search-count");

  // Export & Toast
  const copyBtn = document.getElementById("copy-btn");
  const exportDropdownBtn = document.getElementById("export-dropdown-btn");
  const exportMenu = document.getElementById("export-menu");
  const toast = document.getElementById("toast");
  const toastMsg = document.getElementById("toast-msg");
  const systemStatusText = document.getElementById("system-status-text");

  // App State
  let currentFile = null;
  let currentAudioUrl = null;
  let currentTranscription = null;

  // Initialize Voice Recorder
  window.studioRecorder = new VoiceRecorder({
    onRecordingComplete: (blob) => {
      const ext = blob.type.includes("mp4") ? "m4a" : "webm";
      currentFile = new File([blob], `voice_capture_${Date.now()}.${ext}`, { type: blob.type });
      setAudioSource(currentFile);
      transcribeBtn.disabled = false;
      showToast("Recording ready for transcription.");
    }
  });

  fetchHealth();

  // Mode Tab Navigation
  tabUpload.addEventListener("click", () => switchMode("upload"));
  tabRecord.addEventListener("click", () => switchMode("record"));

  function switchMode(mode) {
    if (mode === "upload") {
      tabUpload.classList.add("active");
      tabRecord.classList.remove("active");
      uploadPanel.classList.remove("hidden");
      recordPanel.classList.add("hidden");
    } else {
      tabRecord.classList.add("active");
      tabUpload.classList.remove("active");
      recordPanel.classList.remove("hidden");
      uploadPanel.classList.add("hidden");
      window.studioRecorder.resizeCanvas();
    }
  }

  // Quick Sample Audio Click
  document.querySelectorAll(".btn-sample").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const sampleFile = btn.dataset.sample;
      try {
        const resp = await fetch(`/samples/${sampleFile}`);
        if (!resp.ok) throw new Error("Could not load sample file.");
        const blob = await resp.blob();
        const file = new File([blob], sampleFile, { type: blob.type || "audio/mpeg" });
        handleSelectedFile(file);
        showToast(`Loaded ${sampleFile}`);
      } catch (err) {
        showToast("Error loading sample audio.");
      }
    });
  });

  // Dropzone Events
  browseBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleSelectedFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleSelectedFile(e.target.files[0]);
    }
  });

  removeFileBtn.addEventListener("click", () => clearCurrentFile());

  function handleSelectedFile(file) {
    currentFile = file;
    const mbSize = (file.size / (1024 * 1024)).toFixed(2);
    const ext = file.name.split(".").pop().toUpperCase() || "AUDIO";

    previewFilename.textContent = file.name;
    previewFormatBadge.textContent = ext;
    previewFilemeta.textContent = `${mbSize} MB`;

    filePreviewCard.classList.remove("hidden");
    dropzone.classList.add("hidden");

    setAudioSource(file);
    transcribeBtn.disabled = false;
  }

  function clearCurrentFile() {
    currentFile = null;
    fileInput.value = "";
    filePreviewCard.classList.add("hidden");
    dropzone.classList.remove("hidden");
    transcribeBtn.disabled = true;
    audioPlayerCard.classList.add("hidden");
    if (currentAudioUrl) {
      URL.revokeObjectURL(currentAudioUrl);
      currentAudioUrl = null;
    }
    audioPlayback.pause();
    audioPlayback.src = "";
  }

  function setAudioSource(fileOrBlob) {
    if (currentAudioUrl) {
      URL.revokeObjectURL(currentAudioUrl);
    }
    currentAudioUrl = URL.createObjectURL(fileOrBlob);
    audioPlayback.src = currentAudioUrl;
    audioPlayback.load();
    audioPlayerCard.classList.remove("hidden");
  }

  // Audio Player Controls
  playerPlayBtn.addEventListener("click", () => {
    if (audioPlayback.paused) {
      audioPlayback.play();
    } else {
      audioPlayback.pause();
    }
  });

  audioPlayback.addEventListener("play", () => {
    playIcon.classList.add("hidden");
    pauseIcon.classList.remove("hidden");
  });

  audioPlayback.addEventListener("pause", () => {
    pauseIcon.classList.add("hidden");
    playIcon.classList.remove("hidden");
  });

  audioPlayback.addEventListener("loadedmetadata", () => {
    playerTotalTime.textContent = formatDuration(audioPlayback.duration);
  });

  audioPlayback.addEventListener("timeupdate", () => {
    if (audioPlayback.duration) {
      const pct = (audioPlayback.currentTime / audioPlayback.duration) * 100;
      scrubberProgress.style.width = `${pct}%`;
      scrubberThumb.style.left = `${pct}%`;
      playerCurTime.textContent = formatDuration(audioPlayback.currentTime);
    }
    highlightPlaybackSync(audioPlayback.currentTime);
  });

  playerJumpBack.addEventListener("click", () => {
    audioPlayback.currentTime = Math.max(0, audioPlayback.currentTime - 5);
  });

  playerJumpFwd.addEventListener("click", () => {
    audioPlayback.currentTime = Math.min(audioPlayback.duration || 0, audioPlayback.currentTime + 5);
  });

  scrubberTrack.addEventListener("click", (e) => {
    const rect = scrubberTrack.getBoundingClientRect();
    const pos = (e.clientX - rect.left) / rect.width;
    if (audioPlayback.duration) {
      audioPlayback.currentTime = pos * audioPlayback.duration;
    }
  });

  // Speed Selector
  speedBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    speedMenu.classList.toggle("hidden");
  });

  speedMenu.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const speed = parseFloat(btn.dataset.speed);
      audioPlayback.playbackRate = speed;
      speedBtn.textContent = `${speed}x`;
      speedMenu.querySelectorAll("button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      speedMenu.classList.add("hidden");
    });
  });

  document.addEventListener("click", () => {
    speedMenu.classList.add("hidden");
    exportMenu.classList.add("hidden");
  });

  // Volume & Mute
  volSlider.addEventListener("input", (e) => {
    audioPlayback.volume = parseFloat(e.target.value);
    audioPlayback.muted = false;
  });

  muteBtn.addEventListener("click", () => {
    audioPlayback.muted = !audioPlayback.muted;
    volSlider.value = audioPlayback.muted ? 0 : audioPlayback.volume || 1;
  });

  // Run Transcription
  transcribeBtn.addEventListener("click", async () => {
    if (!currentFile) return;

    transcribeBtn.disabled = true;
    progressContainer.classList.remove("hidden");
    progressLabel.textContent = "Processing audio with Whisper model...";

    const formData = new FormData();
    formData.append("file", currentFile);
    formData.append("model", modelSelect.value);
    formData.append("language", languageSelect.value);
    formData.append("task", taskSelect.value);
    formData.append("beam_size", qualitySelect.value);
    formData.append("word_timestamps", "true");

    try {
      const response = await fetch("/api/transcribe", {
        method: "POST",
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Transcription failed." }));
        throw new Error(errorData.detail || `Server error (${response.status})`);
      }

      const result = await response.json();
      currentTranscription = result;
      displayResults(result);
      showToast("Transcription complete.");

    } catch (err) {
      console.error("Transcription error:", err);
      alert("Error: " + err.message);
    } finally {
      transcribeBtn.disabled = false;
      progressContainer.classList.add("hidden");
    }
  });

  // Display Results
  function displayResults(data) {
    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: "smooth" });

    statDuration.textContent = `${data.duration}s`;
    statTime.textContent = `${data.processing_time}s`;
    const langCode = (data.language || "en").toUpperCase();
    const conf = Math.round((data.language_probability || 1.0) * 100);
    statLang.textContent = `${langCode} (${conf}%)`;
    statWords.textContent = `${data.word_count || 0} words`;

    fullTranscriptBody.textContent = data.text || "";
    renderSegments(data.segments || []);
  }

  function renderSegments(segments) {
    segmentsContainer.innerHTML = "";
    if (!segments || segments.length === 0) {
      segmentsContainer.innerHTML = `<div style="color:var(--text-muted);text-align:center;padding:28px;">No speech detected in this recording.</div>`;
      return;
    }

    segments.forEach((seg) => {
      const row = document.createElement("div");
      row.className = "manuscript-segment";
      row.dataset.start = seg.start;
      row.dataset.end = seg.end;

      const cue = document.createElement("div");
      cue.className = "segment-cue";

      const playBtn = document.createElement("button");
      playBtn.className = "btn-cue-play";
      playBtn.title = "Play snippet";
      playBtn.innerHTML = `<svg viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>`;
      playBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        audioPlayback.currentTime = seg.start;
        audioPlayback.play();
      });

      const cueTime = document.createElement("span");
      cueTime.className = "cue-time";
      cueTime.textContent = `${formatDuration(seg.start)} - ${formatDuration(seg.end)}`;

      cue.appendChild(playBtn);
      cue.appendChild(cueTime);

      const speech = document.createElement("div");
      speech.className = "segment-speech";

      if (seg.words && seg.words.length > 0) {
        seg.words.forEach((w) => {
          const token = document.createElement("span");
          token.className = "word-token";
          token.textContent = w.word + " ";
          token.dataset.start = w.start;
          token.dataset.end = w.end;
          token.title = `[${w.start}s - ${w.end}s] Click to seek`;

          token.addEventListener("click", (e) => {
            e.stopPropagation();
            audioPlayback.currentTime = w.start;
            audioPlayback.play();
          });

          speech.appendChild(token);
        });
      } else {
        speech.textContent = seg.text;
      }

      const copyBtnSeg = document.createElement("button");
      copyBtnSeg.className = "btn-seg-copy";
      copyBtnSeg.title = "Copy snippet";
      copyBtnSeg.innerHTML = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>`;
      copyBtnSeg.addEventListener("click", (e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(seg.text);
        showToast("Snippet copied.");
      });

      row.appendChild(cue);
      row.appendChild(speech);
      row.appendChild(copyBtnSeg);

      row.addEventListener("click", () => {
        audioPlayback.currentTime = seg.start;
        audioPlayback.play();
      });

      segmentsContainer.appendChild(row);
    });
  }

  function highlightPlaybackSync(curTime) {
    const rows = segmentsContainer.querySelectorAll(".manuscript-segment");
    rows.forEach((row) => {
      const start = parseFloat(row.dataset.start);
      const end = parseFloat(row.dataset.end);

      if (curTime >= start && curTime <= end) {
        if (!row.classList.contains("active")) {
          rows.forEach((r) => r.classList.remove("active"));
          row.classList.add("active");
          row.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }

        row.querySelectorAll(".word-token").forEach((tok) => {
          const wStart = parseFloat(tok.dataset.start);
          const wEnd = parseFloat(tok.dataset.end);
          if (curTime >= wStart && curTime <= wEnd) {
            tok.classList.add("playing");
          } else {
            tok.classList.remove("playing");
          }
        });
      } else {
        row.classList.remove("active");
        row.querySelectorAll(".word-token").forEach((tok) => tok.classList.remove("playing"));
      }
    });
  }

  // Keyword Search
  searchInput.addEventListener("input", (e) => {
    const query = e.target.value.toLowerCase().trim();
    const rows = segmentsContainer.querySelectorAll(".manuscript-segment");
    let hits = 0;

    rows.forEach((row) => {
      const speech = row.querySelector(".segment-speech");
      const rawText = speech.textContent.toLowerCase();

      if (!query) {
        row.style.display = "flex";
        return;
      }

      if (rawText.includes(query)) {
        row.style.display = "flex";
        hits++;
      } else {
        row.style.display = "none";
      }
    });

    if (query) {
      searchCount.textContent = `${hits} ${hits === 1 ? 'match' : 'matches'}`;
      searchCount.classList.remove("hidden");
    } else {
      searchCount.classList.add("hidden");
    }
  });

  // View Switch (Timeline vs Document)
  viewSegmentsBtn.addEventListener("click", () => {
    viewSegmentsBtn.classList.add("active");
    viewTextBtn.classList.remove("active");
    segmentsContainer.classList.remove("hidden");
    plainTextContainer.classList.add("hidden");
  });

  viewTextBtn.addEventListener("click", () => {
    viewTextBtn.classList.add("active");
    viewSegmentsBtn.classList.remove("active");
    plainTextContainer.classList.remove("hidden");
    segmentsContainer.classList.add("hidden");
  });

  // Copy Full Transcript
  copyBtn.addEventListener("click", () => copyFullTranscript());
  copyDocBtn.addEventListener("click", () => copyFullTranscript());

  function copyFullTranscript() {
    if (!currentTranscription || !currentTranscription.text) {
      showToast("No transcription available to copy.");
      return;
    }
    navigator.clipboard.writeText(currentTranscription.text).then(() => {
      showToast("Transcript copied to clipboard.");
    }).catch(() => {
      showToast("Failed to copy transcript.");
    });
  }

  // Export Menu
  exportDropdownBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    exportMenu.classList.toggle("hidden");
  });

  exportMenu.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.stopPropagation();
      exportMenu.classList.add("hidden");
      const format = btn.dataset.format;
      await downloadExport(format);
    });
  });

  async function downloadExport(format) {
    if (!currentTranscription) {
      showToast("Please transcribe an audio file first.");
      return;
    }

    try {
      const response = await fetch(`/api/export?format=${format}&filename=${encodeURIComponent(currentFile ? currentFile.name : "transcript")}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(currentTranscription)
      });

      if (!response.ok) throw new Error("Export failed.");

      const blob = await response.blob();
      const disposition = response.headers.get("Content-Disposition");
      let filename = `transcript.${format === 'txt_timestamps' ? 'txt' : format}`;
      if (disposition && disposition.includes("filename=")) {
        filename = disposition.split("filename=")[1].replace(/['"]/g, "");
      }

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast(`Exported ${filename}`);
    } catch (err) {
      showToast("Failed to export file.");
    }
  }

  function formatDuration(secs) {
    if (!secs || isNaN(secs)) return "00:00";
    const mins = Math.floor(secs / 60);
    const remSecs = Math.floor(secs % 60);
    return `${String(mins).padStart(2, "0")}:${String(remSecs).padStart(2, "0")}`;
  }

  function showToast(msg) {
    toastMsg.textContent = msg;
    toast.classList.remove("hidden");
    setTimeout(() => {
      toast.classList.add("hidden");
    }, 2800);
  }

  async function fetchHealth() {
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const data = await res.json();
        if (data.status === "healthy") {
          systemStatusText.innerHTML = `CTranslate2 INT8 &bull; FFmpeg Engine Active`;
        }
      }
    } catch (e) {
      systemStatusText.textContent = "Connecting to Whisper Engine...";
    }
  }
});

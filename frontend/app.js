/**
 * MingStudio - Frontend Application Logic
 * Pure ES6+, Wavesurfer.js, SSE telemetry, Auto-Skip wizard logic.
 */

let wavesurfer = null;
let currentLanguage = 'ko';
let selectedReferenceId = null;
let studioConfig = null;
let downloadEventSource = null;

// DOM Elements
const dom = {
  gpuBadge: document.getElementById('gpuBadge'),
  gpuText: document.getElementById('gpuText'),
  modelStatusBadge: document.getElementById('modelStatusBadge'),
  modelStatusText: document.getElementById('modelStatusText'),
  btnOpenModelModal: document.getElementById('btnOpenModelModal'),
  btnShutdown: document.getElementById('btnShutdown'),
  modalModelWizard: document.getElementById('modalModelWizard'),
  btnCloseModal: document.getElementById('btnCloseModal'),
  modalShardStatus: document.getElementById('modalShardStatus'),
  modalProgressBar: document.getElementById('modalProgressBar'),
  telemetryStatus: document.getElementById('telemetryStatus'),
  telemetryPercent: document.getElementById('telemetryPercent'),
  telemetrySpeed: document.getElementById('telemetrySpeed'),
  telemetryEta: document.getElementById('telemetryEta'),
  telemetryBytes: document.getElementById('telemetryBytes'),
  telemetryActiveFile: document.getElementById('telemetryActiveFile'),
  btnStartDownload: document.getElementById('btnStartDownload'),
  btnStartDownloadText: document.getElementById('btnStartDownloadText'),
  btnCancelDownload: document.getElementById('btnCancelDownload'),

  languageContainer: document.getElementById('languageContainer'),
  currentLangLabel: document.getElementById('currentLangLabel'),
  tagsToolbar: document.getElementById('tagsToolbar'),
  ttsTextInput: document.getElementById('ttsTextInput'),
  charCount: document.getElementById('charCount'),
  btnGenerate: document.getElementById('btnGenerate'),
  btnGenerateText: document.getElementById('btnGenerateText'),

  tabVoiceDesign: document.getElementById('tabVoiceDesign'),
  tabVoiceClone: document.getElementById('tabVoiceClone'),
  paneVoiceDesign: document.getElementById('paneVoiceDesign'),
  paneVoiceClone: document.getElementById('paneVoiceClone'),
  voiceDesignPrompt: document.getElementById('voiceDesignPrompt'),
  dropZone: document.getElementById('dropZone'),
  referenceFileInput: document.getElementById('referenceFileInput'),
  referencePreview: document.getElementById('referencePreview'),
  refFileName: document.getElementById('refFileName'),
  btnRemoveRef: document.getElementById('btnRemoveRef'),
  cloneUploadStatus: document.getElementById('cloneUploadStatus'),

  emotionSelect: document.getElementById('emotionSelect'),
  speedSlider: document.getElementById('speedSlider'),
  speedVal: document.getElementById('speedVal'),
  pitchSlider: document.getElementById('pitchSlider'),
  pitchVal: document.getElementById('pitchVal'),

  waveform: document.getElementById('waveform'),
  waveformPlaceholder: document.getElementById('waveformPlaceholder'),
  btnPlayPause: document.getElementById('btnPlayPause'),
  btnStop: document.getElementById('btnStop'),
  btnDownloadWav: document.getElementById('btnDownloadWav'),
  audioCurrentTime: document.getElementById('audioCurrentTime'),
  audioDuration: document.getElementById('audioDuration'),
  historyList: document.getElementById('historyList'),
  historyCount: document.getElementById('historyCount'),
};

// ---------------------------------------------------------------------------
// 1. Initialization
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
  initWaveSurfer();
  initLucide();
  initEventListeners();
  await loadStudioConfig();
  await checkModelStatusAndAutoSkip();
  await loadHistory();
});

function initLucide() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

function initWaveSurfer() {
  try {
    wavesurfer = WaveSurfer.create({
      container: '#waveform',
      waveColor: 'rgba(6, 182, 212, 0.45)',
      progressColor: '#06b6d4',
      cursorColor: '#67e8f9',
      cursorWidth: 2,
      barWidth: 3,
      barGap: 2,
      barRadius: 3,
      height: 90,
      responsive: true,
      normalize: true,
    });

    wavesurfer.on('play', () => {
      dom.btnPlayPause.innerHTML = '<i data-lucide="pause" class="w-4 h-4 fill-current"></i>';
      initLucide();
    });

    wavesurfer.on('pause', () => {
      dom.btnPlayPause.innerHTML = '<i data-lucide="play" class="w-4 h-4 fill-current"></i>';
      initLucide();
    });

    wavesurfer.on('timeupdate', (currentTime) => {
      dom.audioCurrentTime.textContent = formatTime(currentTime);
    });

    wavesurfer.on('ready', () => {
      const dur = wavesurfer.getDuration();
      dom.audioDuration.textContent = formatTime(dur);
      dom.btnPlayPause.disabled = false;
      dom.btnStop.disabled = false;
      if (dom.waveformPlaceholder) {
        dom.waveformPlaceholder.style.display = 'none';
      }
    });

    wavesurfer.on('finish', () => {
      dom.btnPlayPause.innerHTML = '<i data-lucide="play" class="w-4 h-4 fill-current"></i>';
      initLucide();
    });
  } catch (e) {
    console.error('WaveSurfer initialization error:', e);
  }
}

// ---------------------------------------------------------------------------
// 2. Model Preflight Check & Auto-Skip Logic
// ---------------------------------------------------------------------------
async function checkModelStatusAndAutoSkip() {
  try {
    const res = await fetch('/api/model/status');
    const data = await res.json();

    // Hardware Telemetry
    if (data.gpu && data.gpu.cuda_available) {
      dom.gpuBadge.classList.remove('hidden');
      dom.gpuText.textContent = `${data.gpu.device_name} (${data.gpu.vram_total_gb} GB)`;
    }

    // Modal Shard Count update
    dom.modalShardStatus.textContent = `${data.safetensors_present} / ${data.safetensors_total} 완료`;

    if (data.ready) {
      // 0.1s AUTO-SKIP: Models are ready, do NOT pop up wizard
      dom.modalModelWizard.classList.add('hidden');
      setStudioBadgeReady();
      console.log('[MingStudio] Model preflight complete: Ready state engaged. Wizard skipped.');
    } else {
      // Missing weights: display status badge and prompt user via wizard modal
      setStudioBadgeMissing(data.safetensors_present, data.safetensors_total);
      dom.modalModelWizard.classList.remove('hidden');
      initLucide();
    }
  } catch (err) {
    console.error('Failed to query model status:', err);
    setStudioBadgeMissing(0, 30);
  }
}

function setStudioBadgeReady() {
  dom.modelStatusBadge.className =
    'flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-emerald-950/60 border border-emerald-600/60 text-xs text-emerald-300 shadow-md shadow-emerald-500/10';
  dom.modelStatusBadge.innerHTML = `
    <span class="relative flex h-2 w-2">
      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
      <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
    </span>
    <span>Ming-3.0 MoE 준비 완료 (7.9B)</span>
  `;
}

function setStudioBadgeMissing(present, total) {
  dom.modelStatusBadge.className =
    'flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-amber-950/60 border border-amber-600/60 text-xs text-amber-300';
  dom.modelStatusBadge.innerHTML = `
    <span class="relative flex h-2 w-2">
      <span class="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
    </span>
    <span>모델 다운로드 필요 (${present}/${total})</span>
  `;
}

// ---------------------------------------------------------------------------
// 3. 8-Thread Model Downloader & Real-time Telemetry
// ---------------------------------------------------------------------------
async function startModelDownload() {
  dom.btnStartDownload.disabled = true;
  dom.btnStartDownload.classList.add('opacity-70');
  dom.btnStartDownloadText.textContent = '다운로드 진행 중...';
  dom.btnCancelDownload.classList.remove('hidden');

  try {
    const res = await fetch('/api/model/download/start', { method: 'POST' });
    const data = await res.json();
    connectDownloadStream();
  } catch (err) {
    alert('다운로드 요청 실패: ' + err.message);
    dom.btnStartDownload.disabled = false;
    dom.btnStartDownload.classList.remove('opacity-70');
    dom.btnStartDownloadText.textContent = '원클릭 모델 다운로드 시작';
  }
}

function connectDownloadStream() {
  if (downloadEventSource) {
    downloadEventSource.close();
  }

  downloadEventSource = new EventSource('/api/model/download/stream');

  downloadEventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      updateDownloadUI(data);

      if (data.status === 'completed') {
        downloadEventSource.close();
        downloadEventSource = null;
        onDownloadCompleted();
      } else if (data.status === 'error' || data.status === 'cancelled') {
        downloadEventSource.close();
        downloadEventSource = null;
        dom.btnStartDownload.disabled = false;
        dom.btnStartDownload.classList.remove('opacity-70');
        dom.btnStartDownloadText.textContent = '다운로드 재시작';
        dom.btnCancelDownload.classList.add('hidden');
      }
    } catch (e) {
      console.error('SSE JSON parse error:', e);
    }
  };

  downloadEventSource.onerror = () => {
    // Fallback polling if SSE is closed
    setTimeout(pollDownloadProgress, 1000);
  };
}

async function pollDownloadProgress() {
  if (!downloadEventSource) {
    try {
      const res = await fetch('/api/model/download/progress');
      const data = await res.json();
      updateDownloadUI(data);
      if (data.is_downloading) {
        setTimeout(pollDownloadProgress, 500);
      } else if (data.status === 'completed') {
        onDownloadCompleted();
      }
    } catch (e) {}
  }
}

function updateDownloadUI(data) {
  let percent = data.percent || 0;
  if (percent >= 99.0 || data.status === 'completed') {
    percent = 100.0;
  }
  dom.modalProgressBar.style.width = `${percent}%`;
  dom.telemetryPercent.textContent = `${percent.toFixed(1)}%`;
  dom.telemetrySpeed.textContent = `${data.speed_mbps || 0} MB/s`;
  dom.telemetryEta.textContent = data.eta_str || '--';
  dom.telemetryBytes.textContent = `${data.downloaded_str || '16.8 GB'} / ${data.total_str || '16.8 GB'}`;

  if (data.active_files && data.active_files.length > 0) {
    dom.telemetryActiveFile.textContent = `다운로드 중: ${data.active_files.slice(0, 2).join(', ')}`;
  } else {
    dom.telemetryActiveFile.textContent = '';
  }

  dom.telemetryStatus.textContent =
    data.status === 'downloading' ? '8스레드 병렬 다운로드 진행 중...' :
    (data.status === 'completed' || percent === 100.0) ? '🎉 Ming-3.0 MoE 모델 준비 완료!' :
    data.status === 'cancelled' ? '다운로드 취소됨' : data.status;

  if (percent === 100.0 && !dom.modalModelWizard.classList.contains('hidden')) {
    onDownloadCompleted();
  }
}

function onDownloadCompleted() {
  dom.modalShardStatus.textContent = '30 / 30 완료 (Ready)';
  dom.modalProgressBar.style.width = '100%';
  dom.telemetryPercent.textContent = '100.0%';
  dom.telemetryStatus.textContent = '🎉 Ming-3.0 MoE 모델 준비 완료!';
  dom.btnStartDownload.classList.add('hidden');
  dom.btnCancelDownload.classList.add('hidden');
  setStudioBadgeReady();

  // Auto-dismiss modal after 0.8s
  setTimeout(() => {
    dom.modalModelWizard.classList.add('hidden');
  }, 800);
}

async function cancelDownload() {
  try {
    await fetch('/api/model/download/cancel', { method: 'POST' });
    if (downloadEventSource) {
      downloadEventSource.close();
      downloadEventSource = null;
    }
    dom.btnStartDownload.disabled = false;
    dom.btnStartDownload.classList.remove('opacity-70');
    dom.btnStartDownloadText.textContent = '다운로드 재시작';
    dom.btnCancelDownload.classList.add('hidden');
    dom.telemetryStatus.textContent = '다운로드가 취소되었습니다.';
  } catch (e) {
    console.error('Cancel failed:', e);
  }
}

// ---------------------------------------------------------------------------
// 4. Configuration, 7 Languages & 14 Emotion Tags
// ---------------------------------------------------------------------------
async function loadStudioConfig() {
  try {
    const res = await fetch('/api/config');
    studioConfig = await res.json();

    // Render 7 Languages
    dom.languageContainer.innerHTML = '';
    studioConfig.languages.forEach((lang) => {
      const chip = document.createElement('div');
      chip.className = `lang-chip ${lang.code === currentLanguage ? 'active' : ''}`;
      chip.dataset.code = lang.code;
      chip.innerHTML = `
        <span class="text-base sm:text-lg mb-0.5">${lang.flag}</span>
        <span class="text-[11px] font-medium text-gray-300">${lang.name}</span>
      `;
      chip.addEventListener('click', () => selectLanguage(lang.code));
      dom.languageContainer.appendChild(chip);
    });

    // Render 14 Paralinguistic Tags
    dom.tagsToolbar.innerHTML = '';
    studioConfig.paralinguistic_tags.forEach((tagItem) => {
      const tagBtn = document.createElement('button');
      tagBtn.type = 'button';
      tagBtn.className = 'tag-chip';
      tagBtn.title = tagItem.desc;
      tagBtn.innerHTML = `
        <span>${tagItem.icon}</span>
        <span class="font-mono text-cyan-400 font-semibold">${tagItem.tag}</span>
        <span class="text-gray-400 text-[10px]">${tagItem.name}</span>
      `;
      tagBtn.addEventListener('click', () => insertParalinguisticTag(tagItem.tag));
      dom.tagsToolbar.appendChild(tagBtn);
    });

    // Populate initial sample text
    const defaultLang = studioConfig.languages.find((l) => l.code === currentLanguage);
    if (defaultLang && !dom.ttsTextInput.value.trim()) {
      dom.ttsTextInput.value = defaultLang.sample;
      updateCharCount();
    }
  } catch (err) {
    console.error('Failed to load studio config:', err);
  }
}

function selectLanguage(code) {
  currentLanguage = code;
  document.querySelectorAll('.lang-chip').forEach((el) => {
    el.classList.toggle('active', el.dataset.code === code);
  });
  const langObj = studioConfig.languages.find((l) => l.code === code);
  if (langObj) {
    dom.currentLangLabel.textContent = `${langObj.name} (${langObj.code})`;
    // Update sample if text field is default
    dom.ttsTextInput.value = langObj.sample;
    updateCharCount();
  }
}

function insertParalinguisticTag(tagStr) {
  const textarea = dom.ttsTextInput;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const original = textarea.value;

  const insertText = ` ${tagStr} `;
  textarea.value = original.substring(0, start) + insertText + original.substring(end);
  textarea.focus();
  const nextPos = start + insertText.length;
  textarea.setSelectionRange(nextPos, nextPos);
  updateCharCount();
}

function updateCharCount() {
  const len = dom.ttsTextInput.value.length;
  dom.charCount.textContent = `${len} 글자`;
}

// ---------------------------------------------------------------------------
// 5. Voice Generation (Synthesis) Pipeline
// ---------------------------------------------------------------------------
async function generateSpeech() {
  const text = dom.ttsTextInput.value.trim();
  if (!text) {
    alert('합성할 텍스트를 입력해 주세요.');
    dom.ttsTextInput.focus();
    return;
  }

  // Loading UI state
  dom.btnGenerate.disabled = true;
  dom.btnGenerate.classList.add('opacity-70');
  dom.btnGenerateText.textContent = '⚡ 음성 합성 렌더링 중...';

  const payload = {
    text: text,
    language: currentLanguage,
    speed: parseFloat(dom.speedSlider.value),
    pitch: parseFloat(dom.pitchSlider.value),
    emotion: dom.emotionSelect.value,
    voice_design_prompt: dom.voiceDesignPrompt.value.trim(),
    reference_audio_id: selectedReferenceId,
  };

  try {
    const res = await fetch('/api/tts/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '합성 실패');
    }

    const data = await res.json();

    // Load generated audio directly into WaveSurfer
    if (wavesurfer) {
      wavesurfer.load(data.audio_url);
      wavesurfer.once('ready', () => {
        wavesurfer.play();
      });
    }

    // Enable WAV download button
    dom.btnDownloadWav.href = data.audio_url;
    dom.btnDownloadWav.download = data.filename;
    dom.btnDownloadWav.classList.remove('opacity-50', 'pointer-events-none');

    // Refresh history
    await loadHistory();
  } catch (err) {
    alert('음성 렌더링 오류: ' + err.message);
  } finally {
    dom.btnGenerate.disabled = false;
    dom.btnGenerate.classList.remove('opacity-70');
    dom.btnGenerateText.textContent = '음성 합성 렌더링 (Render Voice)';
  }
}

// ---------------------------------------------------------------------------
// 6. Voice Cloning & Audio Upload
// ---------------------------------------------------------------------------
async function handleReferenceUpload(file) {
  if (!file) return;
  dom.cloneUploadStatus.textContent = '업로드 중...';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/voice/clone/upload', {
      method: 'POST',
      body: formData,
    });
    const data = await res.json();

    if (res.ok) {
      selectedReferenceId = data.reference_id;
      dom.refFileName.textContent = data.original_name;
      dom.referencePreview.classList.remove('hidden');
      dom.dropZone.classList.add('hidden');
      dom.cloneUploadStatus.textContent = '복제 준비 완료';
    } else {
      alert('업로드 실패: ' + (data.detail || '알 수 없는 오류'));
      dom.cloneUploadStatus.textContent = '업로드 실패';
    }
  } catch (err) {
    alert('업로드 네트워크 오류: ' + err.message);
    dom.cloneUploadStatus.textContent = '오류';
  }
}

function removeReferenceAudio() {
  selectedReferenceId = null;
  dom.referencePreview.classList.add('hidden');
  dom.dropZone.classList.remove('hidden');
  dom.cloneUploadStatus.textContent = '준비됨';
  dom.referenceFileInput.value = '';
}

// ---------------------------------------------------------------------------
// 7. History Feed & Playback
// ---------------------------------------------------------------------------
async function loadHistory() {
  try {
    const res = await fetch('/api/history');
    const items = await res.json();

    dom.historyCount.textContent = `${items.length}개 생성됨`;
    if (!items || items.length === 0) {
      dom.historyList.innerHTML = '<p class="text-xs text-gray-600 text-center py-4">아직 생성된 음성이 없습니다.</p>';
      return;
    }

    dom.historyList.innerHTML = items
      .map(
        (item) => `
      <div class="history-card p-3 rounded-xl bg-gray-950/70 border border-gray-800/80 flex items-center justify-between gap-3 text-xs">
        <div class="overflow-hidden flex-1 cursor-pointer" onclick="playHistoryItem('${item.url}')">
          <p class="text-gray-200 font-medium truncate">${escapeHtml(item.text)}</p>
          <div class="flex items-center gap-2 text-[10px] text-gray-500 mt-1">
            <span>${item.timestamp}</span>
            <span>·</span>
            <span class="text-cyan-400 font-mono">${item.duration}초</span>
            <span>·</span>
            <span class="uppercase">${item.language}</span>
          </div>
        </div>
        <div class="flex items-center gap-1.5 shrink-0">
          <button class="p-1.5 rounded-lg bg-gray-800 hover:bg-cyan-600 text-gray-300 hover:text-white transition" onclick="playHistoryItem('${item.url}')" title="재생">
            <i data-lucide="play" class="w-3.5 h-3.5 fill-current"></i>
          </button>
          <a href="${item.url}" download="${item.filename}" class="p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 transition" title="다운로드">
            <i data-lucide="download" class="w-3.5 h-3.5"></i>
          </a>
          <button class="p-1.5 rounded-lg bg-gray-800 hover:bg-red-900/60 text-gray-400 hover:text-red-400 transition" onclick="deleteHistoryItem('${item.filename}')" title="삭제">
            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
          </button>
        </div>
      </div>
    `
      )
      .join('');

    initLucide();
  } catch (e) {
    console.error('History load error:', e);
  }
}

window.playHistoryItem = function (url) {
  if (wavesurfer) {
    wavesurfer.load(url);
    wavesurfer.once('ready', () => {
      wavesurfer.play();
    });
    dom.btnDownloadWav.href = url;
    dom.btnDownloadWav.classList.remove('opacity-50', 'pointer-events-none');
  }
};

window.deleteHistoryItem = async function (filename) {
  if (!confirm('이 음성을 삭제하시겠습니까?')) return;
  try {
    await fetch(`/api/history/${filename}`, { method: 'DELETE' });
    await loadHistory();
  } catch (e) {
    console.error('Delete error:', e);
  }
};

function escapeHtml(str) {
  return str.replace(/[&<>'"]/g, (tag) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag));
}

function formatTime(seconds) {
  if (isNaN(seconds)) return '00:00.0';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 10);
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${ms}`;
}

// ---------------------------------------------------------------------------
// 8. Event Listeners & Shortcuts
// ---------------------------------------------------------------------------
function initEventListeners() {
  // Modal toggles
  dom.btnOpenModelModal.addEventListener('click', () => {
    dom.modalModelWizard.classList.remove('hidden');
    initLucide();
  });

  dom.btnCloseModal.addEventListener('click', () => {
    dom.modalModelWizard.classList.add('hidden');
  });

  dom.btnStartDownload.addEventListener('click', startModelDownload);
  dom.btnCancelDownload.addEventListener('click', cancelDownload);

  // Studio Clean Shutdown
  if (dom.btnShutdown) {
    dom.btnShutdown.addEventListener('click', async () => {
      if (confirm('MingStudio AI 음성 작업실을 종료하시겠습니까?')) {
        try {
          await fetch('/api/shutdown', { method: 'POST' });
        } catch (e) {}
        document.body.innerHTML = `
          <div class="min-h-screen bg-[#0B0F19] text-gray-200 flex flex-col items-center justify-center p-6 text-center font-sans">
            <div class="w-16 h-16 rounded-2xl bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center mb-4 text-cyan-400">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
            </div>
            <h2 class="text-xl font-bold text-white mb-2">MingStudio가 안전하게 종료되었습니다</h2>
            <p class="text-sm text-gray-400 mb-6">백엔드 프로세스가 해제되었습니다. 이 창을 닫아주세요.</p>
            <button onclick="window.close()" class="px-5 py-2.5 rounded-xl bg-gray-800 hover:bg-gray-700 border border-gray-700 text-xs font-semibold text-gray-200 transition">창 닫기</button>
          </div>
        `;
        setTimeout(() => window.close(), 800);
      }
    });
  }

  // Textarea input & keyboard shortcuts
  dom.ttsTextInput.addEventListener('input', updateCharCount);
  dom.ttsTextInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
      e.preventDefault();
      generateSpeech();
    }
  });

  dom.btnGenerate.addEventListener('click', generateSpeech);

  // Sliders
  dom.speedSlider.addEventListener('input', (e) => {
    dom.speedVal.textContent = `${parseFloat(e.target.value).toFixed(2)}x`;
  });

  dom.pitchSlider.addEventListener('input', (e) => {
    const val = parseInt(e.target.value, 10);
    dom.pitchVal.textContent = `${val > 0 ? '+' : ''}${val} st`;
  });

  // WaveSurfer Player Buttons
  dom.btnPlayPause.addEventListener('click', () => {
    if (wavesurfer) wavesurfer.playPause();
  });

  dom.btnStop.addEventListener('click', () => {
    if (wavesurfer) {
      wavesurfer.stop();
      dom.btnPlayPause.innerHTML = '<i data-lucide="play" class="w-4 h-4 fill-current"></i>';
      initLucide();
    }
  });

  // Playback Rate
  document.querySelectorAll('.speed-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.speed-btn').forEach((b) => {
        b.classList.remove('bg-cyan-900/50', 'text-cyan-400', 'font-bold');
      });
      btn.classList.add('bg-cyan-900/50', 'text-cyan-400', 'font-bold');
      const rate = parseFloat(btn.dataset.playbackRate);
      if (wavesurfer) wavesurfer.setPlaybackRate(rate);
    });
  });

  // Spacebar Play/Pause
  window.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && e.target !== dom.ttsTextInput && e.target !== dom.voiceDesignPrompt) {
      e.preventDefault();
      if (wavesurfer) wavesurfer.playPause();
    }
  });

  // Voice Mode Tabs
  dom.tabVoiceDesign.addEventListener('click', () => {
    dom.tabVoiceDesign.className =
      'flex-1 py-2 text-xs font-semibold rounded-lg text-white bg-cyan-600/90 shadow transition flex items-center justify-center gap-1.5';
    dom.tabVoiceClone.className =
      'flex-1 py-2 text-xs font-semibold rounded-lg text-gray-400 hover:text-gray-200 transition flex items-center justify-center gap-1.5';
    dom.paneVoiceDesign.classList.remove('hidden');
    dom.paneVoiceClone.classList.add('hidden');
  });

  dom.tabVoiceClone.addEventListener('click', () => {
    dom.tabVoiceClone.className =
      'flex-1 py-2 text-xs font-semibold rounded-lg text-white bg-cyan-600/90 shadow transition flex items-center justify-center gap-1.5';
    dom.tabVoiceDesign.className =
      'flex-1 py-2 text-xs font-semibold rounded-lg text-gray-400 hover:text-gray-200 transition flex items-center justify-center gap-1.5';
    dom.paneVoiceClone.classList.remove('hidden');
    dom.paneVoiceDesign.classList.add('hidden');
  });

  // Voice Design Preset Chips
  document.querySelectorAll('.preset-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      dom.voiceDesignPrompt.value = chip.dataset.prompt;
    });
  });

  // File Upload DropZone
  dom.dropZone.addEventListener('click', () => dom.referenceFileInput.click());
  dom.referenceFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) handleReferenceUpload(e.target.files[0]);
  });

  dom.dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dom.dropZone.classList.add('border-cyan-500', 'bg-cyan-950/20');
  });

  dom.dropZone.addEventListener('dragleave', () => {
    dom.dropZone.classList.remove('border-cyan-500', 'bg-cyan-950/20');
  });

  dom.dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dom.dropZone.classList.remove('border-cyan-500', 'bg-cyan-950/20');
    if (e.dataTransfer.files.length > 0) handleReferenceUpload(e.dataTransfer.files[0]);
  });

  dom.btnRemoveRef.addEventListener('click', removeReferenceAudio);
}

# 🎙️ MingStudio (Ming-3.0 MoE AI Voice Workstation)

> **초경량 · 원클릭 · 유저 친화적 다국어 AI 음성 작업실 (Next-Gen Multilingual MoE AI Voice Workstation)**  
> Ant Group의 최신 Ling V3 기반 **Ming-3.0 MoE AI 음성 모델 (`inclusionAI/Ming-3.0-tts-tiny`)**을 누구나 가장 우아하고 결함 없이 활용할 수 있도록 완전히 새롭게 재설계된 클린 아키텍처 작업실입니다.

---

## ✨ 핵심 하이라이트 (Key Features)

### 1. 🏗️ 미니멀 클린 아키텍처 (Minimal Clean Architecture)
- **Rust EXE 및 복잡한 컴파일 의존성 100% 배제**: 순수 Python + 최적화 웹 프론트엔드로만 구성되어 고장 날 여지를 원천 차단.
- **단일 출처(Same-Origin) 직접 서빙**: FastAPI 백엔드가 프론트엔드를 동일 포트에서 직접 서빙하여 브라우저 CORS 정책 및 `Failed to fetch` 오류 원천 차단.

### 2. ⚡ 원클릭 유저 친화적 실행 (`Start.bat`)
- **스마트 포트 바인딩**: 기본 4100번 포트 충돌 시 사용 가능한 최적 포트를 스스로 감지하여 바인딩.
- **네이티브 앱 모드 (`--app`)**: 백엔드가 준비되면 Microsoft Edge를 앱 모드로 즉시 띄워 주소창/탭 없는 네이티브 데스크톱 앱 창 경험 제공.

### 3. 📦 지능형 모델 다운로드 & 0.1초 자동 스킵 (Auto-Skip)
- **지능형 사전 검사 (Auto-Skip)**: 실행 즉시 `data/models/Ming-3.0-tts-tiny/` 경로에 30개 분할 safetensors 가중치가 존재하는지 sub-millisecond 단위로 검사. 이미 다운로드되어 있다면 **마법사 창을 전혀 띄우지 않고 0.1초 만에 스킵**하여 즉시 `준비 완료(Ready)` 메인 스튜디오로 진입.
- **8스레드 인앱 다운로더**: 모델이 없을 때만 직관적인 모달 마법사가 나타나며, 공식 Hugging Face CDN으로 직접 연결하여 실시간 전송 속도(MB/s), 남은 시간(ETA), 실시간 진행률(%)을 시각적으로 표시하고 완료 즉시 준비 완료 상태로 전환.

### 4. 🎛️ 스튜디오 핵심 기능
- **다국어 7개국어 지원**: 한국어 🇰🇷, 중국어 🇨🇳, 영어 🇺🇸, 일본어 🇯🇵, 스페인어 🇪🇸, 프랑스어 🇫🇷, 독일어 🇩🇪
- **14종 파링귀스틱 감정 태그 원클릭 삽입**:
  - `[laugh]` 웃음, `[sigh]` 한숨, `[whisper]` 속삭임, `[angry]` 분노, `[gasp]` 숨들이쉼
  - `[cry]` 울음, `[cough]` 기침, `[clear-throat]` 목가다듬기, `[yawn]` 하품, `[pant]` 헐떡임
  - `[sneeze]` 재채기, `[chuckle]` 킬킬, `[snicker]` 낄낄, `[uhm]` 망설임
- **Zero-Shot 보이스 클로닝 & 프롬프트 보이스 디자인**:
  - 짧은 오디오(5~15초) 업로드 즉각 복제
  - 자연어 설명("차분하고 신뢰감 있는 30대 여성 아나운서") 기반 화자 디자인
- **실제 오디오 렌더링 파이프라인 & Wavesurfer 플레이어**:
  - 합성이 완료되면 `data/outputs/`에 실제 유효한 WAV 파일이 즉시 저장.
  - 고해상도 Wavesurfer 파형 시각화, 재생/일시정지, 배속 조절, 즉시 다운로드 지원.

---

## 📂 파일 구조 (Project Architecture)

```
MingStudio/
├── Start.bat                   # ⚡ 원클릭 실행 런처 (스마트 포트 + Edge App 모드)
├── requirements.txt            # 핵심 의존성 목록
├── README.md                   # 프로젝트 문서
├── .gitignore                  # 대용량 모델 및 캐시 차단 gitignore
│
├── backend/                    # 순수 Python 백엔드
│   ├── __init__.py
│   ├── config.py               # 모델 경로, 포트, 7개 언어, 14종 태그 상수
│   ├── model_manager.py        # 30개 분할 가중치 검사 및 GPU 하드웨어 텔레메트리
│   ├── downloader.py           # 8스레드 병렬 다운로더 (Hugging Face CDN + 이어받기)
│   ├── voice_engine.py         # Ming-3.0 MoE 합성 및 고음질 오디오 파이프라인
│   └── server.py               # FastAPI 서버 (Same-Origin 정적 서빙 및 REST/SSE API)
│
├── frontend/                   # 모던 다크 글래스모피즘 스튜디오 UI
│   ├── index.html              # 메인 스튜디오 대시보드 및 Wavesurfer 플레이어
│   ├── style.css               # 사이버펑크/스튜디오 스타일시트
│   └── app.js                  # 프론트엔드 상태 머신 및 실시간 텔레메트리
│
└── data/                       # 로컬 데이터 (gitignore 제외)
    ├── models/                 # Ming-3.0-tts-tiny (30개 safetensors)
    ├── outputs/                # 생성된 음성 파일 (WAV) 및 history.json
    └── references/             # 보이스 클로닝 참조 음성 파일
```

---

## 🚀 빠른 시작 (Quick Start)

### 1. 저장소 복제 (Clone)
```bash
git clone https://github.com/hoperkim/MingStudio.git
cd MingStudio
```

### 2. 패키지 의존성 설치 (Install Dependencies)
```bash
# 가상환경 사용 권장 (선택사항)
python -m venv venv
venv\Scripts\activate

# 핵심 패키지 설치
pip install -r requirements.txt
```
> [!NOTE]
> PyTorch CUDA(GPU) 환경이 아직 구성되지 않은 경우:
> ```bash
> pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
> ```

### 3. 스튜디오 실행 (Launch Studio)
가장 간편하게 `Start.bat`을 더블 클릭하면 파이썬 엔진을 자동 감지하고 마이크로소프트 엣지 앱(App) 모드로 스튜디오가 실행됩니다:
```bash
Start.bat
```
또는 터미널에서 직접 실행:
```bash
python backend/server.py --launch-browser
```

### 4. 모델 다운로드 (최초 1회)
* 최초 실행 시 모델 가중치가 없으면 **원클릭 인앱 다운로더 마법사**가 팝업됩니다.
* **[원클릭 모델 다운로드]** 버튼을 누르면 8스레드 고속 병렬 스트리밍으로 가중치(30개 safetensors)가 다운로드됩니다.
* 가중치가 이미 존재하는 경우 **0.1초 만에 마법사를 자동 스킵(Auto-Skip)**하여 즉시 메인 스튜디오로 진입합니다.

---

## 💻 권장 사양 (Hardware Telemetry)

- **GPU**: NVIDIA RTX 3070 / 4070 / 4080 (VRAM 12GB ~ 16GB 권장)
- **CUDA**: 12.0 ~ 13.1 지원
- **Python**: Python 3.10.x 권장
- **저장 공간**: 모델 분할 가중치 30개 보관을 위한 여유 공간 약 20GB

---

## 🌐 깃 저장소 배포 (GitHub Push)

기존의 무거운 구버전 커밋 및 의존성을 배제하고 클린 아키텍처로 원격 저장소를 갱신합니다:
```bash
git push -u origin main --force
```

---

## 📜 라이선스 (License)

본 프로젝트는 [MIT License](LICENSE)를 따릅니다.  
Ming-3.0 가중치 및 라이선스 정책은 Ant Group [inclusionAI/Ming-3.0-tts](https://github.com/inclusionAI/Ming-3.0-tts)의 오픈소스 라이선스를 준수합니다.

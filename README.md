# 🎙️ MingStudio — Universal AI Voice Workstation

<div align="center">
  <p><strong>Next-Gen Open-Source AI Voice Workstation powered by Ming-3.0 MoE (7.9B) — Zero-Shot Voice Cloning, Prompt Voice Design, 14 Paralinguistic Emotion Tags, Multi-Speaker Studio & Video Dubbing in Korean, Chinese, English & Japanese.</strong></p>
  <p><em>100% Local · Zero-Pollution Portable · High-Performance CUDA Acceleration</em></p>
  <p>
    <a href="#features">Key Features</a> ·
    <a href="#languages">Languages</a> ·
    <a href="#quick-start">Quick Start</a> ·
    <a href="#architecture">Architecture</a> ·
    <a href="#license">License</a>
  </p>
</div>

---

## 🌟 주요 특징 (Key Features)

### 1. 🌐 완벽한 다국어 선택 지원 (Multilingual)
- **한국어 (Korean 🇰🇷)**: 자연스러운 억양과 지적인 다큐멘터리/나레이션 톤
- **중국어 (Chinese 🇨🇳)**: 표준 보통화 및 15개 방언 지원
- **영어 (English 🇺🇸)**: 북미 스튜디오 아나운서 및 캐릭터 보이스
- **일본어 (Japanese 🇯🇵)**: 애니메이션/오디오북 특화 고선명 발화
- **유럽 언어 (Spanish 🇪🇸, French 🇫🇷, German 🇩🇪)**

### 2. 🎭 14종 파링귀스틱 감정 & 호흡 태그 (원클릭 인라인 삽입)
대본 작성 중 버튼 클릭 한 번으로 미세한 감정과 비언어적 소리를 자연스럽게 녹여냅니다:
- `[laugh]` (웃음) · `[chuckle]` (키득) · `[sigh]` (한숨) · `[gasp]` (놀람)
- `[whisper]` (속삭임) · `[cough]` (기침) · `[clear throat]` (목가다듬기)
- `[groan]` (신음) · `[crying]` (울먹임) · `[shush]` (쉿) · `[sniff]` (훌쩍임)
- `[angry]` (분노) · `[happy]` (행복) · `[fear]` (공포)

### 3. 🧬 Zero-Shot 보이스 클로닝 & 텍스트 보이스 디자인
- **5초 즉시 복제**: 짧은 오디오 샘플 하나로 모든 언어를 말하는 내 목소리 라이브러리 생성
- **Prompt Voice Design**: "20대 후반, 차분하고 서늘한 긴장감의 한국어 여성 나레이터" 등 자연어 설명만으로 세상에 없던 새로운 목소리 창조

### 4. 👥 멀티 스피커 스튜디오 (Multi-Speaker Studio)
- 팟캐스트, 연극, 인터뷰 등 등장인물(화자 A, 화자 B, 화자 C)별로 목소리와 언어를 각각 배정하여 장문 대본을 일괄 연속 렌더링

### 5. 🎬 영상 더빙 & 타임라인 싱크 스튜디오
- 쇼츠/릴스/유튜브 영상(`mp4`)을 로드하여 자막 타이밍 시트에 음성을 오차 없이 배치
- 배경음(BGM) 볼륨을 자동으로 낮춰주는 **스마트 오디오 덕킹(Audio Ducking)** 내장

---

## 🚀 빠른 시작 (Quick Start)

### 윈도우 원클릭 포터블 실행
1. [Releases](https://github.com/hoperkim/MingStudio/releases)에서 `MingStudio-Portable-Windows-x64.zip` 다운로드
2. 원하는 폴더에 압축 해제
3. **`Start.bat`** (또는 `MingStudio.exe`) 더블 클릭!

> 💡 별도의 Python, Git, C++ 컴파일러 설치가 전혀 필요 없는 **완전 무설치(Zero-Pollution) 포터블 에디션**입니다.

---

## 💻 권장 사양

| 하드웨어 | 최소 사양 | 권장 사양 |
| :--- | :--- | :--- |
| **GPU** | NVIDIA GTX 1060 (6GB) | **NVIDIA RTX 4070 / 4080 (12~16GB VRAM)** |
| **RAM** | 16 GB | **32 GB 이상** |
| **OS** | Windows 10 / 11 (64-bit) | Windows 11 (64-bit) |

---

## 📄 License
MIT License © 2026 hoperkim. All rights reserved.
Model weights licensed under inclusionAI / Ant Group open-weights license.

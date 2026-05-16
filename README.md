# yt-harvest

유튜브 영상의 대본·댓글·답글·메타 정보를 한 번에 긁어오는 도구.

## 모드 (URL만 보고 자동 감지)

| URL | 동작 |
|---|---|
| `youtube.com/watch?v=...` | 영상 1개 |
| `youtube.com/@xxx` / `/channel/UCxxx` | 채널의 일반 영상 전부 |
| `youtube.com/@xxx/shorts` / `/shorts/...` | 쇼츠 전부 |
| `youtube.com/playlist?list=...` | 재생목록 전부 |

## 받는 것

- 영상 메타 (제목/조회수/좋아요/설명/태그/챕터 등)
- 한국어 자막 (사람 단 ko / 자동 ko-orig 둘 다 시도)
- 댓글 전체 + 답글 전체 (좋아요/시간/작성자 포함)
- 채널 정보 (구독자 수 등)

## 출력 폴더 구조

```
yt-harvest-output/
  <채널명>_<날짜>_<시각>/
    _index.md
    _stats.csv
    channel.json
    <영상ID>/
      meta.json
      transcript.txt
      transcript_source.txt
      comments.csv
      comments.json
      thumbnail.jpg
```

## 개발 환경

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m src.main --help
```

## 윈도우 처음 실행 시

Windows SmartScreen 경고가 뜸. **추가 정보** → **실행** 한 번만 누르면 됨.

## 빌드

```bash
# Windows에서
pyinstaller YtHarvest.spec --clean
gh release create vX.Y.Z dist/YtHarvest.exe --repo YeoHoYeon/yt-harvest
```

# 📚 Librario

> 시놀로지 NAS 에서 돌아가는 **개인 만화·웹툰·전자책 서버** + 안드로이드 PWA 리더
> (Komga / Kavita 같은 자가호스팅 라이브러리 서버를 Python·FastAPI 로 가볍게 재구성)

지원 포맷: `CBZ / ZIP / PDF / EPUB / TXT`
스택: **FastAPI + SQLite(WAL) + 순수 JS PWA** (빌드 도구 불필요) · 단일 Docker 이미지

---

## ✨ 기능

**기본**
- 폴더 = 시리즈, 파일 = 책. 상위 폴더는 **자동 태그**, `ComicInfo.xml` 메타데이터 병합.
- 만화 뷰어(페이지 단위 스트리밍), PDF·EPUB(단말기에서 렌더), TXT(서버 디코딩).
- 별점·읽기 진행률·이어보기, 사용자별 권한, **제한(성인/R17) 라이브러리**는 관리자·허용 사용자만 노출.
- 안드로이드 "홈 화면에 추가" 로 앱처럼 사용(PWA + 서비스워커 오프라인 셸).

**이번 버전(1.1) 신규**
- 🗑 **휴지통** — 파일이 삭제/이동되면 DB 에서 지우지 않고 휴지통으로. 별점·태그·진행률 **보존**, 파일이 돌아오면 스캔 시 **자동 복구**. 영구 삭제는 수동으로만.
- ⏱ **예약 스캔** — 변경/신규 파일만 처리하는 **빠른 스캔**(N시간마다) + 모든 파일 메타·표지를 다시 읽는 **심층 스캔**(N일마다, 지정 시각).
- 📈 **분석 대시보드** — 라이브러리/형식/태그별 통계, 용량, 최근 추가, 내 완독 수 등.
- 🔎 **외부 메타데이터 가져오기** — Google Books · Open Library · AniList 에서 표지·줄거리·작가·태그를 검색해 적용.
- 🔁 **메타데이터 새로고침** — 파일 하나/시리즈 단위로 다시 파싱.
- 🏷 **파일명 태그 규칙** — `ComicInfo.xml` 이 없어도 파일명의 `[대괄호]`·키워드·정규식으로 태그 추출.
- 🔐 **로그인 유지(자동 로그인)** — 로그인 화면 체크박스.

---

## 0. 준비물

- 시놀로지 NAS (예: **DS423+**) · DSM 7.x
- **Container Manager**(구 Docker 패키지)
- **Portainer**(컨테이너로 설치) — 이 문서는 Portainer 로 배포합니다.
- 외부 접속을 원하면: **DDNS 도메인 + Let's Encrypt 인증서**(둘 다 DSM 에서 무료 발급)
- (개발용) 본인 PC/맥에 **Git** 과 **Python 3.12**

> 이 프로젝트를 먼저 **본인 GitHub 저장소**에 올려두세요(Public 또는 Private). Portainer 가 그 주소에서 코드를 받아 이미지를 빌드합니다.

---

## 1. GitHub 에 올리기

개발 PC 에서:

```bash
git clone <이-저장소를-내-계정으로-fork/복사한-주소>   # 또는 아래처럼 새로 시작
cd librario

git init
git add .
git commit -m "Librario 최초 커밋"
git branch -M main
git remote add origin https://github.com/<your-id>/librario.git
git push -u origin main
```

> `.gitignore` 가 `data/`, `*.db`, `secret.key`, `.venv/` 를 제외하므로 **런타임 데이터·시크릿은 커밋되지 않습니다.**

---

## 2. Portainer 로 컨테이너 만들기 (GitHub 주소로 빌드)

1. Portainer 접속 → 왼쪽 **Stacks** → **+ Add stack**.
2. 이름: `librario`.
3. **Build method → Repository** 선택.
   - **Repository URL**: `https://github.com/<your-id>/librario`
   - **Repository reference**: `refs/heads/main`
   - **Compose path**: `docker-compose.yml`
   - Private 저장소면 **Authentication** 토글 후 GitHub 토큰 입력.
4. (권장) **GitOps updates** 토글 ON — 자동 업데이트. (→ 4장 참고)
5. 필요하면 **Environment variables** 에서 `SECRET_KEY` 등을 지정(또는 compose 기본값 사용).
6. **Deploy the stack** 클릭.

Portainer 가 저장소를 받아 `Dockerfile` 로 이미지를 빌드하고 컨테이너를 실행합니다.
첫 빌드는 의존성 설치로 몇 분 걸릴 수 있습니다.

### 배포 전에 꼭 수정할 것 — `docker-compose.yml`
경로

COMIC_PATH = 
NOVEL_PATH = 
BOOK_PATH  = 

- **`SECRET_KEY`**: 길고 무작위한 값으로 교체(로그인 토큰 서명 키, 한 번 정하면 유지).
- **`volumes`**: `왼쪽=시놀로지 실제 경로`, `오른쪽=컨테이너 내부 경로`. 본인 폴더 구조에 맞게.
- **`SEED_LIBRARIES`**: 위 `볼륨의 컨테이너 내부 경로`와 **정확히 일치**시켜야 최초 자동 등록됩니다.
- **`ports`**: `"8580:8080"` — 왼쪽(호스트 8580)이 이미 쓰이면 다른 값으로.
- **`COOKIE_SECURE`**: 처음 `http://NAS내부IP:8580` 로 테스트할 땐 `"false"`.
  역방향 프록시(HTTPS)로만 접속할 거면 `"true"` 로 바꾸세요(→ 5장).

---

## 3. 최초 실행 & 설정

1. 브라우저에서 `http://<NAS-IP>:8580` 접속 → **첫 관리자 계정** 생성.
2. **관리 → 라이브러리** 에서 `SEED_LIBRARIES` 로 등록된 라이브러리 확인.
   - 없으면 **+ 라이브러리 추가**(경로는 컨테이너 내부 경로 `/books/...`).
3. **성인/R17 라이브러리**: 해당 라이브러리 **수정 → 제한 켜기**. 이제 관리자·허용 사용자만 보입니다.
4. **관리 → 사용자** 에서 가족/지인 계정 추가, 제한 라이브러리 접근 허용 여부 선택.
5. **스캔** 또는 **전체 스캔** 실행. 파일이 많으면 백그라운드로 진행되며 상단에 진행률이 뜹니다.

---

## 4. 코드 수정 → 자동 업데이트 (GitOps) ✅

> **결론부터**: GitHub 에 push 만 한다고 자동으로 바뀌지 **않습니다.** Portainer 에서
> **GitOps updates(자동 업데이트)** 를 켜 두어야 push → 재배포가 자동으로 일어납니다.
> 이 기능은 **일반 Docker 스택에서 Portainer 무료(CE) 버전으로도 사용 가능**합니다.
> (참고: "Business 전용" 제약은 *Edge Stack* 에 한정됩니다.)

동작 방식(둘 중 택1):

| 방식 | 설명 | 언제 |
| --- | --- | --- |
| **Polling(폴링)** | Portainer 가 저장소를 주기적으로(예: 5분) 확인, 새 커밋이 있으면 재배포 | 방화벽 뒤 등 어디서나 무난. **추천** |
| **Webhook** | GitHub push 시 Portainer 로 즉시 신호 → 거의 실시간 재배포 | 외부에서 Portainer 에 접근 가능할 때 |

설정: **Stacks → librario → GitOps updates**
- **Polling** 선택 후 **Fetch interval**(예: `5m`) 저장, 또는
- **Webhook** 선택 → 생성된 URL 을 GitHub 저장소 **Settings → Webhooks** 에 등록.

동작 흐름:
```
개발 PC 에서 코드 수정 → git push → (Polling/Webhook) → Portainer 가 새 커밋 감지
   → 저장소 다시 받기 → Dockerfile 로 이미지 재빌드 → 컨테이너 교체
```
- 이 스택은 `build:` 를 쓰므로 재배포 시 **이미지를 새로 빌드**합니다(레지스트리 불필요).
- 변경이 반영되지 않는 것 같으면 GitOps 설정의 **Force redeployment**(변경 없어도 강제 재배포) 를 켜거나, Portainer 에서 스택을 한 번 **Pull and redeploy** 하세요.
- 서비스워커 캐시 때문에 브라우저에 옛 화면이 보이면, 새로고침하면 새 버전이 적용됩니다(캐시 이름을 버전마다 올리도록 되어 있습니다).

> **데이터는 안전**: 업데이트는 코드/이미지만 교체합니다. DB·썸네일은 `librario-data` 볼륨(`/data`)에 남아 그대로 유지됩니다.

---

## 5. 시놀로지 역방향 프록시로 외부 접속

목표: `https://librario.내도메인.com` → 컨테이너(`localhost:8580`).

1. **DSM → 제어판 → 외부 액세스 → DDNS** 로 도메인 확보(예: `xxx.synology.me`) 또는 본인 도메인 연결.
2. **제어판 → 보안 → 인증서** 에서 그 도메인으로 **Let's Encrypt 인증서** 발급.
3. **제어판 → 로그인 포털 → 고급 → 역방향 프록시 → 생성**:
   - **소스**: 프로토콜 `HTTPS`, 호스트 `librario.내도메인.com`, 포트 `443`
   - **대상**: 프로토콜 `HTTP`, 호스트 `localhost`, 포트 `8580`
4. 방금 만든 규칙에 3번의 인증서를 연결(제어판 → 보안 → 인증서 → 설정).
5. 공유기/방화벽에서 **443 포트 포워딩**(외부에서 접속하려면).
6. **`docker-compose.yml` 에서 `COOKIE_SECURE: "true"` 로 변경 후 재배포.**
   - HTTPS 로만 접속하니 보안 쿠키를 켜는 게 맞습니다.
   - ⚠️ 반대로 `http://IP:포트` 직접 접속을 계속 쓸 거면 `false` 유지(true 면 로그인이 유지되지 않음).

이제 외부 어디서든 `https://librario.내도메인.com` 으로 접속, 안드로이드에서 **홈 화면에 추가**하면 앱처럼 씁니다.

> 포트 매핑 요약: `역방향 프록시(443) → 호스트포트(8580) → 컨테이너(8080)`.

---

## 6. 개발 환경 (앱·프로젝트 업데이트용) 🛠

코드를 고쳐 위 자동 배포로 흘려보내는 전체 순서입니다.

**① 한 번만: 로컬 환경 준비**
```bash
# Python 3.12 와 git 이 설치돼 있어야 합니다.
git clone https://github.com/<your-id>/librario.git
cd librario

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

**② 로컬에서 실행해 확인**
```bash
# 데이터는 로컬 ./data 에 저장(서버 데이터와 분리), 로컬은 http 이므로 쿠키 보안 끔
export DATA_DIR="$(pwd)/data"
export COOKIE_SECURE=false
export SCAN_ON_STARTUP=false
cd backend
uvicorn app.main:app --reload --port 8080
# 브라우저: http://localhost:8080  (테스트용 라이브러리 경로를 UI 에서 추가)
```

**③ 코드 수정 → 테스트**
```bash
# 백엔드 자동 테스트(선택)
cd /path/to/librario
.venv/bin/python smoke_test.py           # 기본 기능 41개
.venv/bin/python test_new_features.py     # 신규 기능(휴지통·태그·분석 등)
```
- 프론트엔드는 빌드가 없으므로 `frontend/` 파일을 고치고 브라우저 새로고침이면 끝.

**④ 반영: 커밋 & 푸시**
```bash
git add .
git commit -m "설명"
git push
```

**⑤ 자동 배포**
- 4장에서 GitOps 를 켰다면 → Portainer 가 감지해 **자동 재빌드·재배포**.
- 안 켰다면 → Portainer **Stacks → librario → Pull and redeploy** 수동 클릭.

> 요약 루프: `수정 → 로컬 테스트 → git push → (GitOps) 자동 배포`.

---

## 7. 태그 자동화 (기존 komga_xml.py 흐름 + 신규 규칙)

- **폴더 기반**: 상위 폴더명이 태그로, 바로 위 폴더는 시리즈명으로 자동 정리됩니다.
- **ComicInfo.xml**: 있으면 제목/작가/출판사/언어/장르(태그)를 병합합니다.
  기존에 쓰던 `komga_xml.py` 같은 태그 주입 스크립트로 파일 옆에 XML 을 만들어 두면 그대로 인식합니다.
- **파일명 태그 규칙(신규)**: XML 이 없어도 파일명에서 뽑습니다. **관리 → 예약·규칙** 에서:
  - `[대괄호]` 안 내용을 태그로(숫자·권/화 표기는 제외).
  - **키워드**(형식 `파일명포함어=태그`): 예 `완결=완결`, `BL=BL`.
  - **정규식**(형식 `패턴 => 태그` 또는 `패턴 => group:1`): 예 `\d+-\d+화 => 연재분`.
  - 규칙을 바꾼 뒤에는 **심층 스캔**(또는 개별 **메타 새로고침**)을 해야 반영됩니다.

수동으로 추가한 태그는 재스캔해도 **사라지지 않습니다.**

---

## 8. 환경 변수 요약

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `SECRET_KEY` | 자동생성 | 로그인 토큰 서명 키. **직접 지정 권장**(고정값 유지) |
| `DATA_DIR` | `/data` | DB·썸네일·시크릿 저장 위치(영구 볼륨) |
| `COOKIE_SECURE` | `false` | HTTPS(역방향 프록시) 전용 접속이면 `true` |
| `TZ` | (미설정) | 예약 심층 스캔 시각 기준 시간대. 예 `Asia/Seoul` |
| `SCAN_ON_STARTUP` | `true` | 컨테이너 시작 시 전체 스캔 |
| `SCHEDULER_ENABLED` | `true` | 예약 스캔 스케줄러 사용 |
| `SEED_LIBRARIES` | (없음) | 최초 1회 라이브러리 등록. `이름::/경로;이름2::/경로2` |
| `METADATA_ENABLED` | `true` | 외부 메타데이터 기능 사용 |
| `FILENAME_TAGS` | `true` | 파일명 태그 추출 사용 |

---

## 9. 용량·성능 (수백 GB / 수만 파일)

문제없이 처리하도록 설계돼 있습니다.
- 파일을 **통째로 메모리에 올리지 않고** 스트리밍/부분요청(Range)/페이지 단위 추출로 서빙.
- SQLite 는 수백만 행도 무리 없이 처리.
- **변경분만 처리하는 스캔**(수정시각 비교) 덕에 평소 재스캔이 빠릅니다. TXT 는 매우 가벼움.

권장:
- **최초 전체 스캔 + 썸네일 생성**은 파일 수만 개면 시간이 걸립니다(백그라운드 진행).
- DS423+ 는 **RAM 6GB 로 증설** 권장, 가능하면 `/data`(DB·썸네일)를 **SSD** 에 두면 쾌적합니다.
- 예약: **빠른 스캔**을 자주(예: 6시간), **심층 스캔**을 드물게(예: 주 1회 새벽)로 나눠 두세요.

---

## 10. 오프라인/CDN 참고

PDF·EPUB 뷰어는 `pdf.js`·`epub.js`·`jszip` 를 **jsDelivr CDN** 에서 불러옵니다.
- **보는 기기(휴대폰/PC)에 인터넷이 있으면 그대로 동작**합니다(대부분의 외부 접속 시나리오).
- 완전 오프라인/폐쇄망에서만 쓰려면, 해당 라이브러리를 `frontend/assets/vendor/` 에 직접 넣고
  `frontend/assets/app.js` 의 CDN URL 을 로컬 경로로 바꿔 self-host 하세요.

---

## 11. 문제 해결

- **로그인이 유지되지 않아요** → 접속 방식과 `COOKIE_SECURE` 불일치. `http://IP` 접속이면 `false`, `https://도메인` 접속이면 `true`.
- **라이브러리가 비어 있어요** → `volumes` 의 컨테이너 경로와 `SEED_LIBRARIES` 경로가 다르거나, 실제 NAS 경로 오타. 스캔 상태의 오류 메시지 확인.
- **성인 폴더가 일반 사용자에게 보여요** → 라이브러리 **수정 → 제한** 켜기.
- **업데이트가 반영 안 돼요** → 4장의 GitOps **Force redeployment** 켜기 또는 수동 **Pull and redeploy**, 그리고 브라우저 새로고침.
- **표지가 안 나오는 EPUB** → 개별 책에서 **메타 새로고침**, 또는 **메타데이터 찾기**로 표지 교체.

---

## 12. 앞으로 (네이티브 앱)

현재는 안드로이드에서 **PWA(홈 화면에 추가)** 로 앱처럼 사용합니다.
차후 동일 API 를 그대로 사용하는 네이티브 안드로이드 앱(오프라인 다운로드·푸시 등)으로 확장할 수 있습니다.

---

**라이선스**: MIT (LICENSE 참고)

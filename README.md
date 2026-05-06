# Weather App Deployment Project

Flask 기반 날씨 조회 웹 애플리케이션을 `Docker`, `Docker Compose`, `Kubernetes`, `Helm`으로 실행하고 배포하는 예제 프로젝트입니다.  
앱은 `wttr.in` API를 호출해 현재 날씨, 시간대별 예보, 5일 예보를 보여주며 기본 도시와 언어를 환경 변수로 제어할 수 있습니다.

## 1. 프로젝트 개요

이 프로젝트는 다음 흐름을 한 저장소에 담고 있습니다.

- Python Flask 애플리케이션 구현
- Docker 이미지 빌드
- Nginx를 통한 리버스 프록시 구성
- Docker Compose 기반 로컬 컨테이너 실행
- Kubernetes 매니페스트 기반 배포
- Helm Chart 기반 환경별 배포
- GitHub Actions를 이용한 이미지 테스트 및 푸시 자동화

## 2. 주요 기능

- 도시 이름 기반 날씨 조회
- 한국어/영어 전환
- 현재 온도, 체감 온도, 습도, 풍속 표시
- 일출/일몰 정보 표시
- 시간대별 예보 표시
- 5일 예보 표시
- 즐겨찾기 도시 추가/삭제
- `/health` 헬스체크 엔드포인트 제공

## 3. 기술 스택

- Backend: Python 3.12, Flask
- Weather API: `wttr.in`
- Container: Docker
- Reverse Proxy: Nginx
- Orchestration: Kubernetes
- Package Manager for K8s: Helm
- CI/CD: GitHub Actions

## 4. 디렉터리 구조

```text
.
├─ weather.py                    # Flask 애플리케이션
├─ Dockerfile                    # 앱 이미지 빌드 정의
├─ docker-compose.yml            # Flask + Nginx 로컬 실행
├─ nginx.conf                    # Nginx 리버스 프록시 설정
├─ setup.sh                      # 클러스터 부가 구성 스크립트
├─ test_basic.py                 # 기본 테스트
├─ k8s/
│  ├─ flask-deployment.yaml      # Deployment
│  ├─ flask-service.yaml         # Service
│  ├─ flask-hpa.yaml             # HPA
│  ├─ ingress.yaml               # Ingress
│  ├─ weather-configmap.yaml     # ConfigMap
│  └─ weather-secret.yaml        # Secret
├─ weather-chart/
│  ├─ Chart.yaml                 # Helm Chart 메타데이터
│  ├─ values.yaml                # 기본 값
│  ├─ values.dev.yaml            # 개발 환경 값
│  ├─ values.prod.yaml           # 운영 환경 값
│  └─ templates/                 # Helm 템플릿
└─ .github/workflows/
   ├─ docker-publish.yml         # develop 브랜치 CI/CD
   └─ docker-deploy.yml          # main 브랜치 이미지 배포용 워크플로
```

## 5. 애플리케이션 구성

### 5.1 요청 처리 흐름

1. 사용자가 브라우저에서 `/`로 접속합니다.
2. Flask 앱이 `city`, `lang`, `favs` 쿼리스트링을 읽습니다.
3. 서버가 `WTTR_BASE_URL` 환경 변수를 기준으로 `wttr.in`에 날씨 데이터를 요청합니다.
4. 응답 JSON을 가공해 현재 날씨, 시간대별 예보, 5일 예보, 일출/일몰 정보를 화면에 렌더링합니다.
5. `/health` 엔드포인트는 배포 환경에서 liveness/readiness probe로 사용됩니다.

### 5.2 실행 구성

- Flask 앱은 기본적으로 `0.0.0.0:8000`에서 실행됩니다.
- Docker Compose에서는 Nginx가 `8080` 포트로 외부 요청을 받고 Flask 컨테이너 `8000` 포트로 프록시합니다.
- Kubernetes에서는 `Service`가 Flask Pod의 `8000` 포트를 노출하고 `Ingress`가 외부 진입점을 제공합니다.

## 6. 환경 변수

앱에서 사용하는 주요 환경 변수는 아래와 같습니다.

| 변수명 | 설명 | 기본값 |
|---|---|---|
| `APP_PORT` | Flask 실행 포트 | `8000` |
| `DEFAULT_CITY` | 최초 조회 도시 | `Seoul` |
| `DEFAULT_LANG` | 기본 언어 (`ko`, `en`) | `ko` |
| `WTTR_BASE_URL` | 날씨 API 베이스 URL | `https://wttr.in` |

Kubernetes에서는 다음 리소스로 주입됩니다.

- `ConfigMap`: `DEFAULT_CITY`, `DEFAULT_LANG`, `APP_PORT`
- `Secret`: `WTTR_BASE_URL`

## 7. 로컬 실행 방법

### 7.1 Python으로 직접 실행

필수 조건:

- Python 3.11 이상 권장

실행 예시:

```bash
pip install flask
python weather.py
```

접속:

- `http://localhost:8000`

환경 변수를 지정해서 실행할 수도 있습니다.

```bash
APP_PORT=8000 DEFAULT_CITY=Seoul DEFAULT_LANG=ko python weather.py
```

Windows PowerShell 예시:

```powershell
$env:APP_PORT="8000"
$env:DEFAULT_CITY="Seoul"
$env:DEFAULT_LANG="ko"
python weather.py
```

### 7.2 Docker로 실행

이미지 빌드:

```bash
docker build -t weather-app .
```

컨테이너 실행:

```bash
docker run -p 8000:8000 \
  -e APP_PORT=8000 \
  -e DEFAULT_CITY=Seoul \
  -e DEFAULT_LANG=ko \
  -e WTTR_BASE_URL=https://wttr.in \
  weather-app
```

접속:

- `http://localhost:8000`

### 7.3 Docker Compose로 실행

이 프로젝트의 `docker-compose.yml`은 다음 구조로 동작합니다.

- `flask`: `onexy91/dev-docker-flask:develop` 이미지 실행
- `nginx`: `8080` 포트를 외부에 노출하고 Flask로 프록시

실행:

```bash
docker compose up -d
```

로그 확인:

```bash
docker compose logs -f
```

중지:

```bash
docker compose down
```

접속:

- `http://localhost:8080`

## 8. Docker 이미지 구성

`Dockerfile`은 매우 단순한 구조입니다.

1. `python:3.12-slim` 기반 이미지 사용
2. 작업 디렉터리를 `/app`으로 설정
3. `Flask` 설치
4. `weather.py` 복사
5. `python weather.py` 실행

즉, 애플리케이션 코드는 단일 파일 기반으로 컨테이너화되어 있습니다.

## 9. Kubernetes 배포 방법

### 9.1 배포 리소스 설명

`k8s/` 디렉터리에는 다음 리소스가 있습니다.

- `weather-configmap.yaml`: 기본 도시, 언어, 앱 포트 설정
- `weather-secret.yaml`: 외부 날씨 API URL 저장
- `flask-deployment.yaml`: Flask 앱 2개 replica 실행
- `flask-service.yaml`: ClusterIP 서비스 생성
- `flask-hpa.yaml`: CPU/메모리 기준 오토스케일링
- `ingress.yaml`: `weather.local` 호스트 기반 진입점 구성

### 9.2 기본 배포 순서

```bash
kubectl apply -f k8s/weather-configmap.yaml
kubectl apply -f k8s/weather-secret.yaml
kubectl apply -f k8s/flask-deployment.yaml
kubectl apply -f k8s/flask-service.yaml
kubectl apply -f k8s/flask-hpa.yaml
kubectl apply -f k8s/ingress.yaml
```

배포 확인:

```bash
kubectl get pods
kubectl get svc
kubectl get ingress
kubectl get hpa
```

롤아웃 상태 확인:

```bash
kubectl rollout status deployment/flask
```

### 9.3 Ingress 접속

현재 Ingress 설정은 아래 호스트를 사용합니다.

- `weather.local`

로컬 테스트 시 hosts 파일에 아래 내용을 추가해야 할 수 있습니다.

```text
127.0.0.1 weather.local
```

Ingress Controller가 설치되어 있어야 정상 동작합니다.

## 10. Helm 배포 방법

### 10.1 Chart 구성

`weather-chart/`는 Kubernetes 리소스를 템플릿화한 Helm Chart입니다.

- 기본 설정: `values.yaml`
- 개발 환경 설정: `values.dev.yaml`
- 운영 환경 설정: `values.prod.yaml`

주요 설정 항목:

- 이미지 저장소/태그
- replica 수
- Ingress 호스트
- HPA 최소/최대 수량
- CPU/메모리 리소스
- 기본 도시/언어
- 외부 API URL

### 10.2 개발 환경 배포

```bash
helm install weather ./weather-chart -f weather-chart/values.dev.yaml
```

업그레이드:

```bash
helm upgrade weather ./weather-chart -f weather-chart/values.dev.yaml
```

### 10.3 운영 환경 배포

```bash
helm install weather ./weather-chart -f weather-chart/values.prod.yaml
```

또는 이미 배포되어 있다면:

```bash
helm upgrade weather ./weather-chart -f weather-chart/values.prod.yaml
```

배포 결과 확인:

```bash
helm list
kubectl get all
kubectl get ingress
kubectl get hpa
```

## 11. 부가 인프라 설치 스크립트

`setup.sh`에는 Kubernetes 운영에 필요한 부가 구성 예시가 들어 있습니다.

- NGINX Ingress Controller 설치
- Metrics Server 설치
- ArgoCD 설치
- Prometheus + Grafana 설치
- Helm Chart 배포 예시

예시:

```bash
bash setup.sh
```

주의:

- 스크립트는 클러스터에 실제 리소스를 생성합니다.
- ArgoCD, Prometheus Stack까지 설치하므로 학습용/개발용 클러스터에서 먼저 검증하는 것을 권장합니다.

## 12. GitHub Actions CI/CD

### 12.1 develop 브랜치

`.github/workflows/docker-publish.yml`

- `develop` 브랜치에 push 시 실행
- `weather.py` 문법 검사
- `pytest` 실행
- Docker Hub 로그인
- 이미지 빌드 및 푸시
- 태그:
  - `develop`
  - `${github.sha}`

### 12.2 main 브랜치

`.github/workflows/docker-deploy.yml`

- `main` 브랜치에 push 시 실행
- Docker 이미지 빌드 및 푸시
- 태그:
  - `latest`
  - `${github.sha}`

현재 워크플로에는 `kubectl`을 이용한 실제 클러스터 배포 단계가 주석 처리되어 있습니다.  
즉, 현재 상태 기준으로는 "이미지 빌드/푸시 자동화"까지 연결되어 있고, "클러스터 반영 자동화"는 추가 설정이 필요한 상태입니다.

## 13. 운영 시 확인 포인트

- 앱은 외부 `wttr.in` 서비스에 의존하므로 네트워크 통신이 가능해야 합니다.
- HPA 사용을 위해서는 `metrics-server`가 필요합니다.
- Ingress 사용을 위해서는 Ingress Controller가 필요합니다.
- Docker Compose는 로컬 프록시 테스트용이고, Kubernetes/Helm은 실제 배포용 구성입니다.
- 기본 테스트 파일은 현재 더미 테스트이므로, 실제 운영 전에는 기능 테스트를 보강하는 것이 좋습니다.

## 14. 자주 사용하는 명령어

### Docker

```bash
docker build -t weather-app .
docker compose up -d
docker compose down
```

### Kubernetes

```bash
kubectl apply -f k8s/
kubectl get pods
kubectl get svc
kubectl get ingress
kubectl rollout status deployment/flask
```

### Helm

```bash
helm install weather ./weather-chart -f weather-chart/values.dev.yaml
helm upgrade weather ./weather-chart -f weather-chart/values.prod.yaml
helm uninstall weather
```

## 15. 개선 아이디어

- `requirements.txt` 추가로 의존성 관리 명확화
- HTML 템플릿 분리
- 테스트 코드 확장
- GitHub Actions에 실제 Kubernetes 배포 자동화 연결
- Secret 관리 방식 개선
- 사용자 즐겨찾기 저장을 서버 세션 또는 DB 기반으로 확장

## 16. 라이선스 및 참고

학습 및 실습 목적의 배포 예제 프로젝트로 활용할 수 있습니다.  
외부 날씨 데이터는 `wttr.in` 응답에 의존합니다.

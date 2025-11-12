# HUFS - 빈 강의실 찾기

한국외국어대학교 서울캠퍼스의 빈 강의실을 찾아주는 간단한 웹 애플리케이션입니다.

## 실행 방법

1.  **의존성 설치:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **웹 서버 실행:**
    ```bash
    gunicorn app:app
    ```
    또는 개발 모드로 실행:
    ```bash
    python app.py
    ```

3.  브라우저에서 `http://127.0.0.1:8000` (gunicorn) 또는 `http://127.0.0.1:5001` (개발 서버)으로 접속합니다.

## 프로젝트 구조

-   `app.py`: 메인 Flask 애플리케이션
-   `data/classroom_schedule.json`: 강의실 시간표 데이터
-   `templates/index.html`: 프론트엔드 HTML 파일
-   `static/`: CSS, 이미지 등 정적 파일
-   `requirements.txt`: Python 의존성 목록

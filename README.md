# 🚀 CLONADO // ADVANCED WEB OPTIMIZER

> **HIGH-PERFORMANCE SYSTEM FOR EXTRACTION, OPTIMIZATION & AUDITING**

A high-performance web cloning system designed not just to download sites, but to **optimize, cleanse, and audit** them automatically.

Unlike basic `wget` or simple scraping scripts, **Clonado** leverages **Playwright** for dynamic content rendering (SPA/JS), **Celery** for asynchronous processing, and a proprietary **Optimization Engine** to minimize resource footprint.

![Python](https://img.shields.io/badge/PYTHON-3.11-0a0a0a?style=for-the-badge&logo=python&logoColor=3776AB) ![FastAPI](https://img.shields.io/badge/FASTAPI-0.109-009688?style=for-the-badge&logo=fastapi&logoColor=white) ![Celery](https://img.shields.io/badge/CELERY-DISTRIBUTED-37814A?style=for-the-badge&logo=celery&logoColor=white) ![Docker](https://img.shields.io/badge/DOCKER-READY-2496ED?style=for-the-badge&logo=docker&logoColor=white)

## ✨ CORE CAPABILITIES

*   **🌐 FULL JS RENDERING**: Capable of cloning Single Page Applications (React, Vue, Angular) and sites with *Lazy Loading* thanks to Playwright power.
*   **⚡ AUTO-OPTIMIZATION**:
    *   **Image Processing**: Automatic WebP/JPEG conversion and compression via `Pillow`.
    *   **Code Minification**: CSS and JavaScript reduction for improved clone performance.
*   **🛡️ TRACKER NEUTRALIZATION**: Automatically identifies and removes tracking scripts (Google Analytics, Facebook Pixel) and disables forms for safe "offline" navigation.
*   **📊 QUALITY SCORE**: Audits the cloned site and generates a quality report based on accessibility, resource optimization, and broken link analysis.
*   **🏗️ SCALABLE ARCHITECTURE**: Microservices design using FastAPI (API), Celery (Workers), and Redis (Broker). Production ready.
*   **📦 ZIP PACKAGING**: Delivers the complete, clean site in a polished `.zip` archive ready for local browsing or deployment.

## 🛠️ TECH STACK

| COMPONENT | TECHNOLOGY |
| :--- | :--- |
| **Backend** | Python, FastAPI |
| **Task Queue** | Celery + Redis |
| **Scraping Engine** | Playwright + BeautifulSoup4 |
| **Image Engine** | Pillow (PIL) |
| **Containerization** | Docker & Docker Compose |

## 🚀 INSTALLATION & DEPLOYMENT

The fastest way to launch the system is via Docker Compose.

### PREREQUISITES
*   Docker
*   Docker Compose

### 1. CLONE REPOSITORY
```bash
git clone https://github.com/luismellizo/clonado.git
cd clonado
```

### 2. EXECUTE WITH DOCKER
This command initiates the API, Celery Worker, and Redis services.
```bash
docker-compose up --build
```
> **SYSTEM ACCESS:** `http://localhost:8000`

---

## 💻 LOCAL DEVELOPMENT (NO DOCKER)

If you prefer manual execution:

**INSTALL DEPENDENCIES**
```bash
pip install -r requirements.txt
playwright install
playwright install-deps
```

**START REDIS**
Ensure a local Redis instance is running.

**START WORKER [TERMINAL 1]**
```bash
celery -A app.celery_app worker --loglevel=info
```

**START API [TERMINAL 2]**
```bash
uvicorn app.main:app --reload
```

## 📖 USAGE PROTOCOL

1.  Open browser at `http://localhost:8000`
2.  Input target URL (e.g., `https://example.com`)
3.  System will initiate background protocol:
    *   `[NAV]` Navigation & Auto-Scroll
    *   `[GET]` Resource Assets Download
    *   `[SEC]` Tracker Neutralization
    *   `[OPT]` Image & Code Optimization
    *   `[QAL]` Quality Score Calculation
4.  Download optimized `.zip` archive.

## 📂 PROJECT STRUCTURE

```text
├── app/
│   ├── main.py          # FastAPI Entry Point
│   ├── tasks.py         # Async Task Definitions
│   ├── cloner.py        # Playwright Scraping Logic
│   ├── optimizer.py     # Resource Optimization Engine
│   ├── quality.py       # Quality Scoring Algorithm
│   └── validator.py     # File Validation & Security
├── frontend/            # User Interface (HTML/JS)
├── docker-compose.yml   # Service Orchestration
└── requirements.txt     # Python Dependencies
```

## 🤝 CONTRIBUTION

Contributions are welcome. Please open an issue to discuss major changes before submitting a Pull Request.

## 📄 LICENSE

This project is licensed under the MIT License.

---
> *"Cloning the web, one byte at a time."*

© 2026 CLONADO SYSTEM. ALL RIGHTS RESERVED.

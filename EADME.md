# SpaceX Explorer API 🚀

[cite_start]A DevOps-oriented backend service built with FastAPI that provides simplified access to SpaceX launch and rocket data[cite: 3]. [cite_start]This project implements a full DevOps lifecycle, including automated CI/CD, security scanning, and container orchestration[cite: 4].

## 🛠 Features
* [cite_start]**REST API**: Lightweight endpoints (<150 lines of code) for SpaceX data[cite: 3, 35].
* [cite_start]**Observability**: Integrated Prometheus metrics, structured JSON logging, and custom request tracing[cite: 11, 42].
* [cite_start]**Security**: Automated SAST and DAST scanning integrated into the pipeline[cite: 15, 43].
* [cite_start]**Containerization**: Multi-stage Docker build for optimized image size[cite: 18, 41].
* [cite_start]**Deployment**: Kubernetes manifests for local or cloud deployment[cite: 19, 44].

## 🚀 Local Setup
1. **Clone the repository** and navigate to the project root.
2. [cite_start]**Install dependencies**[cite: 20]:
   ```bash
   pip install -r requirements.txt
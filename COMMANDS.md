**RUN SCRIPT**

uvicorn app.main:app --host 0.0.0.0 --port 8000



**DOCKER BUILD**

docker rm spacex-api

docker stop spacex-api

docker build -t spacex-api:1.0 .

docker run -d -p 8000:8000 --name spacex-api spacex-api:1.0

docker ps



**TRACING**

docker logs -f spacex-api





**RUN DOCKER PROMETHEUS**

docker rm -f prometheus

docker run -d --name prometheus -p 9090:9090 -v C:/Users/Lenovo/Desktop/devops-project/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus



**VISUALISE PROMETHEUS UI (METRICS)**

http://localhost:9090

   - spacex\_requests\_total

   -spacex\_errors\_total

   -rate(spacex\_request\_latency\_seconds\_sum\[1m]) / rate(spacex\_request\_latency\_seconds\_count\[1m])

**SAST**

bandit -r app/ -f json -o bandit-report.json

safety check --json > safety-report.json

streamlit run dashboard.py





**DAST**

python dast\_scan.py

streamlit run Dast\_Dashboard.py











**KUBERNETES**

  minikube start

minikube image build -t spacex-api:1.0 .


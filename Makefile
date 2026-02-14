stop:
	docker compose down --volumes --remove-orphans

up:
	mkdir -p ./airflow/{dags,logs,plugins,config}
	docker compose up airflow-init
	docker compose up --build -d

kill-generator:
	docker kill generator

upload-json-samples:
	curl -X POST "http://localhost:8080/logs/upload" -H  "accept: application/json" -H  "Content-Type: multipart/form-data" -F "file=@log-collector/samples/logs.json"

upload-clf-samples:
	curl -X POST "http://localhost:8080/logs/upload" -H  "accept: application/json" -H  "Content-Type: multipart/form-data" -F "file=@log-collector/samples/logs.clf"

upload-syslog-samples:
	curl -X POST "http://localhost:8080/logs/upload" -H  "accept: application/json" -H  "Content-Type: multipart/form-data" -F "file=@log-collector/samples/logs.syslog"

.PHONY: up clean kill-generator upload-json-samples upload-syslog-samples upload-clf-samples

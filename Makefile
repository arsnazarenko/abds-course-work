init:
	mkdir -p ./airflow/{dags,logs,plugins,config}
	mkdir -p ./volumes/{prometheus-data,grafana-data} && chmod 777 ./volumes/{prometheus-data,grafana-data}
	mkdir -p ./volumes/{rmq1-data,rmq2-data,rmq3-data} && chmod 777 ./volumes/{rmq1-data,rmq2-data,rmq3-data}
	mkdir -p ./volumes/{ch1-data,ch2-data,ch3-data} && chmod 777 ./volumes/{ch1-data,ch2-data,ch3-data}

up:
	docker compose up --build -d

stop:
	docker compose down --volumes --remove-orphans

kill-generator:
	docker kill generator

upload-json-samples:
	curl -X POST "http://localhost:8080/logs/upload" -H  "accept: application/json" -H  "Content-Type: multipart/form-data" -F "file=@log-collector/samples/logs.json"

upload-clf-samples:
	curl -X POST "http://localhost:8080/logs/upload" -H  "accept: application/json" -H  "Content-Type: multipart/form-data" -F "file=@log-collector/samples/logs.clf"

upload-syslog-samples:
	curl -X POST "http://localhost:8080/logs/upload" -H  "accept: application/json" -H  "Content-Type: multipart/form-data" -F "file=@log-collector/samples/logs.syslog"

.PHONY: up stop kill-generator upload-json-samples upload-syslog-samples upload-clf-samples init

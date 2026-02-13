clean: 
	docker compose down --volumes --remove-orphans

start:
	mkdir -p ./dags ./logs ./plugins ./config
	docker compose up airflow-init
	docker compose up --build -d

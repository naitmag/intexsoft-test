lint:
	poetry run flake8 .

format:
	poetry run isort .
	poetry run black --check .

check:
	make lint
	make format

start-build:
	docker-compose down
	docker-compose up --build

start:
	docker-compose up

restart-app:
	docker-compose up -d --build app

stop:
	docker-compose stop

down:
	docker-compose down

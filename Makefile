.PHONY: build up down test logs clean

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down -v

test:
	pytest tests/ -v

logs:
	docker-compose logs -f

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
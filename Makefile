.PHONY: help up down logs index eval load lint test fmt psql tf-validate

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "};{printf "  \033[36m%-14s\033[0m %s\n",$$1,$$2}'

up:            ## build and start the full stack
	docker compose up -d --build

down:          ## stop and remove volumes
	docker compose down -v

logs:          ## tail the service logs
	docker compose logs -f api worker

index:         ## run the indexer over ./data
	docker compose run --rm worker

eval:          ## run the evaluation queries against a running api
	python3 scripts/eval.py

load:          ## concurrency demo — shows batching behaviour under load
	./scripts/load.sh

lint:          ## ruff
	ruff check . && ruff format --check .

fmt:
	ruff format .

test:          ## pytest (testcontainers spins up a real postgres)
	pytest -q

psql:
	docker compose exec postgres psql -U jenie -d jenie

tf-validate:   ## terraform fmt + validate, no cloud account needed
	cd infra/terraform/envs/dev && terraform init -backend=false && terraform validate

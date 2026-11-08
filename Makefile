# Two clusters, two Terraform states, one git repo reconciled by Flux.
#
#   make bootstrap   one-time: generate the age key and pin GitHub's host key
#   make up-dev      create the dev cluster and point Flux at clusters/dev
#   make images      build and side-load images (kind has no registry)
#   make validate    everything CI checks, locally
#
SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

TF_DEV  := infrastructure/terraform/envs/dev
TF_PROD := infrastructure/terraform/envs/prod
REGISTRY ?= ghcr.io/fordpatsakorn
TAG ?= v0.1.0

export TF_VAR_sops_age_key = $(shell cat .secrets/age.agekey 2>/dev/null)
export TF_VAR_git_known_hosts = $(shell cat .secrets/known_hosts 2>/dev/null)
export TF_VAR_image_automation_deploy_key = $(shell cat .secrets/deploy_key 2>/dev/null)

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n",$$1,$$2}'

.PHONY: bootstrap
bootstrap: ## Generate the SOPS age key and pin GitHub's SSH host key
	@mkdir -p .secrets
	@test -f .secrets/age.agekey || age-keygen -o .secrets/age.agekey
	@ssh-keyscan github.com > .secrets/known_hosts 2>/dev/null
	@echo "age public key (put this in .sops.yaml):"
	@grep 'public key' .secrets/age.agekey

.PHONY: up-dev up-prod
up-dev: ## Create the dev cluster and bootstrap Flux
	cd $(TF_DEV) && terraform init -input=false && terraform apply -auto-approve
up-prod: ## Create the prod cluster and bootstrap Flux
	cd $(TF_PROD) && terraform init -input=false && terraform apply -auto-approve

.PHONY: down-dev down-prod
down-dev: ## Destroy the dev cluster
	cd $(TF_DEV) && terraform destroy -auto-approve
down-prod: ## Destroy the prod cluster
	cd $(TF_PROD) && terraform destroy -auto-approve

.PHONY: images
images: ## Build images and side-load them (kind has no registry)
	docker build -t $(REGISTRY)/jenie-api:$(TAG) -f api/Dockerfile .
	docker build -t $(REGISTRY)/jenie-indexer:$(TAG) -f worker/Dockerfile .
	docker build -t $(REGISTRY)/postgres-pgvector:17 images/postgres-pgvector
	for c in jenie-dev jenie-prod; do \
	  kind get clusters | grep -qx $$c || continue; \
	  kind load docker-image --name $$c $(REGISTRY)/jenie-api:$(TAG) $(REGISTRY)/jenie-indexer:$(TAG) $(REGISTRY)/postgres-pgvector:17; \
	done

.PHONY: validate
validate: ## Everything CI checks: terraform, helm, kustomize
	terraform -chdir=$(TF_DEV)  init -backend=false -input=false >/dev/null && terraform -chdir=$(TF_DEV)  validate
	terraform -chdir=$(TF_PROD) init -backend=false -input=false >/dev/null && terraform -chdir=$(TF_PROD) validate
	terraform fmt -check -recursive infrastructure
	@# Linted against each ci/ values file rather than bare: the schema requires
	@# target.name and target.selector, so default values are *meant* to fail.
	@# That is the convention ci/ exists for (chart-testing does the same).
	@for f in charts/service-policy/ci/*.yaml; do \
	  echo "  lint   $$f"; helm lint charts/service-policy -f $$f --quiet || exit 1; \
	  helm template t charts/service-policy -f $$f -n jenie >/dev/null || exit 1; \
	done
	@for d in kubernetes/infrastructure/controllers/overlays/dev \
	          kubernetes/infrastructure/controllers/overlays/prod \
	          kubernetes/infrastructure/configs \
	          kubernetes/apps/jenie/overlays/dev \
	          kubernetes/apps/jenie/overlays/prod; do \
	  echo "  build  $$d"; kustomize build $$d >/dev/null || exit 1; \
	done

.PHONY: status
status: ## What Flux thinks of the world
	flux get all -A

.PHONY: canary
canary: ## Watch the prod canary progress
	kubectl -n jenie get canary -w

# Two clusters, two Terraform states, one git repo reconciled by Flux.
#
#   make bootstrap   one-time: generate the age key and pin GitHub's host key
#   make up-dev      create the dev cluster and point Flux at clusters/dev
#   make images      build and side-load images (kind has no registry)
#   make validate    everything CI checks, locally
#
# Cluster-facing targets take ENV (default dev):
#
#   make status ENV=prod
#   make reconcile          pull git now instead of waiting for the interval
#   make smoke              is the gateway answering
#   make logs C=source-controller
#
SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

TF_DEV  := infrastructure/terraform/envs/dev
TF_PROD := infrastructure/terraform/envs/prod
STAGES  := 1-cluster 2-platform

# Which cluster the cluster-facing targets talk to.
ENV ?= dev

# Derived from the repo, never inherited from the shell. This is a safety
# property, not a convenience: without it `make status` runs against whatever
# context happens to be current — which on a machine with a real homelab
# cluster means a repo-local command quietly talking to production.
KUBECONFIG_PATH := $(CURDIR)/infrastructure/terraform/envs/$(ENV)/1-cluster/.kube/config
export KUBECONFIG := $(KUBECONFIG_PATH)

# kind maps the gateway NodePort to a different host port per env so the two
# clusters can run side by side.
ifeq ($(ENV),prod)
GATEWAY_URL := http://localhost
else
GATEWAY_URL := http://localhost:8080
endif

# Four root modules share one provider download. Also a workaround with a
# second purpose: the registry serves provider checksums from GitHub release
# assets, which some networks time out on, so re-downloading per stage turns
# one flaky dependency into four.
export TF_PLUGIN_CACHE_DIR := $(CURDIR)/.terraform-cache
REGISTRY ?= ghcr.io/fordkuppp
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
	@grep -q 'age:' .sops.yaml 2>/dev/null || { \
	  key=$$(grep 'public key' .secrets/age.agekey | awk '{print $$NF}'); \
	  printf 'creation_rules:\n  - path_regex: kubernetes/.*\\.sops\\.ya?ml$$\n    encrypted_regex: ^(data|stringData)$$\n    age: %s\n' "$$key" > .sops.yaml; \
	  echo "wrote .sops.yaml — commit it, it holds only the public key"; \
	}
	@grep 'public key' .secrets/age.agekey

.PHONY: up-dev up-prod
up-dev: ## Create the dev cluster and bootstrap Flux
	@for s in $(STAGES); do \
	  echo "==> $$s"; \
	  terraform -chdir=$(TF_DEV)/$$s init -input=false >/dev/null && \
	  terraform -chdir=$(TF_DEV)/$$s apply -auto-approve || exit 1; \
	done
up-prod: ## Create the prod cluster and bootstrap Flux
	@for s in $(STAGES); do \
	  echo "==> $$s"; \
	  terraform -chdir=$(TF_PROD)/$$s init -input=false >/dev/null && \
	  terraform -chdir=$(TF_PROD)/$$s apply -auto-approve || exit 1; \
	done

.PHONY: down-dev down-prod
down-dev: ## Destroy the dev cluster (reverse stage order)
	-terraform -chdir=$(TF_DEV)/2-platform destroy -auto-approve
	terraform -chdir=$(TF_DEV)/1-cluster destroy -auto-approve
down-prod: ## Destroy the prod cluster (reverse stage order)
	-terraform -chdir=$(TF_PROD)/2-platform destroy -auto-approve
	terraform -chdir=$(TF_PROD)/1-cluster destroy -auto-approve

.PHONY: images
images: ## Build infra images and side-load them (kind has no registry)
	@# Only the operand image for now. The api and indexer builds return when
	@# the application comes back out of temp/ — see docs/decisions.md.
	docker build -t $(REGISTRY)/postgres-pgvector:17 infrastructure/images/postgres-pgvector
	@for c in jenie-dev jenie-prod; do \
	  kind get clusters | grep -qx $$c || continue; \
	  kind load docker-image --name $$c $(REGISTRY)/postgres-pgvector:17; \
	done

.PHONY: validate
validate: ## Everything CI checks: terraform, helm, kustomize
	@for e in $(TF_DEV) $(TF_PROD); do for s in $(STAGES); do \
	  echo "  tf     $$e/$$s"; \
	  terraform -chdir=$$e/$$s init -backend=false -input=false >/dev/null && \
	  terraform -chdir=$$e/$$s validate >/dev/null || exit 1; \
	done; done
	terraform fmt -check -recursive infrastructure
	@# Linted against each ci/ values file rather than bare: the schema requires
	@# target.name and target.selector, so default values are *meant* to fail.
	@# That is the convention ci/ exists for (chart-testing does the same).
	@for f in kubernetes/charts/service-policy/ci/*.yaml; do \
	  echo "  lint   $$f"; helm lint kubernetes/charts/service-policy -f $$f --quiet || exit 1; \
	  helm template t kubernetes/charts/service-policy -f $$f -n jenie >/dev/null || exit 1; \
	done
	@for d in kubernetes/infrastructure/controllers/overlays/dev \
	          kubernetes/infrastructure/controllers/overlays/prod \
	          kubernetes/infrastructure/configs \
	          kubernetes/apps/jenie/overlays/dev \
	          kubernetes/apps/jenie/overlays/prod \
	          kubernetes/apps/jenie/image-automation; do \
	  echo "  build  $$d"; kustomize build $$d >/dev/null || exit 1; \
	done

# Every cluster-facing target depends on this. It fails loudly rather than
# falling through to the ambient context.
.PHONY: guard
guard:
	@test -f "$(KUBECONFIG_PATH)" || { \
	  echo "no kubeconfig at $(KUBECONFIG_PATH)"; \
	  echo "the ENV=$(ENV) cluster does not exist — run: make up-$(ENV)"; \
	  echo; \
	  echo "not falling back to your current context on purpose: that is how"; \
	  echo "a command in this repo ends up talking to a cluster you care about."; \
	  exit 1; }

.PHONY: kubeconfig
kubeconfig: guard ## Print the export line for this ENV's cluster
	@echo "export KUBECONFIG=$(KUBECONFIG_PATH)"

.PHONY: status
status: guard ## Flux and workload status for ENV (default dev)
	@echo "context: $$(kubectl config current-context)"
	@echo
	@flux get all -A

.PHONY: reconcile
reconcile: guard ## Pull git now instead of waiting out the sync interval
	@# The loop that should have been used instead of `kubectl apply -k`
	@# during debugging: ~15s, and it cannot leave the cluster holding state
	@# that is not in the repo.
	flux reconcile source git flux2-sync
	flux reconcile kustomization infra-controllers
	flux reconcile kustomization infra-configs
	-flux reconcile kustomization apps

.PHONY: smoke
smoke: guard ## Is the gateway answering, and is it programmed?
	@printf 'GET %s/  -> ' '$(GATEWAY_URL)'
	@curl -sS -o /dev/null -w 'HTTP %{http_code}\n' --max-time 8 '$(GATEWAY_URL)/' \
	  || echo '(no answer — check `make status` and the Gateway below)'
	@echo
	@kubectl get gateway -A
	@echo
	@kubectl -n envoy-gateway-system get svc -l gateway.envoyproxy.io/owning-gateway-name=external 2>/dev/null \
	  || kubectl -n envoy-gateway-system get svc

.PHONY: logs
logs: guard ## Tail a controller: make logs C=source-controller [ENV=prod]
	@case "$(C)" in \
	  ""|source-controller|kustomize-controller|helm-controller|notification-controller|image-automation-controller|image-reflector-controller) \
	    kubectl -n flux-system logs -l "app=$${C:-source-controller}" --tail=100 -f ;; \
	  envoy-gateway) kubectl -n envoy-gateway-system logs -l control-plane=envoy-gateway --tail=100 -f ;; \
	  envoy)         kubectl -n envoy-gateway-system logs -l gateway.envoyproxy.io/owning-gateway-name=external -c envoy --tail=100 -f ;; \
	  flagger)       kubectl -n flagger-system logs -l app.kubernetes.io/name=flagger --tail=100 -f ;; \
	  sloth)         kubectl -n sloth logs -l app.kubernetes.io/name=sloth --tail=100 -f ;; \
	  cnpg)          kubectl -n cnpg-system logs -l app.kubernetes.io/name=cloudnative-pg --tail=100 -f ;; \
	  *) echo "unknown component '$(C)'"; exit 1 ;; \
	esac

.PHONY: canary
canary: guard ## Watch canary rollouts (prod runs the progressive strategy)
	kubectl -n jenie get canary -w

.PHONY: events
events: guard ## Recent warnings, newest last — usually says why something is stuck
	kubectl get events -A --field-selector type=Warning --sort-by=.lastTimestamp 2>/dev/null | tail -25

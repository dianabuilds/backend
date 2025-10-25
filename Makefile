.PHONY: run-public run-admin run-ops docker-local-% docker-local-down

# Allow overriding paths/commands for custom setups
BACKEND_DIR ?= apps/backend
COMPOSE ?= docker compose
COMPOSE_PROFILE ?= local

# Forward contour runs to the backend Makefile
run-public run-admin run-ops:
	@$(MAKE) -C $(BACKEND_DIR) $@

# docker-local-backend-public -> docker compose --profile local up backend-public
docker-local-%:
	$(COMPOSE) --profile $(COMPOSE_PROFILE) up $*

docker-local-down:
	$(COMPOSE) --profile $(COMPOSE_PROFILE) down

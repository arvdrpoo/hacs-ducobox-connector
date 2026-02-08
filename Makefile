# Makefile

include devcontainers/local.env

# Check for docker compose command
ifneq ($(shell command -v docker compose >/dev/null 2>&1 && echo $$?),)
    DC=docker compose --env-file devcontainers/local.env -f devcontainers/docker-compose.yml
else
    DC=docker-compose --env-file devcontainers/local.env -f devcontainers/docker-compose.yml
endif

.PHONY: build start stop restart logs clean open-browser ensure-paths test

# Ensure necessary directories exist
ensure-paths:
	@mkdir -p $(HA_CONF_DIR)/homeassistant
	@mkdir -p ./custom_components/ducobox-connectivity-board
	@echo "Verified necessary paths."

# Build and pull images
build: ensure-paths
	PUID=$(PUID) PGID=$(PGID) TZ=$(TZ) HA_CONF_DIR=$(HA_CONF_DIR) $(DC) pull

# Start the Home Assistant container
start: build
	PUID=$(PUID) PGID=$(PGID) TZ=$(TZ) HA_CONF_DIR=$(HA_CONF_DIR) $(DC) up -d
	@echo "Waiting for Home Assistant to be healthy..."
	@until [ "$$($(DC) ps -q homeassistant | xargs docker inspect -f '{{.State.Health.Status}}')" = "healthy" ]; do \
		sleep 5; \
		echo "Still waiting..."; \
	done
	@echo "Home Assistant is healthy! Launching browser..."
	$(MAKE) open-browser

# Stop the Home Assistant container
stop:
	$(DC) down

# Restart the container to test changes
restart:
	$(MAKE) stop && $(MAKE) start

# Show logs for the Home Assistant container
logs:
	$(DC) logs -f homeassistant

# Clean up containers and remove volumes
clean:
	$(DC) down -v

# Rebuild and restart for testing purposes
rebuild: clean build start

# Open Home Assistant in a browser
open-browser:
	xdg-open http://localhost:8123 || open http://localhost:8123 || start http://localhost:8123

# Run the test suite
test:
	.venv/bin/python -m pytest tests/ -v

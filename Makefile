.PHONY: configure

configure:
	@echo "Configuring test framework..."
	@python3 -m venv .venv
	@bash -c 'source .venv/bin/activate && echo "Using Python: $$(python3 -V)"'
	@echo "Installing dependencies..."
	@echo "" > config.log
	@bash -c 'source .venv/bin/activate && pip install $(PIP_FLAGS) -r requirements.txt -q --log config.log'
	@echo "Configuration completed."

clean:
	@echo "Cleaning test framework..."
	@rm -rf .venv
	@echo "Clean completed."

PHONY_TARGETS += test-framework test.test-framework render
.PHONY: $(PHONY_TARGETS)

test-framework:
	@if [ -z "$$DATA_PATH" ]; then \
		DATA_PATH=$$PWD/data; \
	fi
	@echo "DATA_PATH env value for test environment config: $$DATA_PATH"
	@python3 -m src.multi_server_test $(filter-out $(PHONY_TARGETS),$(MAKECMDGOALS))
	@echo "Multi-server test framework completed."

test.test-framework: test-framework

render:
	@echo "Rendering Jinja2 from $@..."
	@DATA_PATH=$$PWD/data python3 -m src.config_builder $(filter-out $(PHONY_TARGETS),$(MAKECMDGOALS))
	@echo "Rendering completed."

# Dummy targets to avoid "No rule to make target" errors
%:
	@:

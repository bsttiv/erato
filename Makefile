.PHONY: test test-harness
TEST_COMPOSE = docker compose -p erato-test -f compose.yaml -f backend/compose.test.yaml --profile test

test:
	@set -eu; \
	cleanup() { $(TEST_COMPOSE) down --volumes --remove-orphans; }; \
	trap cleanup EXIT; trap 'exit 130' INT; trap 'exit 143' TERM; \
	$(TEST_COMPOSE) build backend-test frontend-test maestro-mock maestro-mock-control; \
	result=0; \
	$(TEST_COMPOSE) run --rm backend-test || result=1; \
	$(TEST_COMPOSE) run --rm frontend-test || result=1; \
	exit $$result

test-harness:
	python3 backend/test_harness.py

.PHONY: help dev build migrate seed demo clean logs status

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

dev: ## Start development environment  
	docker-compose -f docker-compose.simple.yml up --build -d
	@echo ""
	@echo "🚀 EvalWise Backend Started!"
	@echo "📱 API: http://localhost:8000"
	@echo "🔗 API docs: http://localhost:8000/docs"
	@echo "📊 Health: http://localhost:8000/health"
	@echo ""

build: ## Build all services
	docker-compose -f docker-compose.simple.yml build

migrate: ## Run database migrations
	docker-compose -f docker-compose.simple.yml run --rm api alembic upgrade head

seed: ## Seed database with test data via SQL
	@echo "Seeding database with test data..."
	docker-compose -f docker-compose.simple.yml exec postgres psql -U evalwise -d evalwise -c "DELETE FROM evaluator;" || true
	docker-compose -f docker-compose.simple.yml exec postgres psql -U evalwise -d evalwise -c "DELETE FROM scenario;" || true  
	docker-compose -f docker-compose.simple.yml exec postgres psql -U evalwise -d evalwise -c "DELETE FROM dataset;" || true
	docker-compose -f docker-compose.simple.yml exec postgres psql -U evalwise -d evalwise -c "INSERT INTO evaluator (id, name, kind, config_json) VALUES (gen_random_uuid(), 'Rule-based Safety', 'rule_based', '{\"denylist\": [\"bomb\", \"weapon\", \"kill\", \"hate\"]}');"
	docker-compose -f docker-compose.simple.yml exec postgres psql -U evalwise -d evalwise -c "INSERT INTO evaluator (id, name, kind, config_json) VALUES (gen_random_uuid(), 'PII Detector', 'pii_regex', '{\"patterns\": [\"email\", \"phone\", \"ssn\"]}');"
	docker-compose -f docker-compose.simple.yml exec postgres psql -U evalwise -d evalwise -c "INSERT INTO evaluator (id, name, kind, config_json) VALUES (gen_random_uuid(), 'LLM Judge Safety', 'llm_judge', '{\"judge_model\": \"gpt-4\", \"rubric\": \"general\"}');"
	docker-compose -f docker-compose.simple.yml exec postgres psql -U evalwise -d evalwise -c "INSERT INTO scenario (id, name, type, params_json, tags) VALUES (gen_random_uuid(), 'Basic Jailbreak', 'jailbreak_basic', '{\"techniques\": [\"dan\", \"roleplay\"]}', ARRAY['jailbreak']);"
	docker-compose -f docker-compose.simple.yml exec postgres psql -U evalwise -d evalwise -c "INSERT INTO scenario (id, name, type, params_json, tags) VALUES (gen_random_uuid(), 'Safety Probe', 'safety_probe', '{\"categories\": [\"violence\", \"hate_speech\"]}', ARRAY['safety']);"
	docker-compose -f docker-compose.simple.yml exec postgres psql -U evalwise -d evalwise -c "INSERT INTO dataset (id, name, version_hash, tags, is_synthetic) VALUES (gen_random_uuid(), 'Demo QA Dataset', 'demo123', ARRAY['demo', 'qa'], true);"
	@echo "✅ Database seeded successfully!"

test-api: ## Test API endpoints
	@echo "Testing API endpoints..."
	@echo "Health check:"
	@curl -s http://localhost:8000/health | jq . || echo "API not responding"
	@echo "\nDatasets:"
	@curl -s http://localhost:8000/datasets | jq . || echo "Datasets endpoint not working"
	@echo "\nScenarios:"
	@curl -s http://localhost:8000/scenarios | jq . || echo "Scenarios endpoint not working"
	@echo "\nEvaluators:"
	@curl -s http://localhost:8000/evaluators | jq . || echo "Evaluators endpoint not working"

demo: ## Run complete demo (migrate + seed + start)
	@echo "Starting EvalWise demo..."
	$(MAKE) migrate
	$(MAKE) dev
	@sleep 3
	$(MAKE) seed
	$(MAKE) test-api
	@echo ""
	@echo "🚀 EvalWise Demo Started!"
	@echo "📱 API: http://localhost:8000"
	@echo "🔗 API docs: http://localhost:8000/docs"
	@echo "📊 Health: http://localhost:8000/health"
	@echo ""
	@echo "You can now:"
	@echo "- Visit http://localhost:8000/docs to explore the API"
	@echo "- Create datasets, scenarios, evaluators via the API"
	@echo "- Run 'make test-api' to test endpoints"
	@echo "- Run 'make clean' to stop everything"

clean: ## Clean up containers and volumes
	docker-compose -f docker-compose.simple.yml down -v
	docker system prune -f

logs: ## Show logs
	docker-compose -f docker-compose.simple.yml logs -f api

status: ## Show container status
	docker-compose -f docker-compose.simple.yml ps
# FootballDecoded Data Infrastructure - Makefile
# Simplified commands for development workflow

.PHONY: help install setup-db test lint clean extract analyze deploy

# Default target
help:
	@echo "FootballDecoded Data Infrastructure Commands"
	@echo "==========================================="
	@echo ""
	@echo "Setup:"
	@echo "  install     Install project dependencies"
	@echo "  setup-db    Initialize PostgreSQL database with PostGIS"
	@echo ""
	@echo "Development:"
	@echo "  extract     Run data extraction pipeline"
	@echo "  analyze     Generate tactical analysis"
	@echo "  test        Run tests (when implemented)"
	@echo "  lint        Format and lint code"
	@echo ""
	@echo "Data:"
	@echo "  clean       Clean cache and logs"
	@echo "  backup      Backup database"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy      Deploy with Docker"

# Installation and setup
install:
	pip install -e .
	pip install -e ".[dev,analysis]"
	@echo "✅ FootballDecoded dependencies installed"

setup-db:
	createdb footballdecoded_dev || echo "Database already exists"
	psql footballdecoded_dev -c "CREATE EXTENSION IF NOT EXISTS postgis;"
	psql footballdecoded_dev -c "CREATE EXTENSION IF NOT EXISTS btree_gist;"
	@echo "✅ Database setup completed"

# Development workflow
extract:
	python pipelines/extraction_pipeline.py --league "ENG-Premier League" --season 2024
	@echo "✅ Data extraction completed"

analyze:
	python analytics/tactical_analytics/pressure_analysis.py
	python analytics/tactical_analytics/space_control.py
	@echo "✅ Tactical analysis completed"

test:
	pytest tests/ -v --cov=core --cov=analytics
	@echo "✅ Tests completed"

lint:
	black core/ analytics/ pipelines/ visualizations/ tools/
	isort core/ analytics/ pipelines/ visualizations/ tools/
	flake8 core/ analytics/ pipelines/ visualizations/ tools/
	@echo "✅ Code formatting completed"

# Data management
clean:
	rm -rf data/cache/*
	rm -rf logs/*.log
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cache and logs cleaned"

backup:
	pg_dump footballdecoded_dev > backups/footballdecoded_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backup created"

# Deployment
deploy:
	docker-compose up --build -d
	@echo "✅ FootballDecoded stack deployed"

# Quick development cycle
dev-cycle: lint extract analyze
	@echo "✅ Full development cycle completed"

# Database operations
reset-db:
	dropdb footballdecoded_dev --if-exists
	make setup-db
	@echo "✅ Database reset completed"

# Monitoring
logs:
	tail -f logs/footballdecoded.log

status:
	@echo "FootballDecoded Status:"
	@echo "======================"
	@echo "Database: $(shell psql -lqt | cut -d \| -f 1 | grep footballdecoded_dev | wc -l | xargs echo) database(s)"
	@echo "Cache size: $(shell du -sh data/cache 2>/dev/null || echo '0B')"
	@echo "Logs: $(shell ls logs/*.log 2>/dev/null | wc -l) files"
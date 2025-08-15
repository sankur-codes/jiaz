# Makefile

APP_NAME=jiaz
PYINSTALLER_IMAGE=jiaz-builder
PYINSTALLER_SPEC=jiaz/__main__.py

# Automatically detect architecture
ARCH ?= $(shell uname -m)
PLATFORM = $(shell \
	if [ "$(ARCH)" = "arm64" ] || [ "$(ARCH)" = "aarch64" ]; then \
		echo "linux/arm64"; \
	elif [ "$(ARCH)" = "x86_64" ]; then \
		echo "linux/amd64"; \
	elif [ "$(ARCH)" = "arm" ]; then \
		echo "linux/arm"; \
	else \
		echo "linux/amd64"; \
	fi)


.PHONY: help build clean docker-build test test-cov test-cov-missing fix-imports fix-whitespace fix-all lint format prepare

help:
	@echo "Available targets:"
	@echo "  build                     Build standalone binary using pip and pyinstaller"
	@echo "  clean                     Remove build artifacts"
	@echo "  docker-build              Building binary in dockerised way (only for Linux)"
	@echo "  ARCH=<arch> make build    Override detected architecture if needed (e.g., ARCH=amd64)"
	@echo "  test                      Run tests for all commands"
	@echo "  test-cov                  Run tests with coverage"
	@echo "  test-cov-missing          Run tests with coverage and show missing coverage"
	@echo "  fix-imports               Fix unused imports using autoflake"
	@echo "  fix-whitespace            Fix whitespace issues (trailing spaces, blank lines)"
	@echo "  fix-all                   Fix both imports and whitespace issues"
	@echo "  lint                      Run linting checks (black, isort, flake8)"
	@echo "  format                    Format code with black and isort"

docker-build:
	@echo "Detected ARCH: $(ARCH)"
	@echo "Using PLATFORM: $(PLATFORM)"
	docker build --pull --platform=$(PLATFORM) -t $(PYINSTALLER_IMAGE) -f Dockerfile .
	docker run --rm \
		--platform=$(PLATFORM) \
		-v $(CURDIR):/app \
		-w /app \
		$(PYINSTALLER_IMAGE) \
		-c "pip install -r requirements.txt && pyinstaller --clean --onefile $(PYINSTALLER_SPEC) --name $(APP_NAME)"

build:
	@echo "Detected ARCH: $(ARCH)"
	@echo "Using PLATFORM: $(PLATFORM)"
	pip install -r requirements.txt && pyinstaller --clean --onedir jiaz/__main__.py --name jiaz


test:
	@echo "🔍 Running tests for jiaz project..."
	pytest jiaz

test-cov:
	@echo "🔍 Running tests with coverage..."
	pytest --cov=jiaz

test-cov-missing:
	@echo "🔍 Running tests with coverage and showing missing coverage..."
	pytest --cov=jiaz --cov-report=term-missing

clean:
	rm -rf build dist *.spec .coverage .coverage.* .pytest_cache
	find . -type d -name "__pycache__" -exec rm -r {} +

fix-imports:
	@echo "🔧 Fixing unused imports..."
	@which autoflake > /dev/null || pip install autoflake
	python -m autoflake --remove-all-unused-imports --in-place --recursive jiaz/
	@echo "✅ Unused imports fixed"

fix-whitespace:
	@echo "🔧 Fixing whitespace issues..."
	@for file in $$(find jiaz -name "*.py"); do \
		sed -i '' 's/[[:space:]]*$$//' "$$file"; \
		awk 'BEGIN{blank=0} /^[[:space:]]*$$/{blank++; if(blank<=2) print} !/^[[:space:]]*$$/{blank=0; print}' "$$file" > "$$file.tmp" && mv "$$file.tmp" "$$file"; \
	done
	@echo "✅ Whitespace issues fixed"

fix-all:
	@echo "🔧 Fixing unused imports and whitespace issues..."
	$(MAKE) fix-imports
	$(MAKE) fix-whitespace
	@echo "✅ Code quality fixes completed"

lint:
	@echo "🔍 Running linting checks..."
	black --check .
	isort --check-only --settings-path=utils/config/.isort.cfg .
	flake8 jiaz/ --config=utils/config/.flake8
	@echo "✅ Linting completed"

format:
	@echo "🎨 Formatting code..."
	black .
	isort --settings-path=utils/config/.isort.cfg .
	@echo "✅ Code formatting completed"

prepare:
	@echo "🔧 Preparing downloaded binary artifact..."
	ifeq ($(OS),Windows_NT)
		@echo "📦 Detected Windows. Unzipping downloaded artifact..."
		powershell -Command "Expand-Archive -Path jiaz-windows.zip -DestinationPath ."
		@echo "✅ Ready to use: ./jiaz.exe"
	else
		UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Darwin)
		@echo "🍏 Detected macOS. Unzipping and removing quarantine attribute..."
		unzip -o jiaz-macos.zip -d .
		xattr -d com.apple.quarantine ./jiaz || true
		@echo "✅ Ready to use: ./jiaz"
		@echo "💡 To re-apply quarantine: xattr -w com.apple.quarantine '00' ./jiaz"
	else
		@echo "🐧 Detected Linux. Unzipping artifact..."
		unzip -o jiaz-linux.zip -d .
		chmod +x ./jiaz
		@echo "✅ Ready to use: ./jiaz"
	endif
	endif
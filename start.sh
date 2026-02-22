#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
RUN_TESTS=false
REPORT_FILE="test-report.html"
COVERAGE_REPORT="coverage-report"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --test)
            RUN_TESTS=true
            shift
            ;;
        --report-file)
            REPORT_FILE="$2"
            shift 2
            ;;
        --coverage-dir)
            COVERAGE_REPORT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --test              Run test environment instead of normal environment"
            echo "  --report-file FILE  Output file for test report (default: test-report.html)"
            echo "  --coverage-dir DIR  Directory for coverage reports (default: coverage-report)"
            echo "  -h, --help          Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

if [ "$RUN_TESTS" = true ]; then
    echo -e "${GREEN}Starting test environment...${NC}"
    
    # Build and run tests with coverage
    docker compose -f docker-compose.test.yaml up --build --abort-on-container-exit --exit-code-from test 2>&1 | tee test-output.log
    TEST_EXIT_CODE=${PIPESTATUS[0]}
    
    # Stop and remove test containers
    echo -e "${YELLOW}Cleaning up test containers...${NC}"
    docker compose -f docker-compose.test.yaml down -v
    
    # Generate coverage report if tests ran
    if [ -f test-output.log ]; then
        echo -e "${GREEN}Test output saved to: test-output.log${NC}"
    fi
    
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}Tests passed!${NC}"
    else
        echo -e "${RED}Tests failed with exit code: $TEST_EXIT_CODE${NC}"
    fi
    
    exit $TEST_EXIT_CODE
else
    echo -e "${GREEN}Starting normal environment...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    
    # Start normal environment
    docker compose -f docker-compose.yaml up --build
fi

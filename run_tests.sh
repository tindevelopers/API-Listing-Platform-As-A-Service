#!/bin/bash

# LAAS Platform Test Runner
# This script runs the test suite with various configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if pytest is installed
check_dependencies() {
    log_info "Checking test dependencies..."
    
    if ! command -v pytest &> /dev/null; then
        log_error "pytest is not installed. Installing..."
        pip install pytest pytest-asyncio pytest-cov
    fi
    
    log_success "Test dependencies are ready"
}

# Run unit tests
run_unit_tests() {
    log_info "Running unit tests..."
    pytest tests/ -m "unit" -v --cov=laas --cov-report=term-missing
}

# Run integration tests
run_integration_tests() {
    log_info "Running integration tests..."
    pytest tests/ -m "integration" -v --cov=laas --cov-report=term-missing
}

# Run database tests
run_database_tests() {
    log_info "Running database tests..."
    pytest tests/test_database.py -v --cov=laas.database --cov-report=term-missing
}

# Run search tests
run_search_tests() {
    log_info "Running search tests..."
    pytest tests/test_search.py -v --cov=laas.search --cov-report=term-missing
}

# Run all tests
run_all_tests() {
    log_info "Running all tests..."
    pytest tests/ -v --cov=laas --cov-report=term-missing --cov-report=html
}

# Run tests with coverage report
run_coverage_tests() {
    log_info "Running tests with coverage report..."
    pytest tests/ -v --cov=laas --cov-report=html --cov-report=xml --cov-fail-under=80
}

# Run specific test file
run_test_file() {
    local test_file=$1
    if [ -z "$test_file" ]; then
        log_error "Please specify a test file"
        exit 1
    fi
    
    log_info "Running test file: $test_file"
    pytest "$test_file" -v
}

# Run tests with specific marker
run_marked_tests() {
    local marker=$1
    if [ -z "$marker" ]; then
        log_error "Please specify a test marker"
        exit 1
    fi
    
    log_info "Running tests with marker: $marker"
    pytest tests/ -m "$marker" -v
}

# Run tests in parallel
run_parallel_tests() {
    log_info "Running tests in parallel..."
    pytest tests/ -n auto -v
}

# Run tests with verbose output
run_verbose_tests() {
    log_info "Running tests with verbose output..."
    pytest tests/ -v -s --tb=long
}

# Run tests and generate report
run_report_tests() {
    log_info "Running tests and generating report..."
    pytest tests/ -v --cov=laas --cov-report=html --cov-report=xml --junitxml=test-results.xml
}

# Clean test artifacts
clean_test_artifacts() {
    log_info "Cleaning test artifacts..."
    rm -rf htmlcov/
    rm -rf .coverage
    rm -rf .pytest_cache/
    rm -rf test-results.xml
    rm -rf coverage.xml
    log_success "Test artifacts cleaned"
}

# Main function
main() {
    case "${1:-all}" in
        "check")
            check_dependencies
            ;;
        "unit")
            check_dependencies
            run_unit_tests
            ;;
        "integration")
            check_dependencies
            run_integration_tests
            ;;
        "database")
            check_dependencies
            run_database_tests
            ;;
        "search")
            check_dependencies
            run_search_tests
            ;;
        "coverage")
            check_dependencies
            run_coverage_tests
            ;;
        "parallel")
            check_dependencies
            run_parallel_tests
            ;;
        "verbose")
            check_dependencies
            run_verbose_tests
            ;;
        "report")
            check_dependencies
            run_report_tests
            ;;
        "file")
            check_dependencies
            run_test_file "$2"
            ;;
        "mark")
            check_dependencies
            run_marked_tests "$2"
            ;;
        "clean")
            clean_test_artifacts
            ;;
        "all")
            check_dependencies
            run_all_tests
            ;;
        *)
            echo "Usage: $0 {check|unit|integration|database|search|coverage|parallel|verbose|report|file|mark|clean|all}"
            echo ""
            echo "Commands:"
            echo "  check       - Check test dependencies"
            echo "  unit        - Run unit tests only"
            echo "  integration - Run integration tests only"
            echo "  database    - Run database tests only"
            echo "  search      - Run search tests only"
            echo "  coverage    - Run tests with coverage report"
            echo "  parallel    - Run tests in parallel"
            echo "  verbose     - Run tests with verbose output"
            echo "  report      - Run tests and generate report"
            echo "  file <file> - Run specific test file"
            echo "  mark <mark> - Run tests with specific marker"
            echo "  clean       - Clean test artifacts"
            echo "  all         - Run all tests (default)"
            echo ""
            echo "Examples:"
            echo "  $0 unit                    # Run unit tests"
            echo "  $0 file tests/test_auth.py # Run specific test file"
            echo "  $0 mark slow              # Run tests marked as slow"
            echo "  $0 coverage               # Run with coverage report"
            exit 1
            ;;
    esac
    
    log_success "Test execution completed!"
}

# Run main function
main "$@"


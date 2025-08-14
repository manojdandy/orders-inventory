#!/bin/bash

# Load Testing Script for Orders & Inventory Management API
# This script provides easy commands to run different types of load tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_HOST="http://localhost:8000"
RESULTS_DIR="load_test_results"

# Create results directory
mkdir -p "$RESULTS_DIR"

echo -e "${BLUE}🚀 Orders & Inventory API Load Testing Suite${NC}"
echo -e "${BLUE}=============================================${NC}"

# Function to check if API is running
check_api() {
    echo -e "${YELLOW}Checking if API is running...${NC}"
    if curl -s "$API_HOST/health" > /dev/null; then
        echo -e "${GREEN}✅ API is running at $API_HOST${NC}"
        return 0
    else
        echo -e "${RED}❌ API is not running at $API_HOST${NC}"
        echo -e "${YELLOW}Please start the API first:${NC}"
        echo -e "   ${BLUE}python run_api.py${NC}"
        return 1
    fi
}

# Function to run a specific test
run_test() {
    local test_name="$1"
    local test_file="$2"
    local users="$3"
    local spawn_rate="$4"
    local duration="$5"
    local description="$6"
    
    echo -e "\n${BLUE}Running $test_name${NC}"
    echo -e "${YELLOW}Description: $description${NC}"
    echo -e "${YELLOW}Users: $users, Spawn Rate: $spawn_rate, Duration: $duration${NC}"
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local result_prefix="$RESULTS_DIR/${test_name}_${timestamp}"
    
    # Run the test
    if locust -f "$test_file" \
              --host="$API_HOST" \
              --users="$users" \
              --spawn-rate="$spawn_rate" \
              --run-time="$duration" \
              --headless \
              --html="${result_prefix}.html" \
              --csv="${result_prefix}" \
              --logfile="${result_prefix}.log"; then
        echo -e "${GREEN}✅ $test_name completed successfully${NC}"
        echo -e "${BLUE}Results saved to: ${result_prefix}.*${NC}"
    else
        echo -e "${RED}❌ $test_name failed${NC}"
        return 1
    fi
}

# Test scenarios
case "${1:-help}" in
    "quick")
        echo -e "${BLUE}Running Quick Load Test${NC}"
        check_api || exit 1
        run_test "quick_test" "load_tests/locustfile.py" 10 2 "2m" \
                 "Quick smoke test with light load"
        ;;
    
    "standard")
        echo -e "${BLUE}Running Standard Load Test${NC}"
        check_api || exit 1
        run_test "standard_test" "load_tests/locustfile.py" 50 5 "5m" \
                 "Standard load test simulating normal traffic"
        ;;
    
    "stress")
        echo -e "${BLUE}Running Stress Test${NC}"
        check_api || exit 1
        run_test "stress_test" "load_tests/locustfile.py" 200 10 "10m" \
                 "High load stress test to find system limits"
        ;;
    
    "concurrency")
        echo -e "${BLUE}Running Concurrency Test${NC}"
        check_api || exit 1
        run_test "concurrency_test" "load_tests/scenarios.py" 50 10 "3m" \
                 "Test race conditions and concurrent access patterns"
        ;;
    
    "race")
        echo -e "${BLUE}Running Race Condition Test${NC}"
        check_api || exit 1
        run_test "race_condition_test" "load_tests/scenarios.py" 20 5 "2m" \
                 "Specific test for 'last item' race conditions"
        ;;
    
    "endurance")
        echo -e "${BLUE}Running Endurance Test${NC}"
        check_api || exit 1
        run_test "endurance_test" "load_tests/locustfile.py" 30 3 "30m" \
                 "Long-running test to check for memory leaks and stability"
        ;;
    
    "spike")
        echo -e "${BLUE}Running Spike Test${NC}"
        check_api || exit 1
        echo -e "${YELLOW}Phase 1: Baseline load${NC}"
        run_test "spike_baseline" "load_tests/locustfile.py" 10 2 "2m" \
                 "Baseline load before spike"
        
        echo -e "${YELLOW}Phase 2: Spike load${NC}"
        run_test "spike_peak" "load_tests/locustfile.py" 500 50 "1m" \
                 "Sudden spike in traffic"
        
        echo -e "${YELLOW}Phase 3: Recovery${NC}"
        run_test "spike_recovery" "load_tests/locustfile.py" 10 2 "2m" \
                 "Recovery after spike"
        ;;
    
    "interactive")
        echo -e "${BLUE}Starting Interactive Load Test${NC}"
        check_api || exit 1
        echo -e "${YELLOW}Opening Locust web UI...${NC}"
        echo -e "${BLUE}Access the UI at: http://localhost:8089${NC}"
        echo -e "${BLUE}Target host is set to: $API_HOST${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
        
        locust -f "load_tests/locustfile.py" --host="$API_HOST"
        ;;
    
    "all")
        echo -e "${BLUE}Running Complete Test Suite${NC}"
        check_api || exit 1
        
        echo -e "\n${YELLOW}🧪 Starting comprehensive load testing...${NC}"
        
        # Run all tests in sequence
        run_test "quick_smoke" "load_tests/locustfile.py" 5 1 "1m" \
                 "Initial smoke test"
        
        run_test "standard_load" "load_tests/locustfile.py" 25 3 "3m" \
                 "Standard user load"
        
        run_test "concurrency_check" "load_tests/scenarios.py" 30 5 "2m" \
                 "Concurrency and race conditions"
        
        run_test "stress_test" "load_tests/locustfile.py" 100 10 "5m" \
                 "System stress test"
        
        echo -e "\n${GREEN}🎉 Complete test suite finished!${NC}"
        echo -e "${BLUE}Check $RESULTS_DIR for detailed results${NC}"
        ;;
    
    "clean")
        echo -e "${YELLOW}Cleaning up old test results...${NC}"
        rm -rf "$RESULTS_DIR"
        echo -e "${GREEN}✅ Cleaned up test results${NC}"
        ;;
    
    "help"|*)
        echo -e "${BLUE}Load Testing Script Usage:${NC}"
        echo -e ""
        echo -e "${YELLOW}Quick Tests:${NC}"
        echo -e "  ./scripts/run_load_tests.sh quick       - Light load (10 users, 2min)"
        echo -e "  ./scripts/run_load_tests.sh standard    - Normal load (50 users, 5min)"
        echo -e "  ./scripts/run_load_tests.sh stress      - Heavy load (200 users, 10min)"
        echo -e ""
        echo -e "${YELLOW}Specialized Tests:${NC}"
        echo -e "  ./scripts/run_load_tests.sh concurrency - Test concurrent access"
        echo -e "  ./scripts/run_load_tests.sh race        - Test race conditions"
        echo -e "  ./scripts/run_load_tests.sh endurance   - Long-running stability test"
        echo -e "  ./scripts/run_load_tests.sh spike       - Sudden traffic spike test"
        echo -e ""
        echo -e "${YELLOW}Other Options:${NC}"
        echo -e "  ./scripts/run_load_tests.sh interactive - Start Locust web UI"
        echo -e "  ./scripts/run_load_tests.sh all         - Run complete test suite"
        echo -e "  ./scripts/run_load_tests.sh clean       - Clean up test results"
        echo -e "  ./scripts/run_load_tests.sh help        - Show this help"
        echo -e ""
        echo -e "${BLUE}Examples:${NC}"
        echo -e "  # Quick smoke test"
        echo -e "  ./scripts/run_load_tests.sh quick"
        echo -e ""
        echo -e "  # Interactive testing with web UI"
        echo -e "  ./scripts/run_load_tests.sh interactive"
        echo -e ""
        echo -e "  # Complete test suite"
        echo -e "  ./scripts/run_load_tests.sh all"
        echo -e ""
        echo -e "${YELLOW}Prerequisites:${NC}"
        echo -e "  1. API must be running: python run_api.py"
        echo -e "  2. Locust must be installed: poetry install"
        echo -e ""
        echo -e "${BLUE}Results will be saved to: $RESULTS_DIR/${NC}"
        ;;
esac

#!/bin/bash

# Deployment script for Render.com
# This script helps prepare and deploy the Orders & Inventory API

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Orders & Inventory API - Render.com Deployment${NC}"
echo -e "${BLUE}=================================================${NC}"

# Function to check prerequisites
check_prerequisites() {
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"
    
    # Check if git is available
    if ! command -v git &> /dev/null; then
        echo -e "${RED}❌ Git is not installed${NC}"
        exit 1
    fi
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${RED}❌ Not in a git repository${NC}"
        exit 1
    fi
    
    # Check if we have uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        echo -e "${YELLOW}⚠️  You have uncommitted changes${NC}"
        echo -e "${YELLOW}It's recommended to commit all changes before deployment${NC}"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Function to validate deployment files
validate_deployment_files() {
    echo -e "\n${YELLOW}Validating deployment files...${NC}"
    
    # Check for required files
    required_files=("render.yaml" "requirements.txt" "src/orders_inventory/api/main.py")
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            echo -e "${RED}❌ Missing required file: $file${NC}"
            exit 1
        fi
        echo -e "${GREEN}✅ Found: $file${NC}"
    done
    
    # Validate render.yaml syntax
    if command -v python &> /dev/null; then
        python -c "
import yaml
try:
    with open('render.yaml', 'r') as f:
        yaml.safe_load(f)
    print('✅ render.yaml syntax is valid')
except Exception as e:
    print(f'❌ render.yaml syntax error: {e}')
    exit(1)
        " || exit 1
    fi
    
    echo -e "${GREEN}✅ Deployment files validation passed${NC}"
}

# Function to test local API
test_local_api() {
    echo -e "\n${YELLOW}Testing local API...${NC}"
    
    # Check if API is running locally
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✅ Local API is running and healthy${NC}"
        
        # Test a simple endpoint
        echo -e "${BLUE}Testing product creation locally...${NC}"
        response=$(curl -s -X POST "http://localhost:8000/products/" \
                       -H "Content-Type: application/json" \
                       -d '{
                         "sku": "TEST-DEPLOY-001",
                         "name": "Deployment Test Product",
                         "price": 99.99,
                         "stock": 50
                       }')
        
        if echo "$response" | grep -q '"id"'; then
            echo -e "${GREEN}✅ Local API product creation works${NC}"
        else
            echo -e "${YELLOW}⚠️  Local API test failed, but continuing...${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Local API not running (this is optional)${NC}"
        echo -e "${BLUE}To test locally: python run_api.py${NC}"
    fi
}

# Function to prepare for deployment
prepare_deployment() {
    echo -e "\n${YELLOW}Preparing for deployment...${NC}"
    
    # Ensure we're on the main branch
    current_branch=$(git branch --show-current)
    if [[ "$current_branch" != "main" ]]; then
        echo -e "${YELLOW}⚠️  You're on branch '$current_branch', not 'main'${NC}"
        read -p "Continue with current branch? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${BLUE}Switch to main branch: git checkout main${NC}"
            exit 1
        fi
    fi
    
    # Show current commit
    current_commit=$(git rev-parse --short HEAD)
    echo -e "${BLUE}Current commit: $current_commit${NC}"
    
    # Show deployment configuration
    echo -e "\n${BLUE}Deployment Configuration:${NC}"
    echo -e "  📁 Config file: render.yaml"
    echo -e "  🐍 Python version: $(grep -A 5 "envVars:" render.yaml | grep "PYTHON_VERSION" -A 1 | tail -1 | sed 's/.*value: //')"
    echo -e "  🗄️  Database: $(grep -A 5 "envVars:" render.yaml | grep "DATABASE_URL" -A 1 | tail -1 | sed 's/.*value: //')"
    echo -e "  🌐 Environment: $(grep -A 5 "envVars:" render.yaml | grep "ENVIRONMENT" -A 1 | tail -1 | sed 's/.*value: //')"
    
    echo -e "${GREEN}✅ Deployment preparation complete${NC}"
}

# Function to commit and push changes
commit_and_push() {
    echo -e "\n${YELLOW}Committing and pushing changes...${NC}"
    
    # Check if there are any changes to commit
    if git diff-index --quiet HEAD --; then
        echo -e "${BLUE}No changes to commit${NC}"
    else
        echo -e "${BLUE}Committing deployment configuration...${NC}"
        git add .
        git commit -m "feat: Add Render.com deployment configuration

- Add render.yaml for Infrastructure as Code deployment
- Configure production environment variables
- Add requirements.txt for production dependencies
- Update CORS configuration for production
- Add comprehensive deployment documentation"
        
        echo -e "${GREEN}✅ Changes committed${NC}"
    fi
    
    # Push to origin
    echo -e "${BLUE}Pushing to remote repository...${NC}"
    git push origin $(git branch --show-current)
    echo -e "${GREEN}✅ Pushed to remote repository${NC}"
}

# Function to provide deployment instructions
show_deployment_instructions() {
    echo -e "\n${GREEN}🎉 Ready for Render.com deployment!${NC}"
    echo -e "\n${BLUE}Next Steps:${NC}"
    echo -e "1. ${YELLOW}Go to https://render.com${NC}"
    echo -e "2. ${YELLOW}Click 'New +' → 'Blueprint'${NC}"
    echo -e "3. ${YELLOW}Connect your GitHub repository${NC}"
    echo -e "4. ${YELLOW}Render will automatically detect render.yaml${NC}"
    echo -e "5. ${YELLOW}Review the configuration and click 'Apply'${NC}"
    
    echo -e "\n${BLUE}Expected Build Process:${NC}"
    echo -e "  🔨 Build Command: pip install poetry && poetry config virtualenvs.create false && poetry install --only=main"
    echo -e "  🚀 Start Command: uvicorn src.orders_inventory.api.main:app --host 0.0.0.0 --port \$PORT"
    echo -e "  ⏱️  Build Time: ~2-3 minutes"
    
    echo -e "\n${BLUE}After Deployment:${NC}"
    echo -e "  📄 API Docs: https://your-service-url.onrender.com/docs"
    echo -e "  💓 Health Check: https://your-service-url.onrender.com/health"
    echo -e "  📊 Summary: https://your-service-url.onrender.com/summary"
    
    echo -e "\n${BLUE}Test Your Deployment:${NC}"
    echo -e "  curl https://your-service-url.onrender.com/health"
    
    echo -e "\n${GREEN}📚 For detailed instructions, see: DEPLOYMENT.md${NC}"
}

# Main execution
case "${1:-deploy}" in
    "check")
        check_prerequisites
        validate_deployment_files
        test_local_api
        echo -e "\n${GREEN}✅ All checks passed! Ready for deployment.${NC}"
        ;;
    
    "prepare")
        check_prerequisites
        validate_deployment_files
        prepare_deployment
        ;;
    
    "deploy")
        check_prerequisites
        validate_deployment_files
        test_local_api
        prepare_deployment
        commit_and_push
        show_deployment_instructions
        ;;
    
    "help"|*)
        echo -e "${BLUE}Render.com Deployment Script Usage:${NC}"
        echo -e ""
        echo -e "${YELLOW}Commands:${NC}"
        echo -e "  ./scripts/deploy_to_render.sh check     - Run pre-deployment checks"
        echo -e "  ./scripts/deploy_to_render.sh prepare   - Prepare for deployment (no git operations)"
        echo -e "  ./scripts/deploy_to_render.sh deploy    - Full deployment preparation (default)"
        echo -e "  ./scripts/deploy_to_render.sh help      - Show this help"
        echo -e ""
        echo -e "${YELLOW}What this script does:${NC}"
        echo -e "  ✅ Validates all deployment files exist"
        echo -e "  ✅ Checks render.yaml syntax"
        echo -e "  ✅ Tests local API (if running)"
        echo -e "  ✅ Commits and pushes deployment configuration"
        echo -e "  ✅ Provides next steps for Render.com"
        echo -e ""
        echo -e "${YELLOW}Prerequisites:${NC}"
        echo -e "  📁 Git repository with remote origin"
        echo -e "  📄 render.yaml configuration file"
        echo -e "  📦 requirements.txt with dependencies"
        echo -e "  🐍 Python FastAPI application"
        echo -e ""
        echo -e "${BLUE}After running this script, go to render.com to complete deployment${NC}"
        ;;
esac

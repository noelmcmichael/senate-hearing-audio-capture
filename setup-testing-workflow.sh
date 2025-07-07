#!/bin/bash

# Setup Testing Workflow for Senate Hearing Audio Capture
# This script sets up pre-commit hooks and testing infrastructure

echo "🎭 Setting up Playwright Testing Workflow..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Must be run from project root directory"
    exit 1
fi

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    pip3 install pre-commit
fi

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
pre-commit install

# Test the setup
echo "🧪 Testing pre-commit hook setup..."
pre-commit run --all-files --verbose

# Check if Playwright is installed
if [ ! -d "node_modules/playwright" ]; then
    echo "📦 Installing Playwright..."
    npm install
    npx playwright install
fi

# Create test runner script if it doesn't exist
if [ ! -f "test-workflow.sh" ]; then
    echo "📝 Creating test workflow script..."
    cat > test-workflow.sh << 'EOF'
#!/bin/bash
# Test workflow runner
echo "🚀 Running test workflow..."

# Run quick system check
echo "🔍 Quick system check..."
node quick-system-check.js

# Run comprehensive tests
echo "🎭 Running comprehensive tests..."
node run-tests.js

# Show results
echo "📊 Test results ready in playwright-results/"
EOF
    chmod +x test-workflow.sh
fi

echo "✅ Testing workflow setup complete!"
echo ""
echo "📋 Usage:"
echo "  ./test-workflow.sh          # Run all tests"
echo "  node run-tests.js           # Run comprehensive tests"
echo "  node quick-system-check.js  # Quick system validation"
echo ""
echo "🔧 Pre-commit hooks installed - tests will run automatically on commits"
echo "🚀 GitHub Actions workflow configured for CI/CD"
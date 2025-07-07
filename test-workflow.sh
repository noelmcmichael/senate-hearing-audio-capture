#!/bin/bash

# Test workflow runner for Senate Hearing Audio Capture
# This script runs the complete test suite with proper error handling

set -e  # Exit on any error

echo "🚀 Running Senate Hearing Audio Capture Test Workflow..."
echo "================================================"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Must be run from project root directory"
    exit 1
fi

# Check if servers are running
echo "🏥 Checking server health..."

# Check frontend
if ! curl -f http://localhost:3000 >/dev/null 2>&1; then
    echo "⚠️  Frontend server not running. Please start with: cd dashboard && npm start"
    echo "   Continuing with quick system check only..."
    SKIP_COMPREHENSIVE=true
fi

# Check backend
if ! curl -f http://localhost:8001/api/health >/dev/null 2>&1; then
    echo "⚠️  Backend server not running. Please start with: python simple_api_server.py"
    echo "   Continuing with quick system check only..."
    SKIP_COMPREHENSIVE=true
fi

# Run quick system check (works without servers)
echo ""
echo "🔍 Running Quick System Check..."
echo "================================"
if [ -f "quick-system-check.js" ]; then
    node quick-system-check.js || echo "⚠️  Quick system check had issues"
else
    echo "⚠️  quick-system-check.js not found"
fi

# Run comprehensive tests (requires servers)
if [ "$SKIP_COMPREHENSIVE" != "true" ]; then
    echo ""
    echo "🎭 Running Comprehensive Tests..."
    echo "================================"
    if [ -f "run-tests.js" ]; then
        node run-tests.js
    else
        echo "❌ run-tests.js not found"
        exit 1
    fi
else
    echo ""
    echo "⚠️  Skipping comprehensive tests - servers not running"
    echo "To run full test suite:"
    echo "  1. Start backend: python simple_api_server.py"
    echo "  2. Start frontend: cd dashboard && npm start"
    echo "  3. Run: ./test-workflow.sh"
fi

# Show results
echo ""
echo "📊 Test Results..."
echo "=================="
if [ -d "playwright-results" ]; then
    echo "📁 Results saved to: playwright-results/"
    
    if [ -f "playwright-results/test_summary.json" ]; then
        echo "📄 Test Summary:"
        cat playwright-results/test_summary.json | python3 -m json.tool
    fi
    
    if [ -f "playwright-results/test_report.html" ]; then
        echo "📄 HTML Report: playwright-results/test_report.html"
    fi
else
    echo "⚠️  No results directory found"
fi

echo ""
echo "✅ Test workflow complete!"
#!/usr/bin/env node

/**
 * Test ID Audit Script
 * Scans React components for missing data-testid attributes
 */

const fs = require('fs');
const path = require('path');

const DASHBOARD_SRC = path.join(__dirname, 'dashboard', 'src');
const CRITICAL_ELEMENTS = [
  'button',
  'input',
  'select',
  'textarea',
  'form',
  'Link',
  'div.*className.*["\'].*card.*["\']',
  'div.*className.*["\'].*container.*["\']',
  'div.*className.*["\'].*header.*["\']',
  'div.*className.*["\'].*footer.*["\']',
  'nav',
  'table',
  'Modal',
  'Dialog'
];

const INTERACTIVE_PATTERNS = [
  /onClick/g,
  /onSubmit/g,
  /onChange/g,
  /onFocus/g,
  /onBlur/g,
  /href=/g
];

function scanDirectory(dir) {
  const results = [];
  
  if (!fs.existsSync(dir)) {
    console.log(`Directory ${dir} does not exist`);
    return results;
  }
  
  const files = fs.readdirSync(dir);
  
  for (const file of files) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory()) {
      results.push(...scanDirectory(filePath));
    } else if (file.endsWith('.js') || file.endsWith('.jsx')) {
      const fileResults = scanFile(filePath);
      if (fileResults.length > 0) {
        results.push({
          file: path.relative(DASHBOARD_SRC, filePath),
          issues: fileResults
        });
      }
    }
  }
  
  return results;
}

function scanFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const lines = content.split('\n');
  const issues = [];
  
  lines.forEach((line, index) => {
    const lineNumber = index + 1;
    
    // Check for critical elements without data-testid
    CRITICAL_ELEMENTS.forEach(element => {
      const regex = new RegExp(`<${element}(?![^>]*data-testid)`, 'gi');
      const matches = line.match(regex);
      
      if (matches) {
        matches.forEach(match => {
          issues.push({
            type: 'missing-testid',
            line: lineNumber,
            element: match,
            suggestion: `Add data-testid attribute to ${element}`
          });
        });
      }
    });
    
    // Check for interactive elements without data-testid
    INTERACTIVE_PATTERNS.forEach(pattern => {
      if (pattern.test(line) && !line.includes('data-testid')) {
        issues.push({
          type: 'interactive-no-testid',
          line: lineNumber,
          element: line.trim(),
          suggestion: 'Add data-testid to interactive element'
        });
      }
    });
  });
  
  return issues;
}

function generateTestIdSuggestions(fileName, element) {
  const baseName = path.basename(fileName, '.js').toLowerCase();
  const elementType = element.toLowerCase().replace(/[<>]/g, '');
  
  // Generate contextual test IDs
  const suggestions = [
    `${baseName}-${elementType}`,
    `${baseName}-${elementType}-primary`,
    `${baseName}-${elementType}-secondary`,
    `${elementType}-${baseName}`
  ];
  
  return suggestions;
}

function generateReport(results) {
  console.log('\n🔍 Test ID Audit Report');
  console.log('=====================\n');
  
  let totalIssues = 0;
  let totalFiles = results.length;
  
  if (totalFiles === 0) {
    console.log('✅ No React components found or no issues detected');
    return;
  }
  
  results.forEach(fileResult => {
    const issueCount = fileResult.issues.length;
    totalIssues += issueCount;
    
    console.log(`📄 ${fileResult.file} (${issueCount} issues)`);
    console.log('─'.repeat(50));
    
    fileResult.issues.forEach(issue => {
      console.log(`  Line ${issue.line}: ${issue.type}`);
      console.log(`    Element: ${issue.element}`);
      console.log(`    Suggestion: ${issue.suggestion}`);
      
      if (issue.type === 'missing-testid') {
        const suggestions = generateTestIdSuggestions(fileResult.file, issue.element);
        console.log(`    Suggested IDs: ${suggestions.join(', ')}`);
      }
      
      console.log('');
    });
  });
  
  console.log(`\n📊 Summary:`);
  console.log(`   Files scanned: ${totalFiles}`);
  console.log(`   Issues found: ${totalIssues}`);
  console.log(`   Average issues per file: ${(totalIssues / totalFiles).toFixed(1)}`);
  
  if (totalIssues > 0) {
    console.log('\n🎯 Priority Actions:');
    console.log('   1. Add data-testid attributes to critical UI elements');
    console.log('   2. Focus on interactive elements (buttons, forms, links)');
    console.log('   3. Use consistent naming conventions (component-element-purpose)');
    console.log('   4. Update Playwright tests to use data-testid selectors');
  }
}

function main() {
  console.log('🔍 Starting Test ID Audit...');
  console.log(`📁 Scanning directory: ${DASHBOARD_SRC}`);
  
  const results = scanDirectory(DASHBOARD_SRC);
  generateReport(results);
  
  // Save detailed report
  const reportPath = path.join(__dirname, 'test-id-audit-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));
  console.log(`\n📄 Detailed report saved to: ${reportPath}`);
}

if (require.main === module) {
  main();
}

module.exports = { scanDirectory, scanFile, generateReport };
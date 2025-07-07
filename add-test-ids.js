#!/usr/bin/env node

/**
 * Add Test IDs Script
 * Adds data-testid attributes to critical UI elements
 */

const fs = require('fs');
const path = require('path');

const DASHBOARD_FILE = path.join(__dirname, 'dashboard', 'src', 'pages', 'Dashboard.js');

function addTestIdsToDashboard() {
  console.log('📝 Adding test IDs to Dashboard.js...');
  
  if (!fs.existsSync(DASHBOARD_FILE)) {
    console.error('❌ Dashboard.js not found');
    return;
  }
  
  let content = fs.readFileSync(DASHBOARD_FILE, 'utf8');
  
  // Add test IDs to search input
  content = content.replace(
    /<input\s+type="text"\s+placeholder="Search hearings..."/,
    '<input\n              data-testid="search-input"\n              type="text"\n              placeholder="Search hearings..."'
  );
  
  // Add test ID to filter toggle button
  content = content.replace(
    /<button\s+onClick=\{\(\) => setShowFilters\(!showFilters\)\}/,
    '<button\n            data-testid="filter-toggle"\n            onClick={() => setShowFilters(!showFilters)}'
  );
  
  // Add test ID to sort select
  content = content.replace(
    /<select\s+value=\{sortBy\}\s+onChange=\{\(e\) => setSortBy\(e\.target\.value\)\}/,
    '<select\n              data-testid="sort-select"\n              value={sortBy}\n              onChange={(e) => setSortBy(e.target.value)}'
  );
  
  // Add test ID to sort order button
  content = content.replace(
    /<button\s+onClick=\{\(\) => setSortOrder\(sortOrder === 'asc' \? 'desc' : 'asc'\)\}/,
    '<button\n              data-testid="sort-order-toggle"\n              onClick={() => setSortOrder(sortOrder === \'asc\' ? \'desc\' : \'asc\')}'
  );
  
  // Add test ID to clear filters button
  content = content.replace(
    /<button\s+onClick=\{clearFilters\}/,
    '<button\n                  data-testid="clear-filters"\n                  onClick={clearFilters}'
  );
  
  // Add test ID to hearing cards
  content = content.replace(
    /<div\s+key=\{hearing\.id\}\s+onClick=\{\(\) => handleHearingClick\(hearing\)\}/,
    '<div\n              data-testid={`hearing-card-${hearing.id}`}\n              key={hearing.id}\n              onClick={() => handleHearingClick(hearing)}'
  );
  
  // Add test ID to status filter select
  content = content.replace(
    /<select\s+value=\{statusFilter\}\s+onChange=\{\(e\) => setStatusFilter\(e\.target\.value\)\}/,
    '<select\n                  data-testid="status-filter"\n                  value={statusFilter}\n                  onChange={(e) => setStatusFilter(e.target.value)}'
  );
  
  // Add test IDs to committee filter buttons
  content = content.replace(
    /<button\s+key=\{committee\.code\}\s+onClick=\{\(\) => toggleCommitteeFilter\(committee\.code\)\}/,
    '<button\n                      data-testid={`committee-filter-${committee.code}`}\n                      key={committee.code}\n                      onClick={() => toggleCommitteeFilter(committee.code)}'
  );
  
  fs.writeFileSync(DASHBOARD_FILE, content);
  console.log('✅ Test IDs added to Dashboard.js');
}

function addTestIdsToTranscriptComponent() {
  const transcriptFile = path.join(__dirname, 'dashboard', 'src', 'pages', 'HearingTranscript.js');
  
  if (!fs.existsSync(transcriptFile)) {
    console.log('⚠️  HearingTranscript.js not found, skipping...');
    return;
  }
  
  console.log('📝 Adding test IDs to HearingTranscript.js...');
  
  let content = fs.readFileSync(transcriptFile, 'utf8');
  
  // Add test ID to back button
  content = content.replace(
    /<button\s+onClick=\{handleBack\}/,
    '<button\n            data-testid="back-button"\n            onClick={handleBack}'
  );
  
  // Add test ID to export transcript button
  content = content.replace(
    /<button\s+onClick=\{handleExportTranscript\}/,
    '<button\n            data-testid="export-transcript-button"\n            onClick={handleExportTranscript}'
  );
  
  // Add test ID to export text button
  content = content.replace(
    /<button\s+onClick=\{handleExportText\}/,
    '<button\n            data-testid="export-text-button"\n            onClick={handleExportText}'
  );
  
  // Add test ID to export CSV button
  content = content.replace(
    /<button\s+onClick=\{handleExportCSV\}/,
    '<button\n            data-testid="export-csv-button"\n            onClick={handleExportCSV}'
  );
  
  // Add test ID to export summary button
  content = content.replace(
    /<button\s+onClick=\{handleExportSummaryReport\}/,
    '<button\n            data-testid="export-summary-button"\n            onClick={handleExportSummaryReport}'
  );
  
  // Add test ID to transcript table
  content = content.replace(
    /<Table\s+striped\s+bordered\s+hover\s+variant="dark"/,
    '<Table\n                data-testid="transcript-table"\n                striped\n                bordered\n                hover\n                variant="dark"'
  );
  
  fs.writeFileSync(transcriptFile, content);
  console.log('✅ Test IDs added to HearingTranscript.js');
}

function createTestIdConventions() {
  const conventionsFile = path.join(__dirname, 'TEST_ID_CONVENTIONS.md');
  
  const conventions = `# Test ID Conventions

## Naming Pattern
Format: \`{component}-{element}-{purpose}\`

## Examples

### Dashboard Component
- \`search-input\` - Search input field
- \`filter-toggle\` - Filter toggle button
- \`sort-select\` - Sort dropdown
- \`sort-order-toggle\` - Sort order toggle
- \`clear-filters\` - Clear filters button
- \`hearing-card-{id}\` - Individual hearing cards
- \`committee-filter-{code}\` - Committee filter buttons
- \`status-filter\` - Status filter dropdown

### Transcript Component
- \`back-button\` - Back navigation button
- \`export-transcript-button\` - Export transcript button
- \`export-text-button\` - Export text button
- \`export-csv-button\` - Export CSV button
- \`export-summary-button\` - Export summary button
- \`transcript-table\` - Main transcript table

### General Rules
1. Use kebab-case (lowercase with hyphens)
2. Be descriptive but concise
3. Include component context for uniqueness
4. Use consistent terminology across components
5. Add IDs to all interactive elements

### Priority Elements
1. **Buttons** - All clickable buttons
2. **Forms** - Input fields, selects, textareas
3. **Navigation** - Links, menu items
4. **Tables** - Data tables and key rows
5. **Cards** - Clickable cards or containers
6. **Modals** - Dialog boxes and overlays

## Usage in Tests
\`\`\`javascript
// Good - using data-testid
await page.locator('[data-testid="search-input"]').fill('search term');
await page.locator('[data-testid="filter-toggle"]').click();
await page.locator('[data-testid="hearing-card-123"]').click();

// Avoid - using CSS classes or complex selectors
await page.locator('.search-input').fill('search term');
await page.locator('button:has-text("Filters")').click();
\`\`\`
`;
  
  fs.writeFileSync(conventionsFile, conventions);
  console.log('✅ Test ID conventions created');
}

function main() {
  console.log('🚀 Adding Test IDs to Critical Components...');
  
  // Create backup
  const backupDir = path.join(__dirname, 'backup_before_testids');
  if (!fs.existsSync(backupDir)) {
    fs.mkdirSync(backupDir);
  }
  
  if (fs.existsSync(DASHBOARD_FILE)) {
    fs.copyFileSync(DASHBOARD_FILE, path.join(backupDir, 'Dashboard.js'));
  }
  
  // Add test IDs
  addTestIdsToDashboard();
  addTestIdsToTranscriptComponent();
  createTestIdConventions();
  
  console.log('\n✅ Test ID addition complete!');
  console.log('📋 Next steps:');
  console.log('   1. Update Playwright tests to use data-testid selectors');
  console.log('   2. Test the changes in development');
  console.log('   3. Run test suite to verify improvements');
}

if (require.main === module) {
  main();
}

module.exports = { addTestIdsToDashboard, addTestIdsToTranscriptComponent };
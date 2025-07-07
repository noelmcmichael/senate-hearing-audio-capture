# Test ID Conventions

## Naming Pattern
Format: `{component}-{element}-{purpose}`

## Examples

### Dashboard Component
- `search-input` - Search input field
- `filter-toggle` - Filter toggle button
- `sort-select` - Sort dropdown
- `sort-order-toggle` - Sort order toggle
- `clear-filters` - Clear filters button
- `hearing-card-{id}` - Individual hearing cards
- `committee-filter-{code}` - Committee filter buttons
- `status-filter` - Status filter dropdown

### Transcript Component
- `back-button` - Back navigation button
- `export-transcript-button` - Export transcript button
- `export-text-button` - Export text button
- `export-csv-button` - Export CSV button
- `export-summary-button` - Export summary button
- `transcript-table` - Main transcript table

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
```javascript
// Good - using data-testid
await page.locator('[data-testid="search-input"]').fill('search term');
await page.locator('[data-testid="filter-toggle"]').click();
await page.locator('[data-testid="hearing-card-123"]').click();

// Avoid - using CSS classes or complex selectors
await page.locator('.search-input').fill('search term');
await page.locator('button:has-text("Filters")').click();
```

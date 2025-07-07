const { chromium } = require('playwright');

/**
 * Quick system state check to validate our understanding
 * This will help us understand the current routing and component structure
 */

async function quickSystemCheck() {
  console.log('🔍 Quick System State Check...');
  
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('📡 Testing server connectivity...');
  
  // Test backend
  try {
    const backendResponse = await fetch('http://localhost:8001/api/health');
    console.log('✅ Backend healthy:', backendResponse.status);
  } catch (error) {
    console.error('❌ Backend error:', error.message);
  }

  // Test frontend routes
  const routes = [
    { url: 'http://localhost:3000/', name: 'Dashboard' },
    { url: 'http://localhost:3000/hearings/12', name: 'Hearing 12 (Transcript)' },
    { url: 'http://localhost:3000/hearings/12/status', name: 'Hearing 12 Status' },
    { url: 'http://localhost:3000/discovery', name: 'Discovery Dashboard' }
  ];

  for (const route of routes) {
    try {
      console.log(`\n📄 Testing route: ${route.name}`);
      await page.goto(route.url);
      await page.waitForTimeout(3000);
      
      const pageInfo = await page.evaluate(() => {
        return {
          title: document.title,
          url: window.location.href,
          bodyText: document.body.innerText.substring(0, 200),
          hasError: document.body.innerText.toLowerCase().includes('error'),
          hasLoading: document.body.innerText.toLowerCase().includes('loading'),
          elementCount: document.querySelectorAll('*').length
        };
      });
      
      console.log(`   URL: ${pageInfo.url}`);
      console.log(`   Title: ${pageInfo.title}`);
      console.log(`   Elements: ${pageInfo.elementCount}`);
      console.log(`   Has Error: ${pageInfo.hasError}`);
      console.log(`   Preview: ${pageInfo.bodyText.replace(/\n/g, ' ')}`);
      
      if (pageInfo.hasError) {
        console.warn('⚠️ Error detected on page');
      }
      
    } catch (error) {
      console.error(`❌ Route ${route.name} failed:`, error.message);
    }
  }

  // Test API endpoints
  console.log('\n🌐 Testing API endpoints...');
  const apiEndpoints = [
    'http://localhost:8001/api/hearings',
    'http://localhost:8001/api/hearings/12',
    'http://localhost:8001/api/hearings/12/transcript'
  ];

  for (const endpoint of apiEndpoints) {
    try {
      await page.goto(endpoint);
      await page.waitForTimeout(1000);
      
      const responseText = await page.evaluate(() => document.body.textContent);
      console.log(`✅ ${endpoint}: ${responseText.length} chars`);
      
      if (responseText.includes('error') || responseText.includes('404')) {
        console.warn(`⚠️ Potential error in ${endpoint}`);
      }
      
    } catch (error) {
      console.error(`❌ API endpoint ${endpoint} failed:`, error.message);
    }
  }

  await browser.close();
  console.log('\n✅ Quick system check complete');
}

quickSystemCheck().catch(error => {
  console.error('System check failed:', error);
  process.exit(1);
});
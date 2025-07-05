#!/usr/bin/env python3
"""
Test Chrome/Docker functionality for Milestone 5.1
Verifies Chrome browser works correctly in Docker container
"""

import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_chrome_installation():
    """Test if Chrome is properly installed"""
    try:
        import subprocess
        
        # Check if Google Chrome is installed
        result = subprocess.run(['google-chrome', '--version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            logger.info(f"✅ Chrome installed: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"❌ Chrome not found: {result.stderr}")
            return False
            
    except FileNotFoundError:
        logger.error("❌ Chrome binary not found")
        return False
    except Exception as e:
        logger.error(f"❌ Chrome test failed: {e}")
        return False

def test_playwright_chromium():
    """Test Playwright Chromium functionality"""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # Test browser launch
            browser = p.chromium.launch(headless=True)
            logger.info("✅ Playwright Chromium launched successfully")
            
            # Test page creation
            page = browser.new_page()
            logger.info("✅ Playwright page created successfully")
            
            # Test navigation to a simple page
            page.goto("https://httpbin.org/get")
            title = page.title()
            logger.info(f"✅ Page navigation successful: {title}")
            
            browser.close()
            return True
            
    except Exception as e:
        logger.error(f"❌ Playwright Chromium test failed: {e}")
        return False

def test_page_inspector():
    """Test our custom PageInspector class"""
    try:
        sys.path.append(str(Path(__file__).parent))
        from src.utils.page_inspector import PageInspector
        
        with PageInspector(headless=True) as inspector:
            logger.info("✅ PageInspector initialized successfully")
            
            # Test with a simple webpage
            result = inspector.analyze_page("https://httpbin.org/html")
            logger.info(f"✅ PageInspector analysis successful: {len(result)} results")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ PageInspector test failed: {e}")
        return False

def test_isvp_extractor():
    """Test ISVP extractor functionality"""
    try:
        # Import path fix
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir / "src"))
        from extractors.isvp_extractor import ISVPExtractor
        
        extractor = ISVPExtractor()
        logger.info("✅ ISVPExtractor initialized successfully")
        
        # Test URL recognition
        test_urls = [
            "https://www.commerce.senate.gov/2025/6/executive-session-12",
            "https://www.judiciary.senate.gov/hearing",
            "https://www.banking.senate.gov/hearings"
        ]
        
        compatible_urls = 0
        for url in test_urls:
            if extractor.can_extract(url):
                compatible_urls += 1
                logger.info(f"✅ URL compatible: {url}")
            else:
                logger.info(f"⚠️  URL not compatible: {url}")
        
        logger.info(f"✅ ISVP URL compatibility: {compatible_urls}/{len(test_urls)} URLs")
        return True
        
    except Exception as e:
        logger.error(f"❌ ISVP extractor test failed: {e}")
        return False

def test_audio_capture_dependencies():
    """Test audio capture dependencies"""
    try:
        # Test FFmpeg
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("✅ FFmpeg available")
        else:
            logger.error("❌ FFmpeg not available")
            return False
        
        # Test audio libraries
        try:
            import wave
            logger.info("✅ Wave library available")
        except ImportError:
            logger.error("❌ Wave library not available")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Audio dependencies test failed: {e}")
        return False

def test_chrome_headless_audio():
    """Test Chrome headless mode with audio capture simulation"""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # Launch with audio support
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--allow-running-insecure-content',
                    '--autoplay-policy=no-user-gesture-required'
                ]
            )
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            
            page = context.new_page()
            
            # Test loading a page with media
            page.goto("https://www.w3schools.com/html/html5_audio.html", timeout=30000)
            logger.info("✅ Chrome headless with media page loaded")
            
            # Check for audio/video elements
            audio_elements = page.query_selector_all('audio')
            video_elements = page.query_selector_all('video')
            
            logger.info(f"✅ Media elements found: {len(audio_elements)} audio, {len(video_elements)} video")
            
            browser.close()
            return True
            
    except Exception as e:
        logger.error(f"❌ Chrome headless audio test failed: {e}")
        return False

def run_chrome_docker_tests():
    """Run all Chrome/Docker tests"""
    logger.info("=" * 60)
    logger.info("MILESTONE 5.1: Chrome/Docker Dependencies Test")
    logger.info("=" * 60)
    
    tests = [
        ("Chrome Installation", test_chrome_installation),
        ("Playwright Chromium", test_playwright_chromium),
        ("PageInspector", test_page_inspector),
        ("ISVP Extractor", test_isvp_extractor),
        ("Audio Dependencies", test_audio_capture_dependencies),
        ("Chrome Headless Audio", test_chrome_headless_audio)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running test: {test_name}")
        try:
            if test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} ERROR: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"CHROME/DOCKER TEST RESULTS: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    if passed == total:
        logger.info("🎉 ALL CHROME/DOCKER TESTS PASSED!")
        logger.info("✅ Step 5.1 Chrome/Docker Dependencies Fix is COMPLETE")
        return True
    else:
        logger.error(f"❌ {total - passed} tests failed")
        logger.info("💡 Chrome/Docker configuration needs adjustment")
        return False

if __name__ == "__main__":
    success = run_chrome_docker_tests()
    sys.exit(0 if success else 1)
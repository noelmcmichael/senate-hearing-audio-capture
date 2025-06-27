# Senate Hearing Audio Capture Agent

## Executive Summary
This project creates an automated agent to extract audio from U.S. Senate Committee hearings streamed through the Senate's proprietary ISVP (In-House Streaming Video Player) system. The goal is to enable programmatic access to hearing content for policy analysis, regulatory tracking, and civic engagement.

## Problem Statement
U.S. Senate Committee hearings are often streamed through embedded ISVP players on official committee web pages. These streams are not reliably archived on accessible platforms, creating friction for automated transcription and analysis workflows.

## Target
**Primary Test URL**: https://www.commerce.senate.gov/2025/6/executive-session-12
- Executive Session 12, June 25, 2025
- Contains both YouTube embed and ISVP player
- Duration: 44:42 minutes

## Project Structure
```
senate_hearing_audio_capture/
├── README.md                    # This file
├── rules.md                     # Project rules and conventions
├── src/                         # Source code
│   ├── __init__.py
│   ├── main.py                  # Primary entry point
│   ├── extractors/              # Stream extraction modules
│   │   ├── __init__.py
│   │   ├── base_extractor.py    # Base extractor interface  
│   │   ├── isvp_extractor.py    # ISVP-specific extraction
│   │   └── youtube_extractor.py # YouTube fallback extraction (planned)
│   ├── converters/              # Audio conversion modules
│   │   ├── __init__.py
│   │   └── ffmpeg_converter.py  # ffmpeg audio conversion
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       └── page_inspector.py    # Web page analysis
├── tests/                       # Test files
│   └── __init__.py
├── output/                      # Generated audio files
├── logs/                        # Application logs
├── capture.py                   # Main entry script  
├── analyze_target.py            # Page analysis utility
├── verify_audio.py              # Audio verification utility
├── requirements.txt             # Python dependencies
└── .gitignore                   # Git ignore patterns
```

## Current Status
- **Phase**: ✅ MVP Complete - Successfully extracted audio from target page
- **Last Updated**: 2025-06-27
- **Key Files Created**: README.md, rules.md, complete extraction pipeline
- **Test Results**: Successfully extracted 47-minute audio file (474MB WAV) from ISVP stream

## Dependencies
- Python 3.11+
- ffmpeg (for audio conversion)
- Browser automation tools (Playwright/Selenium)
- Requests/httpx for HTTP handling

## Usage
```bash
# Single page extraction (basic)
python capture.py --url "https://www.commerce.senate.gov/2025/6/executive-session-12"

# With custom options
python capture.py --url "URL" --output ./custom_output/ --format mp3 --quality medium --headless

# Verify extracted audio
python verify_audio.py
```

### Options
- `--url`: Senate hearing page URL (required)
- `--output`: Output directory (default: ./output)
- `--format`: Audio format - wav, mp3, flac (default: wav)
- `--quality`: Audio quality - low, medium, high (default: high)
- `--headless`: Run browser in headless mode

## Next Steps
1. ✅ Set up project structure and documentation
2. ✅ Analyze target page ISVP implementation
3. ✅ Build stream URL extraction  
4. ✅ Implement audio conversion pipeline
5. ✅ Add error handling and validation
6. ⏳ Generalize to other Senate committee pages
7. ⏳ Add YouTube fallback extraction
8. ⏳ Implement batch processing
9. ⏳ Add scheduling/monitoring capabilities
10. ⏳ Package as deployable service

## Notes
- This tool is intended for civic engagement and policy analysis
- Respects Senate terms of service and rate limiting
- Designed to be modular for future service deployment

---
*Generated with [Memex](https://memex.tech)*
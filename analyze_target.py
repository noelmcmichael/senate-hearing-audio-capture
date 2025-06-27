#!/usr/bin/env python3
"""
Quick analysis script for the target Senate hearing page.
This will help us understand the ISVP implementation.
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from utils.page_inspector import PageInspector


def main():
    target_url = "https://www.commerce.senate.gov/2025/6/executive-session-12"
    
    print(f"Analyzing target page: {target_url}")
    print("=" * 60)
    
    with PageInspector(headless=False) as inspector:
        analysis = inspector.analyze_page(target_url)
    
    # Pretty print the analysis
    print("\n📊 ANALYSIS RESULTS:")
    print("=" * 60)
    
    if 'error' in analysis:
        print(f"❌ Error: {analysis['error']}")
        return
    
    print(f"🎯 URL: {analysis['url']}")
    print(f"🎬 Players found: {len(analysis['players_found'])}")
    print(f"🌐 Network requests: {len(analysis['network_requests'])}")
    print(f"📜 JS variables: {len(analysis['javascript_variables'])}")
    print(f"🏗️  DOM elements: {len(analysis['dom_elements'])}")
    
    # Show players found
    if analysis['players_found']:
        print("\n🎬 PLAYERS FOUND:")
        for i, player in enumerate(analysis['players_found'], 1):
            print(f"  {i}. Type: {player['type']}")
            if player['type'] == 'youtube':
                print(f"      Video ID: {player.get('video_id', 'N/A')}")
                print(f"      Source: {player.get('src', 'N/A')}")
            elif player['type'] == 'isvp':
                print(f"      Elements: {len(player.get('elements', []))}")
                print(f"      Potential streams: {len(player.get('potential_streams', []))}")
    
    # Show network requests for media
    if analysis['network_requests']:
        print("\n🌐 MEDIA NETWORK REQUESTS:")
        for req in analysis['network_requests']:
            print(f"  • {req['method']} {req['url']}")
            print(f"    Type: {req['resource_type']}")
    
    # Show JavaScript variables
    if analysis['javascript_variables']:
        print("\n📜 JAVASCRIPT VARIABLES:")
        for var_name, value in analysis['javascript_variables'].items():
            print(f"  • {var_name}: {str(value)[:100]}...")
    
    # Show DOM elements
    if analysis['dom_elements']:
        print("\n🏗️  MEDIA DOM ELEMENTS:")
        for elem in analysis['dom_elements']:
            print(f"  • {elem['type']}")
            if elem.get('src'):
                print(f"    src: {elem['src']}")
            if elem.get('type'):
                print(f"    type: {elem['type']}")
    
    # Save detailed analysis to file
    output_file = Path('output') / 'page_analysis.json'
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n💾 Detailed analysis saved to: {output_file}")


if __name__ == "__main__":
    main()
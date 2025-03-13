#!/usr/bin/env python3
"""
Script to generate sample bird images for the dashboard.
This script creates SVG placeholder images with the bird names for each bird in the dashboard.
"""
import os
import json
import sys
from pathlib import Path

# Add parent directory to path to allow importing from parent modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def generate_svg_placeholder(bird_name, output_path, size=(400, 300), bg_color="#4A90E2", text_color="#FFFFFF"):
    """Generate a simple SVG placeholder for a bird image."""
    width, height = size
    
    svg_content = f"""
    <svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="{bg_color}"/>
        <text x="50%" y="50%" font-family="Arial" font-size="24" fill="{text_color}" 
              text-anchor="middle" dominant-baseline="middle">
            {bird_name}
        </text>
        <text x="50%" y="70%" font-family="Arial" font-size="16" fill="{text_color}" 
              text-anchor="middle" dominant-baseline="middle">
            Bird Image
        </text>
    </svg>
    """
    
    with open(output_path, 'w') as file:
        file.write(svg_content)
    
    print(f"Generated placeholder image for {bird_name} at {output_path}")

def main():
    """Main function to generate bird images."""
    # Path to mock data file
    mock_data_path = Path(__file__).parent.parent / 'docs' / 'mock-data.json'
    
    # Path to image directory
    img_dir = Path(__file__).parent.parent / 'dashboard' / 'static' / 'img'
    
    # Create directories if they don't exist
    img_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load mock data
        with open(mock_data_path, 'r') as file:
            mock_data = json.load(file)
        
        # Get birds data
        birds = mock_data.get('birds', {})
        
        # Generate image for each bird
        for bird_name, bird_data in birds.items():
            image_filename = bird_data.get('image')
            if image_filename:
                # Generate full size image
                full_path = img_dir / image_filename
                generate_svg_placeholder(bird_name, full_path)
                
                # Generate thumbnail (just create a copy for now)
                thumb_filename = image_filename.replace('_full', '_thumb')
                thumb_path = img_dir / thumb_filename
                generate_svg_placeholder(bird_name, thumb_path, size=(100, 100))
                
        print(f"Successfully generated {len(birds)} bird images.")
                
    except Exception as e:
        print(f"Error generating bird images: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
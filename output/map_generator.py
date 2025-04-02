#hotel_compset_analyzer/output/map_generator.py
"""
Map generator for the Hotel CompSet Analyzer.
Creates interactive maps of the subject hotel and competitor hotels.
"""

import os
import folium
from typing import Dict, List, Any, Optional
import logging

from data.hotel import Hotel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MapGenerator:
    """Map generator for the Hotel CompSet Analyzer."""
    
    def __init__(self, output_dir: str = "./output"):
        """
        Initialize the map generator.
        
        Args:
            output_dir: Directory where maps will be saved
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def create_map(self, subject_hotel: Hotel, competitor_hotels: List[Hotel], 
                  output_file: Optional[str] = None) -> Optional[str]:
        """
        Create an interactive map of the subject hotel and competitor hotels.
        
        Args:
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
            output_file: Path to save the output HTML file (optional)
            
        Returns:
            Path to the created map file or None if map could not be created
        """
        # Check if we have coordinates for the subject hotel
        if not subject_hotel.latitude or not subject_hotel.longitude:
            logger.warning("Subject hotel coordinates missing, cannot create map")
            return None
        
        # Set default output file if not provided
        if not output_file:
            output_file = os.path.join(self.output_dir, "hotel_map.html")
        
        try:
            # Center map on subject hotel
            subject_location = [subject_hotel.latitude, subject_hotel.longitude]
            m = folium.Map(location=subject_location, zoom_start=13)
            
            # Add subject hotel marker (yellow)
            popup_html = f"""
            <div style="width: 200px">
                <h4>{subject_hotel.name}</h4>
                <p><b>Address:</b> {subject_hotel.address}, {subject_hotel.city}, {subject_hotel.state}</p>
                <p><b>Brand:</b> {subject_hotel.brand_affiliation or 'Independent/Unknown'}</p>
                <p><b>Room Count:</b> {subject_hotel.room_count or 'Unknown'}</p>
            </div>
            """
            
            folium.Marker(
                location=subject_location,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=f"Subject: {subject_hotel.name}",
                icon=folium.Icon(color='orange', icon='home', prefix='fa')
            ).add_to(m)
            
            # Add competitor hotels markers (red)
            for hotel in competitor_hotels:
                if hotel.latitude and hotel.longitude:
                    distance_str = ""
                    if hotel.distance_from_subject is not None:
                        distance_str = f"<p><b>Distance:</b> {hotel.distance_from_subject:.2f} miles</p>"
                    
                    popup_html = f"""
                    <div style="width: 200px">
                        <h4>{hotel.name}</h4>
                        <p><b>Address:</b> {hotel.address}, {hotel.city}, {hotel.state}</p>
                        <p><b>Brand:</b> {hotel.brand_affiliation or 'Independent/Unknown'}</p>
                        <p><b>Room Count:</b> {hotel.room_count or 'Unknown'}</p>
                        {distance_str}
                    </div>
                    """
                    
                    folium.Marker(
                        location=[hotel.latitude, hotel.longitude],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=hotel.name,
                        icon=folium.Icon(color='red', icon='hotel', prefix='fa')
                    ).add_to(m)
            
            # Add distance circles (in meters)
            folium.Circle(
                location=subject_location,
                radius=804.672,  # 0.5 miles in meters
                color='#3186cc',
                fill=True,
                fill_color='#3186cc',
                fill_opacity=0.1,
                popup="0.5 mile radius"
            ).add_to(m)
            
            folium.Circle(
                location=subject_location,
                radius=1609.344,  # 1 mile in meters
                color='#3186cc',
                fill=True,
                fill_color='#3186cc',
                fill_opacity=0.05,
                popup="1 mile radius"
            ).add_to(m)
            
            # Add legend (in HTML)
            legend_html = """
            <div style="position: fixed; 
                        bottom: 50px; right: 50px; width: 200px; height: 120px; 
                        border:2px solid grey; z-index:9999; font-size:14px;
                        background-color: white; padding: 10px;
                        border-radius: 5px;">
                <p><b>Legend</b></p>
                <p>
                    <i class="fa fa-home" style="color: orange;"></i> Subject Hotel<br>
                    <i class="fa fa-hotel" style="color: red;"></i> Competitor Hotel<br>
                    <i class="fa fa-circle" style="color: #3186cc;"></i> Distance Radius
                </p>
            </div>
            """
            
            # Add legend to map
            m.get_root().html.add_child(folium.Element(legend_html))
            
            # Add title
            title_html = f"""
            <div style="position: fixed; 
                        top: 10px; left: 50%; transform: translateX(-50%); 
                        width: 400px; height: 50px; 
                        z-index:9999; font-size:16px;
                        background-color: white; padding: 10px;
                        border-radius: 5px; text-align: center;
                        border:2px solid grey;">
                <h3 style="margin: 0;">CompSet Map for {subject_hotel.name}</h3>
            </div>
            """
            
            # Add title to map
            m.get_root().html.add_child(folium.Element(title_html))
            
            # Save map to HTML file
            m.save(output_file)
            
            logger.info(f"Map created and saved to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error creating map: {e}")
            return None
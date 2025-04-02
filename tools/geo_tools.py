#hotel_compset_analyzer/tools/geo_tools.py
"""
Geographic tools for the Hotel CompSet Analyzer.
"""

import os
import json
import math
import requests
from typing import Dict, List, Any, Optional, Tuple
import logging
import folium
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeoTools:
    """Geographic tools for the CompSet Analyzer."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize geographic tools.
        
        Args:
            api_key: Google Maps API key (defaults to GOOGLE_MAPS_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("GOOGLE_MAPS_API_KEY", "")
    
    def geocode_address(self, address: str) -> Optional[Dict[str, float]]:
        """
        Geocode an address to get latitude and longitude.
        
        Args:
            address: The address to geocode
            
        Returns:
            Dictionary with lat/lng coordinates, or None if geocoding failed
        """
        if not self.api_key:
            # Fallback to a free geocoding API (less accurate and rate-limited)
            return self._geocode_address_free(address)
        
        try:
            params = {
                'address': address,
                'key': self.api_key
            }
            
            base_url = "https://maps.googleapis.com/maps/api/geocode/json"
            response = requests.get(base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if data['status'] == 'OK' and data['results']:
                    location = data['results'][0]['geometry']['location']
                    return {
                        'lat': location['lat'],
                        'lng': location['lng']
                    }
                else:
                    logger.warning(f"Geocoding failed: {data['status']}")
                    return None
                    
            else:
                logger.error(f"Geocoding request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return None
    
    def _geocode_address_free(self, address: str) -> Optional[Dict[str, float]]:
        """
        Geocode an address using a free service.
        
        Args:
            address: The address to geocode
            
        Returns:
            Dictionary with lat/lng coordinates, or None if geocoding failed
        """
        try:
            # Using Nominatim, which has strict usage terms (low volume only)
            params = {
                'q': address,
                'format': 'json'
            }
            
            # Include a user agent to comply with Nominatim terms
            headers = {
                'User-Agent': 'HotelCompSetAnalyzer/1.0'
            }
            
            base_url = "https://nominatim.openstreetmap.org/search"
            response = requests.get(base_url, params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                if data and len(data) > 0:
                    return {
                        'lat': float(data[0]['lat']),
                        'lng': float(data[0]['lon'])
                    }
                else:
                    logger.warning("Free geocoding returned no results")
                    return None
                    
            else:
                logger.error(f"Free geocoding request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Free geocoding error: {e}")
            return None
    
    def calculate_distance(self, coord1: Dict[str, float], coord2: Dict[str, float]) -> float:
        """
        Calculate the distance between two coordinates in miles.
        
        Args:
            coord1: First coordinate (lat/lng)
            coord2: Second coordinate (lat/lng)
            
        Returns:
            Distance in miles
        """
        # Haversine formula for calculating great-circle distance
        lat1, lon1 = coord1['lat'], coord1['lng']
        lat2, lon2 = coord2['lat'], coord2['lng']
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in miles
        r = 3956
        
        # Calculate distance
        distance = c * r
        
        return round(distance, 2)
    
    def calculate_distances(self, subject_hotel: Dict[str, Any], 
                           competitor_hotels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Calculate distances from subject hotel to all competitor hotels.
        
        Args:
            subject_hotel: Subject hotel with lat/lng
            competitor_hotels: List of competitor hotels with lat/lng
            
        Returns:
            List of competitor hotels with distances added
        """
        if not subject_hotel.get('lat') or not subject_hotel.get('lng'):
            logger.warning("Subject hotel coordinates missing, cannot calculate distances")
            return competitor_hotels
        
        subject_coord = {'lat': subject_hotel['lat'], 'lng': subject_hotel['lng']}
        
        for hotel in competitor_hotels:
            if hotel.get('lat') and hotel.get('lng'):
                comp_coord = {'lat': hotel['lat'], 'lng': hotel['lng']}
                hotel['distance_from_subject'] = self.calculate_distance(subject_coord, comp_coord)
            else:
                hotel['distance_from_subject'] = None
        
        return competitor_hotels
    
    def create_map(self, subject_hotel: Dict[str, Any], competitor_hotels: List[Dict[str, Any]],
                  output_file: str = "hotel_map.html") -> str:
        """
        Create an interactive map of the subject and competitor hotels.
        
        Args:
            subject_hotel: Subject hotel with lat/lng
            competitor_hotels: List of competitor hotels with lat/lng
            output_file: Path to save the output HTML file
            
        Returns:
            Path to the created map file
        """
        if not subject_hotel.get('lat') or not subject_hotel.get('lng'):
            logger.warning("Subject hotel coordinates missing, cannot create map")
            return ""
        
        # Center map on subject hotel
        subject_location = [subject_hotel['lat'], subject_hotel['lng']]
        m = folium.Map(location=subject_location, zoom_start=13)
        
        # Add subject hotel marker (yellow)
        folium.Marker(
            location=subject_location,
            popup=f"<b>Subject Hotel:</b> {subject_hotel['name']}<br>{subject_hotel.get('address', '')}",
            tooltip=f"Subject: {subject_hotel['name']}",
            icon=folium.Icon(color='orange', icon='home', prefix='fa')
        ).add_to(m)
        
        # Add competitor hotels markers (red)
        for hotel in competitor_hotels:
            if hotel.get('lat') and hotel.get('lng'):
                folium.Marker(
                    location=[hotel['lat'], hotel['lng']],
                    popup=f"<b>{hotel['name']}</b><br>{hotel.get('address', '')}<br>Distance: {hotel.get('distance_from_subject', 'N/A')} miles",
                    tooltip=hotel['name'],
                    icon=folium.Icon(color='red', icon='hotel', prefix='fa')
                ).add_to(m)
        
        # Add distance circles
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
        
        # Save map to HTML file
        m.save(output_file)
        
        return output_file
    
    def find_nearby_demand_generators(self, lat: float, lng: float, radius_miles: float = 1.0) -> List[Dict[str, Any]]:
        """
        Find nearby points of interest that could be demand generators.
        
        Args:
            lat: Latitude
            lng: Longitude
            radius_miles: Search radius in miles
            
        Returns:
            List of nearby points of interest
        """
        if not self.api_key:
            logger.warning("No API key available for finding demand generators")
            return []
        
        try:
            # Convert radius to meters
            radius_meters = int(radius_miles * 1609.344)
            
            # Types of places that could be demand generators
            place_types = [
                'airport', 'amusement_park', 'aquarium', 'art_gallery', 
                'casino', 'convention_center', 'museum', 'shopping_mall', 
                'stadium', 'tourist_attraction', 'university', 'zoo',
                'hospital', 'corporate_office'
            ]
            
            demand_generators = []
            
            # Make a request for each place type
            for place_type in place_types:
                params = {
                    'location': f"{lat},{lng}",
                    'radius': radius_meters,
                    'type': place_type,
                    'key': self.api_key
                }
                
                base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                response = requests.get(base_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data['status'] == 'OK' and data['results']:
                        for place in data['results']:
                            demand_generators.append({
                                'name': place['name'],
                                'type': place_type,
                                'lat': place['geometry']['location']['lat'],
                                'lng': place['geometry']['location']['lng'],
                                'rating': place.get('rating'),
                                'user_ratings_total': place.get('user_ratings_total')
                            })
                
                # Respect API rate limits
                time.sleep(0.5)
            
            return demand_generators
            
        except Exception as e:
            logger.error(f"Error finding demand generators: {e}")
            return []
#hotel_compset_analyzer/agent/automated_hotel_scraper.py
import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import time
import random
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.scraping_tools import WebScraper
from tools.geo_tools import GeoTools
from agent.llm_controller import LLMController
from data.hotel import Hotel, HotelAmenities, HotelMeetingSpace, HotelReview, HotelRoom

class AutomatedHotelScraper:
    """
    Automated hotel scraper to discover and collect competitive set information.
    """
    
    def __init__(self, location: str, num_competitors: int = 5):
        """
        Initialize the automated hotel scraper.
        
        Args:
            location: City and state to search for hotels
            num_competitors: Number of competitor hotels to find
        """
        # Initialize tools
        self.web_scraper = WebScraper(use_browser=True, headless=False)  # Changed to use_browser
        self.geo_tools = GeoTools()
        self.llm_controller = LLMController()
        
        # Search parameters
        self.location = location
        self.num_competitors = num_competitors
        
        # Logging setup
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Subject hotel
        self.subject_hotel = None
    
    def set_subject_hotel(self, subject_hotel_info: Dict[str, Any]):
        """
        Set subject hotel information.
        
        Args:
            subject_hotel_info: Dictionary with subject hotel details
        """
        # Create a Hotel object for the subject hotel
        self.subject_hotel = Hotel(
            name=subject_hotel_info["name"],
            address=subject_hotel_info.get("address", ""),
            city=subject_hotel_info.get("city", ""),
            state=subject_hotel_info.get("state", ""),
            country=subject_hotel_info.get("country", "United States"),
            brand_affiliation=subject_hotel_info.get("brand", ""),
            chain_scale=subject_hotel_info.get("chain_scale", ""),
            room_count=subject_hotel_info.get("room_count"),
            is_subject=True
        )
        
        # Add amenities
        amenities = HotelAmenities()
        for amenity in subject_hotel_info.get("amenities", []):
            if amenity.lower() == "restaurant":
                amenities.restaurants = [{"name": "Restaurant", "type": "Restaurant"}]
            elif amenity.lower() == "pool":
                amenities.pool = "Yes"
            elif amenity.lower() == "fitness center":
                amenities.fitness_center = True
            elif amenity.lower() == "spa":
                amenities.spa = True
            elif amenity.lower() == "business center":
                amenities.business_center = True
                
        self.subject_hotel.amenities = amenities
        
        # Geocode the subject hotel
        if self.subject_hotel.address:
            address = f"{self.subject_hotel.address}, {self.subject_hotel.city}, {self.subject_hotel.state}"
            coordinates = self.geo_tools.geocode_address(address)
            
            if coordinates:
                self.subject_hotel.latitude = coordinates["lat"]
                self.subject_hotel.longitude = coordinates["lng"]
                self.logger.info(f"Geocoded subject hotel: {coordinates['lat']}, {coordinates['lng']}")
            else:
                self.logger.warning("Could not geocode subject hotel address")
        
        # Enrich subject hotel with additional data
        self._enrich_subject_hotel_data()
        
        # Log
        self.logger.info(f"Set subject hotel: {self.subject_hotel.name}")
    
    def _enrich_subject_hotel_data(self):
        """Enrich subject hotel with additional data from the web."""
        if not self.subject_hotel:
            return
            
        self.logger.info(f"Enriching subject hotel data for {self.subject_hotel.name}")
        
        # Find official website
        official_site = self.web_scraper.find_hotel_official_site(
            self.subject_hotel.name, self.location
        )
        
        if official_site:
            self.logger.info(f"Found official site for subject hotel: {official_site}")
            self.subject_hotel.website = official_site
            
            # Get page content
            content, success = self.web_scraper._get_with_browser(official_site) if self.web_scraper.use_browser else self.web_scraper._get_with_requests(official_site)
            
            if content and success:
                # Extract additional data using LLM
                extraction_results = self.llm_controller.extract_hotel_data(
                    content, self.subject_hotel.name, official_site
                )
                
                if "error" not in extraction_results:
                    # Update fields if not already set
                    for key, value in extraction_results.items():
                        if hasattr(self.subject_hotel, key) and not getattr(self.subject_hotel, key) and value:
                            setattr(self.subject_hotel, key, value)
                    
                    # Add room types if available
                    if "room_types" in extraction_results and extraction_results["room_types"]:
                        for room_type in extraction_results["room_types"]:
                            if isinstance(room_type, dict):
                                self.subject_hotel.room_types.append(HotelRoom(
                                    room_type=room_type.get("name", "Unknown"),
                                    size_sf=room_type.get("size_sf"),
                                    size_metric=room_type.get("size_metric", "sf"),
                                    description=room_type.get("description", "")
                                ))
                    
                    # Add meeting space if available
                    if "meeting_space" in extraction_results and extraction_results["meeting_space"]:
                        ms = extraction_results["meeting_space"]
                        if isinstance(ms, dict):
                            self.subject_hotel.meeting_space = HotelMeetingSpace(
                                total_space_sf=ms.get("total_space_sf"),
                                total_rooms=ms.get("total_rooms"),
                                largest_room_sf=ms.get("largest_room_sf"),
                                largest_room_capacity=ms.get("largest_room_capacity")
                            )
                
                # Extract amenities
                amenities_results = self.llm_controller.extract_amenities(
                    content, self.subject_hotel.name, official_site
                )
                
                if "error" not in amenities_results:
                    # Update amenities
                    if not self.subject_hotel.amenities:
                        self.subject_hotel.amenities = HotelAmenities()
                        
                    # Restaurants
                    if "restaurants" in amenities_results and amenities_results["restaurants"]:
                        restaurants = amenities_results["restaurants"]
                        if isinstance(restaurants, list):
                            self.subject_hotel.amenities.restaurants = [
                                {"name": r.get("name", ""), "type": r.get("type", "")} 
                                for r in restaurants if isinstance(r, dict)
                            ]
                    
                    # Other amenities
                    for key in ["bars_lounges", "pool", "fitness_center", "spa", "business_center", 
                               "parking_details", "parking_cost", "resort_fee", "club_lounge"]:
                        if key in amenities_results and amenities_results[key]:
                            setattr(self.subject_hotel.amenities, key, amenities_results[key])
                
                # Extract images
                images = self.web_scraper.extract_images_from_page(content, official_site)
                
                if images["exterior"] and not self.subject_hotel.exterior_photo_url:
                    self.subject_hotel.exterior_photo_url = images["exterior"][0]
                
                if images["rooms"] and not self.subject_hotel.guestroom_photo_url:
                    self.subject_hotel.guestroom_photo_url = images["rooms"][0]
        
        # Find TripAdvisor page for reviews
        tripadvisor_url = self.web_scraper.search_hotel_on_tripadvisor(
            self.subject_hotel.name, self.location
        )
        
        if tripadvisor_url:
            self.logger.info(f"Found TripAdvisor page for subject hotel: {tripadvisor_url}")
            
            # Get TripAdvisor content
            ta_content, ta_success = self.web_scraper.get_page_content(
                tripadvisor_url, use_selenium=True
            )
            
            if ta_content and ta_success:
                # Extract reviews
                reviews_results = self.llm_controller.summarize_reviews(
                    ta_content, self.subject_hotel.name, "TripAdvisor"
                )
                
                if "error" not in reviews_results:
                    self.subject_hotel.reviews.append(HotelReview(
                        platform="TripAdvisor",
                        score=reviews_results.get("average_score", 0),
                        total_reviews=reviews_results.get("total_reviews", 0),
                        last_updated=datetime.now(),
                        common_themes=reviews_results.get("common_themes", [])
                    ))
        
        # Find nearby demand generators if we have coordinates
        if self.subject_hotel.latitude and self.subject_hotel.longitude:
            try:
                demand_generators = self.geo_tools.find_nearby_demand_generators(
                    self.subject_hotel.latitude, 
                    self.subject_hotel.longitude, 
                    radius_miles=1.0
                )
                
                if demand_generators:
                    self.subject_hotel.nearby_demand_generators = [
                        f"{dg['name']} ({dg['type']})" for dg in demand_generators[:10]
                    ]
            except Exception as e:
                self.logger.error(f"Error finding demand generators: {e}")
    
    def discover_hotels(self) -> List[Dict[str, Any]]:
        """
        Discover potential competitive set hotels in the given location.
        
        Returns:
            List of potential hotel dictionaries
        """
        try:
            # Check if we have a subject hotel with chain scale
            chain_scale = ""
            if self.subject_hotel and self.subject_hotel.chain_scale:
                chain_scale = self.subject_hotel.chain_scale
                    
            # Prepare search queries
            search_queries = []
            
            # Try multiple search approaches to increase chances of finding hotels
            if chain_scale:
                search_queries.append(f"{chain_scale} hotels in {self.location}")
            
            search_queries.append(f"luxury hotels in {self.location}")
            search_queries.append(f"best hotels in {self.location}")
            
            # If subject hotel has coordinates, use them for proximity search
            if self.subject_hotel and self.subject_hotel.latitude and self.subject_hotel.longitude:
                search_queries.append(f"hotels near {self.subject_hotel.address}, {self.location}")
            
            # List to store all search results
            all_results = []
            
            # Try each search query
            for query in search_queries:
                self.logger.info(f"Searching with query: {query}")
                results = self.web_scraper.search_hotel(query, self.location)
                self.logger.info(f"Search returned {len(results)} results")
                
                # Add new results to all_results list
                all_results.extend([r for r in results if r not in all_results])
                
                # If we have enough results, break
                if len(all_results) >= self.num_competitors * 3:
                    break
            
            # Debug: Print all search results
            self.logger.info(f"Total search results found: {len(all_results)}")
            for idx, result in enumerate(all_results):
                self.logger.info(f"Result {idx+1}: {result.get('title', 'No title')} - {result.get('domain', 'No domain')}")
            
            # Filter and process results
            potential_hotels = []
            
            # Skip subject hotel if it's in the results
            subject_name_lower = self.subject_hotel.name.lower() if self.subject_hotel else ""
            
            for result in all_results:
                # Extract key information
                title = result.get('title', '')
                
                # Skip if no title
                if not title:
                    continue
                    
                # Process name - remove "Hotel" and other common suffixes
                name = title
                for suffix in [' Hotel', ' Resort', ' & Spa', ' Washington DC', ' Washington D.C.']:
                    name = name.replace(suffix, '')
                
                hotel_info = {
                    'name': name,
                    'domain': result.get('domain', ''),
                    'url': result.get('url', ''),
                    'snippet': result.get('snippet', '')
                }
                
                
                # Skip if this is the subject hotel
                if subject_name_lower and subject_name_lower in hotel_info['name'].lower():
                    self.logger.info(f"Skipping subject hotel: {hotel_info['name']}")
                    continue
                
                # Relaxed filtering - just ensure it's probably a hotel
                skip_words = ['maps', 'learn more', 'best', 'favorite', 'forum', 'reddit']
                hotel_words = ['hotel', 'resort', 'inn', 'suites', 'hyatt', 'marriott', 'hilton', 'ritz']

                if (len(hotel_info['name']) > 3 and  # Longer names
                    not any(skip_word in hotel_info['name'].lower() for skip_word in skip_words) and
                    (any(hotel_word in title.lower() for hotel_word in hotel_words))):
                    
                    # Log the hotel being added
                    self.logger.info(f"Adding potential hotel: {hotel_info['name']}")
                    potential_hotels.append(hotel_info)
                
                # Stop if we have enough potential hotels
                if len(potential_hotels) >= self.num_competitors * 2:
                    break
            
            # If we still don't have hotels, try to extract from snippets
            if len(potential_hotels) == 0:
                self.logger.warning("No hotels found through title filtering, attempting to extract from snippets")
                for result in all_results:
                    snippet = result.get('snippet', '')
                    if 'hotel' in snippet.lower() or 'resort' in snippet.lower():
                        # Extract potential hotel name - look for capitalized words
                        import re
                        capitalized_words = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', snippet)
                        
                        for potential_name in capitalized_words:
                            if len(potential_name) > 5 and 'hotel' not in potential_name.lower():
                                hotel_info = {
                                    'name': potential_name,
                                    'domain': result.get('domain', ''),
                                    'url': result.get('url', ''),
                                    'snippet': snippet
                                }
                                
                                # Skip if this is the subject hotel
                                if subject_name_lower and subject_name_lower in hotel_info['name'].lower():
                                    continue
                                    
                                self.logger.info(f"Adding hotel from snippet analysis: {hotel_info['name']}")
                                potential_hotels.append(hotel_info)
                                
                                if len(potential_hotels) >= self.num_competitors:
                                    break
                    
                    if len(potential_hotels) >= self.num_competitors:
                        break
            
            # If we still have no hotels, create some with city-specific properties
            if len(potential_hotels) == 0:
                self.logger.warning("No hotels found through search, using known hotels in the city")
                
                # Dynamic approach - use the city name to generate likely hotel chains
                city = self.location.split(',')[0].strip()
                
                # Common hotel chains that exist in major cities
                chains = ["Four Seasons", "Ritz-Carlton", "JW Marriott", "St. Regis", "Mandarin Oriental", 
                        "Hyatt Regency", "Fairmont", "W Hotel", "Westin", "Hilton"]
                
                for chain in chains:
                    hotel_name = f"{chain} {city}"
                    
                    # Skip if this is the subject hotel
                    if subject_name_lower and subject_name_lower in hotel_name.lower():
                        continue
                    
                    hotel_info = {
                        'name': hotel_name,
                        'domain': f"{chain.lower().replace(' ', '')}.com",
                        'url': "",
                        'snippet': f"{chain} hotel in {city}"
                    }
                    self.logger.info(f"Adding generated hotel: {hotel_info['name']}")
                    potential_hotels.append(hotel_info)
                    
                    if len(potential_hotels) >= self.num_competitors:
                        break
            
            self.logger.info(f"Final potential hotel count: {len(potential_hotels)}")
            return potential_hotels
            
        except Exception as e:
            self.logger.error(f"Error discovering hotels: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def collect_hotel_details(self, hotel_dict: Dict[str, Any]) -> Optional[Hotel]:
        """
        Collect detailed information for a specific hotel.
        
        Args:
            hotel_dict: Dictionary with initial hotel information
            
        Returns:
            Populated Hotel object or None
        """
        try:
            hotel_name = hotel_dict['name']
            self.logger.info(f"Collecting details for competitor hotel: {hotel_name}")
            
            # Find official website
            official_site = self.web_scraper.find_hotel_official_site(
                hotel_name, self.location
            )
            
            # Initialize Hotel object with basic info
            hotel = Hotel(
                name=hotel_name,
                address="",
                city=self.location.split(',')[0].strip(),
                state=self.location.split(',')[1].strip() if ',' in self.location else "",
                country="United States",
                website=official_site
            )
            
            if official_site:
                self.logger.info(f"Found official site: {official_site}")
                
                # Get page content
                content, success = self.web_scraper._get_with_browser(official_site) if self.web_scraper.use_browser else self.web_scraper._get_with_requests(official_site)
                
                if content and success:
                    # Extract hotel data using LLM
                    extraction_results = self.llm_controller.extract_hotel_data(
                        content, hotel_name, official_site
                    )
                    
                    if "error" not in extraction_results:
                        # Update hotel data
                        for key, value in extraction_results.items():
                            if hasattr(hotel, key) and value:
                                setattr(hotel, key, value)
                        
                        # Add source
                        hotel.sources["basic_info"] = official_site
                        
                        self.logger.info(f"Extracted basic hotel data for {hotel_name}")
                    else:
                        self.logger.warning(f"Error extracting hotel data: {extraction_results.get('error')}")
                    
                    # Extract amenities
                    amenities_results = self.llm_controller.extract_amenities(
                        content, hotel_name, official_site
                    )
                    
                    if "error" not in amenities_results:
                        # Create amenities object
                        hotel.amenities = HotelAmenities()
                        
                        # Update amenities
                        for key in ["restaurants", "bars_lounges", "pool", "fitness_center", "spa", 
                                   "business_center", "parking_details", "parking_cost", "resort_fee", 
                                   "club_lounge", "other_amenities"]:
                            if key in amenities_results and amenities_results[key]:
                                setattr(hotel.amenities, key, amenities_results[key])
                        
                        # Add source
                        hotel.sources["amenities"] = official_site
                        
                        self.logger.info(f"Extracted amenities for {hotel_name}")
                    else:
                        self.logger.warning(f"Error extracting amenities: {amenities_results.get('error')}")
                    
                    # Extract images
                    images = self.web_scraper.extract_images_from_page(content, official_site)
                    
                    if images["exterior"]:
                        hotel.exterior_photo_url = images["exterior"][0]
                    
                    if images["rooms"]:
                        hotel.guestroom_photo_url = images["rooms"][0]
                    
                    self.logger.info(f"Found {len(images['exterior'])} exterior and {len(images['rooms'])} room images")
            else:
                self.logger.warning(f"Could not find official site for {hotel_name}")
            
            # Try to find on TripAdvisor for reviews
            tripadvisor_url = self.web_scraper.search_hotel_on_tripadvisor(
                hotel_name, self.location
            )
            
            if tripadvisor_url:
                self.logger.info(f"Found on TripAdvisor: {tripadvisor_url}")
                
                # Get page content
                content, success = self.web_scraper._get_with_browser(tripadvisor_url) if self.web_scraper.use_browser else self.web_scraper._get_with_requests(tripadvisor_url)
                
                if content and success:
                    # Extract reviews
                    reviews_results = self.llm_controller.summarize_reviews(
                        content, hotel_name, "TripAdvisor"
                    )
                    
                    if "error" not in reviews_results:
                        # Add review
                        hotel.reviews.append(HotelReview(
                            platform="TripAdvisor",
                            score=reviews_results.get("average_score", 0),
                            total_reviews=reviews_results.get("total_reviews", 0),
                            last_updated=datetime.now(),
                            common_themes=reviews_results.get("common_themes", [])
                        ))
                        
                        # Add source
                        hotel.sources["reviews"] = tripadvisor_url
                        
                        self.logger.info(f"Extracted TripAdvisor reviews for {hotel_name}")
                    else:
                        self.logger.warning(f"Error extracting TripAdvisor reviews: {reviews_results.get('error')}")
            else:
                self.logger.warning(f"Could not find {hotel_name} on TripAdvisor")
            
            # Try Google for reviews if TripAdvisor not available or no reviews extracted
            if not hotel.reviews:
                google_search_url = f"https://www.google.com/search?q={hotel_name}+{self.location}+reviews"
                content, success = self.web_scraper._get_with_browser(google_search_url) if self.web_scraper.use_browser else self.web_scraper._get_with_requests(google_search_url)
                
                if content and success:
                    # Extract reviews
                    reviews_results = self.llm_controller.summarize_reviews(
                        content, hotel_name, "Google"
                    )
                    
                    if "error" not in reviews_results and reviews_results.get("average_score"):
                        # Add review
                        hotel.reviews.append(HotelReview(
                            platform="Google",
                            score=reviews_results.get("average_score", 0),
                            total_reviews=reviews_results.get("total_reviews", 0),
                            last_updated=datetime.now(),
                            common_themes=reviews_results.get("common_themes", [])
                        ))
                        
                        # Add source
                        hotel.sources["reviews"] = google_search_url
                        
                        self.logger.info(f"Extracted Google reviews for {hotel_name}")
            
            # Geocode address
            if hotel.address:
                address = f"{hotel.address}, {hotel.city}, {hotel.state}"
                coordinates = self.geo_tools.geocode_address(address)
                
                if coordinates:
                    hotel.latitude = coordinates["lat"]
                    hotel.longitude = coordinates["lng"]
                    
                    self.logger.info(f"Geocoded address: {coordinates['lat']}, {coordinates['lng']}")
                    
                    # Try to find nearby demand generators
                    try:
                        demand_generators = self.geo_tools.find_nearby_demand_generators(
                            hotel.latitude, hotel.longitude, radius_miles=0.5
                        )
                        
                        if demand_generators:
                            hotel.nearby_demand_generators = [
                                f"{dg['name']} ({dg['type']})" for dg in demand_generators[:5]
                            ]
                            
                            self.logger.info(f"Found {len(hotel.nearby_demand_generators)} nearby demand generators")
                    except Exception as e:
                        self.logger.error(f"Error finding demand generators: {e}")
                else:
                    self.logger.warning(f"Could not geocode address for {hotel_name}")
            
            # If we still don't have address or geocode data, try Google Maps
            if not hotel.latitude or not hotel.longitude:
                google_maps_search = f"{hotel_name} {self.location} map"
                maps_url = f"https://www.google.com/maps/search/{google_maps_search.replace(' ', '+')}"
                
                # Extract basic info from Google Maps
                # This is simplified - in a real implementation, you would need 
                # a more sophisticated method to extract data from Google Maps
                self.logger.info(f"Trying Google Maps for location data: {maps_url}")
            
            # Calculate meeting space per key if we have both values
            if (hotel.meeting_space and hotel.meeting_space.total_space_sf and 
                hotel.room_count and hotel.room_count > 0):
                hotel.meeting_space.meeting_space_per_key = (
                    hotel.meeting_space.total_space_sf / hotel.room_count
                )
            
            # Calculate suite percentage if we have both values
            if hotel.suite_count is not None and hotel.room_count and hotel.room_count > 0:
                hotel.suite_percentage = (hotel.suite_count / hotel.room_count) * 100
            
            # Add a small delay to avoid rate limiting
            time.sleep(random.uniform(1.0, 3.0))
            
            return hotel
        
        except Exception as e:
            self.logger.error(f"Error collecting details for {hotel_dict['name']}: {e}")
            return None
    
    def run_competitive_set_analysis(self) -> Dict[str, Any]:
        """
        Run full competitive set analysis.
        
        Returns:
            Dictionary with analysis results
        """
        # Check if subject hotel is set
        if not self.subject_hotel:
            self.logger.error("Subject hotel not set. Call set_subject_hotel() first.")
            return {"error": "Subject hotel not set", "hotels": []}
        
        # Discover potential hotels
        potential_hotels = self.discover_hotels()
        
        # Collect details for each hotel
        competitive_set = []
        
        for hotel_info in potential_hotels:
            hotel_details = self.collect_hotel_details(hotel_info)
            
            if hotel_details:
                # Calculate distance from subject hotel
                if (self.subject_hotel.latitude and self.subject_hotel.longitude and 
                    hotel_details.latitude and hotel_details.longitude):
                    
                    distance = self.geo_tools.calculate_distance(
                        {"lat": self.subject_hotel.latitude, "lng": self.subject_hotel.longitude},
                        {"lat": hotel_details.latitude, "lng": hotel_details.longitude}
                    )
                    hotel_details.distance_from_subject = distance
                    
                    self.logger.info(f"Distance from subject hotel: {distance:.2f} miles")
                
                competitive_set.append(hotel_details)
                
                # Stop if we have enough hotels
                if len(competitive_set) >= self.num_competitors:
                    break
        
        # Sort by distance if available
        competitive_set.sort(key=lambda x: x.distance_from_subject or float('inf'))
        
        # Prepare output
        return {
            "subject_hotel": self.subject_hotel,
            "competitor_hotels": competitive_set,
            "location": self.location,
            "num_hotels": len(competitive_set)
        }
    
    def export_to_json(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Export analysis results to JSON.
        
        Args:
            data: Analysis results
            filename: Optional filename (defaults to location-based name)
            
        Returns:
            Path to the saved JSON file
        """
        if not filename:
            # Create a safe filename from the location and subject hotel
            safe_location = self.location.replace(' ', '_').replace(',', '').lower()
            safe_hotel = data["subject_hotel"].name.replace(' ', '_').lower() if "subject_hotel" in data else "unknown"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            filename = f"{safe_hotel}_{safe_location}_{timestamp}_compset.json"
        
        # Create output directory
        os.makedirs("./output", exist_ok=True)
        filepath = os.path.join("./output", filename)
        
        # Convert hotels to dictionaries
        serializable_data = {
            "location": data['location'],
            "num_hotels": data['num_hotels'],
            "subject_hotel": self._hotel_to_dict(data.get('subject_hotel')) if data.get('subject_hotel') else None,
            "competitor_hotels": [self._hotel_to_dict(hotel) for hotel in data.get('competitor_hotels', [])]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable_data, f, indent=2, default=str)
        
        self.logger.info(f"Exported CompSet analysis to {filepath}")
        return filepath
    
    def _hotel_to_dict(self, hotel: Hotel) -> Dict[str, Any]:
        """
        Convert Hotel object to a dictionary for JSON serialization.
        
        Args:
            hotel: Hotel object to convert
            
        Returns:
            Serializable dictionary representation
        """
        if not hotel:
            return {}
            
        return {
            "name": hotel.name,
            "address": hotel.address,
            "city": hotel.city,
            "state": hotel.state,
            "country": hotel.country,
            "brand_affiliation": hotel.brand_affiliation,
            "chain_scale": hotel.chain_scale,
            "room_count": hotel.room_count,
            "suite_count": hotel.suite_count,
            "suite_percentage": hotel.suite_percentage,
            "year_built": hotel.year_built,
            "year_renovated": hotel.year_renovated,
            "latitude": hotel.latitude,
            "longitude": hotel.longitude,
            "distance_from_subject": hotel.distance_from_subject,
            "website": hotel.website,
            "owner": hotel.owner,
            "management_company": hotel.management_company,
            "amenities": {
                "restaurants": [{"name": r.get("name", ""), "type": r.get("type", "")} 
                              for r in hotel.amenities.restaurants] if hotel.amenities and hotel.amenities.restaurants else [],
                "bars_lounges": hotel.amenities.bars_lounges if hotel.amenities else [],
                "pool": hotel.amenities.pool if hotel.amenities else None,
                "fitness_center": hotel.amenities.fitness_center if hotel.amenities else False,
                "spa": hotel.amenities.spa if hotel.amenities else False,
                "business_center": hotel.amenities.business_center if hotel.amenities else False,
                "club_lounge": hotel.amenities.club_lounge if hotel.amenities else False,
                "parking_details": hotel.amenities.parking_details if hotel.amenities else None,
                "parking_cost": hotel.amenities.parking_cost if hotel.amenities else None,
                "resort_fee": hotel.amenities.resort_fee if hotel.amenities else None,
                "other_amenities": hotel.amenities.other_amenities if hotel.amenities else []
            },
            "meeting_space": {
                "total_space_sf": hotel.meeting_space.total_space_sf if hotel.meeting_space else None,
                "total_rooms": hotel.meeting_space.total_rooms if hotel.meeting_space else None,
                "largest_room_sf": hotel.meeting_space.largest_room_sf if hotel.meeting_space else None,
                "largest_room_capacity": hotel.meeting_space.largest_room_capacity if hotel.meeting_space else None,
                "meeting_space_per_key": hotel.meeting_space.meeting_space_per_key if hotel.meeting_space else None
            },
            "room_types": [
                {
                    "room_type": rt.room_type,
                    "size_sf": rt.size_sf,
                    "size_metric": rt.size_metric,
                    "description": rt.description
                } for rt in hotel.room_types
            ],
            "reviews": [
                {
                    "platform": review.platform,
                    "score": review.score,
                    "total_reviews": review.total_reviews,
                    "common_themes": review.common_themes
                } for review in hotel.reviews
            ],
            "nearby_demand_generators": hotel.nearby_demand_generators,
            "exterior_photo_url": hotel.exterior_photo_url,
            "guestroom_photo_url": hotel.guestroom_photo_url,
            "sources": hotel.sources
        }
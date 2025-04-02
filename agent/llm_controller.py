#hotel_compset_analyzer/agent/llm_controller.py
"""
LLM Controller for the Hotel CompSet Analyzer.
Manages interactions with the Claude API for agentic web scraping.
"""

import os
import time
import json
from typing import Dict, List, Any, Optional, Tuple
import logging
import anthropic

from agent.prompt_templates import (
    SYSTEM_PROMPT,
    HOTEL_EXTRACTION_PROMPT,
    AMENITIES_EXTRACTION_PROMPT,
    REVIEW_SUMMARY_PROMPT
)
from data.hotel import Hotel, HotelAmenities, HotelReview, HotelRoom, HotelMeetingSpace

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMController:
    """Controller for LLM-based agentic web scraping"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM controller.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable or pass api_key.")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-opus-20240229"  # Using the most capable model
    
    def extract_hotel_data(self, html_content: str, hotel_name: str, url: str) -> Dict[str, Any]:
        """
        Extract hotel data from HTML content using Claude.
        
        Args:
            html_content: The HTML content of the hotel's webpage
            hotel_name: The name of the hotel to extract data for
            url: The URL where the content was retrieved from
            
        Returns:
            Dictionary containing extracted hotel data
        """
        # Truncate HTML if too long (Claude has context limits)
        if len(html_content) > 80000:
            html_content = html_content[:80000] + "... [TRUNCATED]"
        
        prompt = HOTEL_EXTRACTION_PROMPT.format(
            hotel_name=hotel_name,
            url=url,
            html_content=html_content
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                system=SYSTEM_PROMPT,
                max_tokens=4000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract JSON from the response
            message_content = response.content[0].text
            
            # Find JSON content (between ```json and ```)
            json_start = message_content.find("```json")
            json_end = message_content.rfind("```")
            
            if json_start != -1 and json_end != -1:
                json_content = message_content[json_start + 7:json_end].strip()
                return json.loads(json_content)
            else:
                # Try to parse the entire response as JSON
                try:
                    return json.loads(message_content)
                except json.JSONDecodeError:
                    logger.error(f"Failed to extract JSON from response: {message_content[:500]}...")
                    return {"error": "Could not extract structured data", "raw_response": message_content}
        
        except Exception as e:
            logger.error(f"Error extracting hotel data: {e}")
            return {"error": str(e)}
    
    def extract_amenities(self, html_content: str, hotel_name: str, url: str) -> Dict[str, Any]:
        """
        Extract hotel amenities from HTML content using Claude.
        
        Args:
            html_content: The HTML content of the hotel's webpage
            hotel_name: The name of the hotel to extract amenities for
            url: The URL where the content was retrieved from
            
        Returns:
            Dictionary containing extracted amenities data
        """
        # Truncate HTML if too long
        if len(html_content) > 80000:
            html_content = html_content[:80000] + "... [TRUNCATED]"
        
        prompt = AMENITIES_EXTRACTION_PROMPT.format(
            hotel_name=hotel_name,
            url=url,
            html_content=html_content
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                system=SYSTEM_PROMPT,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract JSON from the response
            message_content = response.content[0].text
            
            # Find JSON content (between ```json and ```)
            json_start = message_content.find("```json")
            json_end = message_content.rfind("```")
            
            if json_start != -1 and json_end != -1:
                json_content = message_content[json_start + 7:json_end].strip()
                return json.loads(json_content)
            else:
                # Try to parse the entire response as JSON
                try:
                    return json.loads(message_content)
                except json.JSONDecodeError:
                    logger.error(f"Failed to extract JSON from amenities response: {message_content[:500]}...")
                    return {"error": "Could not extract structured amenities data", "raw_response": message_content}
        
        except Exception as e:
            logger.error(f"Error extracting amenities: {e}")
            return {"error": str(e)}
    
    def summarize_reviews(self, reviews_text: str, hotel_name: str, source: str) -> Dict[str, Any]:
        """
        Summarize hotel reviews using Claude.
        
        Args:
            reviews_text: Text containing multiple reviews
            hotel_name: The name of the hotel
            source: The source of the reviews (e.g., TripAdvisor, Google)
            
        Returns:
            Dictionary containing review summary and common themes
        """
        # Truncate reviews if too long
        if len(reviews_text) > 80000:
            reviews_text = reviews_text[:80000] + "... [TRUNCATED]"
        
        prompt = REVIEW_SUMMARY_PROMPT.format(
            hotel_name=hotel_name,
            source=source,
            reviews_text=reviews_text
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                system=SYSTEM_PROMPT,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract JSON from the response
            message_content = response.content[0].text
            
            # Find JSON content (between ```json and ```)
            json_start = message_content.find("```json")
            json_end = message_content.rfind("```")
            
            if json_start != -1 and json_end != -1:
                json_content = message_content[json_start + 7:json_end].strip()
                return json.loads(json_content)
            else:
                # Try to parse the entire response as JSON
                try:
                    return json.loads(message_content)
                except json.JSONDecodeError:
                    logger.error(f"Failed to extract JSON from review summary: {message_content[:500]}...")
                    return {
                        "average_score": 0,
                        "total_reviews": 0,
                        "common_themes": ["Could not extract review themes"],
                        "error": "Could not extract structured review data",
                        "raw_response": message_content
                    }
        
        except Exception as e:
            logger.error(f"Error summarizing reviews: {e}")
            return {
                "average_score": 0,
                "total_reviews": 0,
                "common_themes": ["Error processing reviews"],
                "error": str(e)
            }
    
    def create_hotel_from_extraction(self, extraction_results: Dict[str, Any], 
                                     amenities_results: Dict[str, Any] = None,
                                     reviews_results: Dict[str, Dict[str, Any]] = None) -> Hotel:
        """
        Create a Hotel object from extraction results.
        
        Args:
            extraction_results: Basic hotel data extraction results
            amenities_results: Hotel amenities extraction results (optional)
            reviews_results: Hotel reviews summarization results by platform (optional)
            
        Returns:
            Hotel object populated with extracted data
        """
        # Create hotel object with basic info
        hotel = Hotel(
            name=extraction_results.get("hotel_name", "Unknown Hotel"),
            address=extraction_results.get("address", ""),
            city=extraction_results.get("city", ""),
            state=extraction_results.get("state", ""),
            country=extraction_results.get("country", "United States"),
            website=extraction_results.get("website", ""),
            brand_affiliation=extraction_results.get("brand_affiliation", ""),
            chain_scale=extraction_results.get("chain_scale", ""),
            owner=extraction_results.get("owner", ""),
            management_company=extraction_results.get("management_company", ""),
            year_built=extraction_results.get("year_built"),
            year_renovated=extraction_results.get("year_renovated"),
            room_count=extraction_results.get("room_count"),
            suite_count=extraction_results.get("suite_count")
        )
        
        # Add room types if available
        room_types = extraction_results.get("room_types", [])
        for room_type in room_types:
            if isinstance(room_type, dict):
                hotel.room_types.append(HotelRoom(
                    room_type=room_type.get("name", "Unknown"),
                    size_sf=room_type.get("size_sf"),
                    size_metric=room_type.get("size_metric", "sf"),
                    description=room_type.get("description", ""),
                    photo_url=room_type.get("photo_url", "")
                ))
        
        # Add meeting space if available
        meeting_space = extraction_results.get("meeting_space", {})
        if meeting_space and isinstance(meeting_space, dict):
            hotel.meeting_space = HotelMeetingSpace(
                total_space_sf=meeting_space.get("total_space_sf"),
                total_rooms=meeting_space.get("total_rooms"),
                largest_room_sf=meeting_space.get("largest_room_sf"),
                largest_room_capacity=meeting_space.get("largest_room_capacity")
            )
        
        # Add amenities if available
        if amenities_results:
            restaurants = amenities_results.get("restaurants", [])
            bars_lounges = amenities_results.get("bars_lounges", [])
            
            hotel.amenities = HotelAmenities(
                restaurants=[{"name": r.get("name", ""), "type": r.get("type", "")} 
                            for r in restaurants] if isinstance(restaurants, list) else [],
                bars_lounges=bars_lounges if isinstance(bars_lounges, list) else [],
                pool=amenities_results.get("pool"),
                fitness_center=amenities_results.get("fitness_center", False),
                fitness_details=amenities_results.get("fitness_details", ""),
                spa=amenities_results.get("spa", False),
                spa_details=amenities_results.get("spa_details", ""),
                business_center=amenities_results.get("business_center", False),
                parking_details=amenities_results.get("parking_details", ""),
                parking_cost=amenities_results.get("parking_cost"),
                resort_fee=amenities_results.get("resort_fee"),
                club_lounge=amenities_results.get("club_lounge", False),
                other_amenities=amenities_results.get("other_amenities", [])
            )
        
        # Add reviews if available
        if reviews_results:
            for platform, review_data in reviews_results.items():
                if isinstance(review_data, dict):
                    hotel.reviews.append(HotelReview(
                        platform=platform,
                        score=review_data.get("average_score", 0),
                        total_reviews=review_data.get("total_reviews", 0),
                        common_themes=review_data.get("common_themes", [])
                    ))
        
        # Add photos if available
        hotel.exterior_photo_url = extraction_results.get("exterior_photo_url", "")
        hotel.guestroom_photo_url = extraction_results.get("guestroom_photo_url", "")
        
        # Add nearby demand generators if available
        hotel.nearby_demand_generators = extraction_results.get("nearby_demand_generators", [])
        
        # Add sources
        hotel.sources = extraction_results.get("sources", {})
        
        return hotel
#hotel_compset_analyzer/agent/prompt_templates.py
"""
Prompt templates for the Claude LLM in the CompSet Analyzer.
"""

# System prompt for Anthropic Claude
SYSTEM_PROMPT = """
You are an expert hotel real estate analyst specializing in extracting structured information from hotel websites and travel sites. Your job is to carefully extract information to build competitive set analyses for hotel properties.

You will be given HTML content or text from hotel websites, OTAs (Online Travel Agencies), review sites, and other sources. You need to extract specific details meticulously and return them in JSON format.

When given HTML content, focus on extracting factual information that would be useful for hotel real estate analysis. Avoid marketing language and focus on the facts.

Be precise in your extractions and always return structured data as JSON.
"""

# Hotel Information Extraction Prompt
HOTEL_EXTRACTION_PROMPT = """
Extract detailed information about the hotel named "{hotel_name}" from this webpage content.
Source URL: {url}

I need you to extract the following information in JSON format:
1. hotel_name: The official name of the hotel
2. address: The street address
3. city: The city
4. state: The state/province
5. country: The country
6. website: The hotel's website URL
7. brand_affiliation: The hotel brand/chain (e.g., Marriott, Hilton)
8. chain_scale: The chain scale (e.g., Luxury, Upper Upscale, Ups-cale)
9. owner: The owner company, if mentioned
10. management_company: The management company, if mentioned
11. year_built: Year the hotel was built, if mentioned
12. year_renovated: Year of the most recent renovation, if mentioned
13. room_count: Total number of rooms
14. suite_count: Number of suites, if mentioned
15. room_types: Array of room types with their details (name, size_sf, description)
16. meeting_space: Object with meeting space details (total_space_sf, total_rooms, largest_room_sf, largest_room_capacity)
17. exterior_photo_url: URL to an exterior photo of the hotel
18. guestroom_photo_url: URL to a standard guestroom photo
19. nearby_demand_generators: Array of nearby attractions or demand generators
20. sources: Object mapping data types to the source URLs where you found the information

Return the data in this JSON format:
{
  "hotel_name": "",
  "address": "",
  "city": "",
  "state": "",
  "country": "",
  "website": "",
  "brand_affiliation": "",
  "chain_scale": "",
  "owner": "",
  "management_company": "",
  "year_built": null,
  "year_renovated": null,
  "room_count": null,
  "suite_count": null,
  "room_types": [
    {
      "name": "",
      "size_sf": null,
      "description": ""
    }
  ],
  "meeting_space": {
    "total_space_sf": null,
    "total_rooms": null,
    "largest_room_sf": null,
    "largest_room_capacity": null
  },
  "exterior_photo_url": "",
  "guestroom_photo_url": "",
  "nearby_demand_generators": [],
  "sources": {}
}
For any fields where information is not available in the provided content, leave them as null or
empty strings/arrays as appropriate. Be factual and precise.
HTML Content:
{html_content}
"""

# Amenities Extraction Prompt
AMENITIES_EXTRACTION_PROMPT = """
Extract detailed amenity information about the hotel named "{hotel_name}" from this webpage content.
Source URL: {url}
I need you to extract the following amenity information in JSON format:

restaurants: Array of restaurant objects (name, type) at the hotel
bars_lounges: Array of bar/lounge names at the hotel
pool: Type of pool (Indoor/Outdoor/Both/None)
fitness_center: Boolean indicating if there's a fitness center
fitness_details: Details about the fitness center
spa: Boolean indicating if there's a spa
spa_details: Details about the spa
business_center: Boolean indicating if there's a business center
parking_details: Details about parking (self/valet)
parking_cost: Cost of parking, if mentioned
resort_fee: Amount of resort/amenity fee, if any
club_lounge: Boolean indicating if there's a club or executive lounge
other_amenities: Array of other notable amenities

Return the data in this JSON format:
{
  "restaurants": [
    {
      "name": "",
      "type": ""
    }
  ],
  "bars_lounges": [],
  "pool": "",
  "fitness_center": false,
  "fitness_details": "",
  "spa": false,
  "spa_details": "",
  "business_center": false,
  "parking_details": "",
  "parking_cost": null,
  "resort_fee": null,
  "club_lounge": false,
  "other_amenities": []
}
For any fields where information is not available in the provided content, leave them as null, false, or empty strings/arrays as appropriate. Be factual and precise.
HTML Content:
{html_content}
"""

# Review Summary Prompt
REVIEW_SUMMARY_PROMPT = """
Analyze and summarize guest reviews for the hotel named "{hotel_name}" from {source}.
I need you to extract the following information in JSON format:

average_score: The average review score for the hotel (on a scale matching the source platform)
total_reviews: The total number of reviews analyzed
common_themes: Array of common themes mentioned in reviews (positive and negative)

Return the data in this JSON format:
{
  "average_score": 0.0,
  "total_reviews": 0,
  "common_themes": []
}
Be factual and precise. Focus on extracting objective information from the reviews.
Reviews Text:
{reviews_text}
"""
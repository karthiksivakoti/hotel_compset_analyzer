#hotel_compset_analyzer/data/hotel.py
"""
Hotel data model for the CompSet Analyzer.
Defines the structure and properties of a hotel in the competitive set.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class HotelAmenities:
    """Data class for hotel amenities."""
    restaurants: List[Dict[str, str]] = field(default_factory=list)  # [{"name": "Name", "type": "Type"}]
    bars_lounges: List[str] = field(default_factory=list)
    pool: Optional[str] = None  # Indoor/Outdoor/None
    fitness_center: bool = False
    fitness_details: Optional[str] = None
    spa: bool = False
    spa_details: Optional[str] = None
    business_center: bool = False
    parking_details: Optional[str] = None
    parking_cost: Optional[float] = None
    resort_fee: Optional[float] = None
    club_lounge: bool = False
    other_amenities: List[str] = field(default_factory=list)


@dataclass
class HotelRoom:
    """Data class for hotel room types."""
    room_type: str
    size_sf: Optional[float] = None
    size_metric: Optional[str] = None  # "sf" or "m2"
    description: Optional[str] = None
    photo_url: Optional[str] = None


@dataclass
class HotelMeetingSpace:
    """Data class for meeting space information."""
    total_space_sf: Optional[float] = None
    total_rooms: Optional[int] = None
    largest_room_sf: Optional[float] = None
    largest_room_capacity: Optional[int] = None
    meeting_space_per_key: Optional[float] = None  # SF per room


@dataclass
class HotelReview:
    """Data class for hotel review information."""
    platform: str  # e.g., "Google", "TripAdvisor", "Booking.com"
    score: float
    total_reviews: int
    last_updated: datetime = field(default_factory=datetime.now)
    common_themes: List[str] = field(default_factory=list)


@dataclass
class Hotel:
    """
    Main data class for hotel information in the CompSet analysis.
    """
    # Basic Info
    name: str
    address: str
    city: str
    state: str
    country: str
    website: Optional[str] = None
    brand_affiliation: Optional[str] = None
    chain_scale: Optional[str] = None
    owner: Optional[str] = None
    management_company: Optional[str] = None
    year_built: Optional[int] = None
    year_renovated: Optional[int] = None
    
    # Physical Characteristics
    room_count: Optional[int] = None
    suite_count: Optional[int] = None
    suite_percentage: Optional[float] = None
    room_types: List[HotelRoom] = field(default_factory=list)
    meeting_space: HotelMeetingSpace = field(default_factory=HotelMeetingSpace)
    
    # Amenities
    amenities: HotelAmenities = field(default_factory=HotelAmenities)
    
    # Location
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_from_subject: Optional[float] = None  # In miles
    nearby_demand_generators: List[str] = field(default_factory=list)
    
    # Reviews
    reviews: List[HotelReview] = field(default_factory=list)
    
    # Photos
    exterior_photo_url: Optional[str] = None
    guestroom_photo_url: Optional[str] = None
    
    # Sources - tracking where information was found
    sources: Dict[str, str] = field(default_factory=dict)
    
    # Is this the subject hotel?
    is_subject: bool = False
    
    def __post_init__(self):
        """Calculate fields after initialization if possible."""
        if self.room_count and self.suite_count and not self.suite_percentage:
            self.suite_percentage = (self.suite_count / self.room_count) * 100 if self.room_count > 0 else 0
        
        if self.meeting_space.total_space_sf and self.room_count and not self.meeting_space.meeting_space_per_key:
            self.meeting_space.meeting_space_per_key = self.meeting_space.total_space_sf / self.room_count if self.room_count > 0 else 0
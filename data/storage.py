#hotel_compset_analyzer/data/storage.py
"""
Data storage and persistence for the CompSet Analyzer.
Handles saving and loading competitive set data.
"""

import os
import json
import pickle
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd

from data.hotel import Hotel


class CompSetStorage:
    """Class for managing CompSet data persistence."""
    
    def __init__(self, base_dir: str = "./saved_compsets"):
        """Initialize with base directory for saved data."""
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
    
    def save_compset(self, subject_hotel: Hotel, competitor_hotels: List[Hotel], 
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save a competitive set analysis to disk.
        
        Args:
            subject_hotel: The subject hotel data
            competitor_hotels: List of competitor hotel data
            metadata: Additional metadata about the analysis
            
        Returns:
            The filename where data was saved
        """
        if not metadata:
            metadata = {}
        
        # Create timestamp and sanitized hotel name for the filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hotel_name_safe = subject_hotel.name.replace(" ", "_").replace("/", "-").lower()
        
        # Create save directory
        save_dir = os.path.join(self.base_dir, f"{hotel_name_safe}_{timestamp}")
        os.makedirs(save_dir, exist_ok=True)
        
        # Prepare data for serialization
        compset_data = {
            "subject_hotel": self._hotel_to_dict(subject_hotel),
            "competitor_hotels": [self._hotel_to_dict(hotel) for hotel in competitor_hotels],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "subject_name": subject_hotel.name,
                "subject_address": subject_hotel.address,
                "competitor_count": len(competitor_hotels),
                **metadata
            }
        }
        
        # Save as JSON
        json_path = os.path.join(save_dir, "compset_data.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(compset_data, f, indent=2, default=str)
        
        # Save as pickle for full object preservation
        pickle_path = os.path.join(save_dir, "compset_data.pkl")
        with open(pickle_path, 'wb') as f:
            pickle.dump({"subject_hotel": subject_hotel, "competitor_hotels": competitor_hotels, "metadata": metadata}, f)
        
        return save_dir
    
    def load_compset(self, compset_dir: str) -> Dict[str, Any]:
        """
        Load a competitive set analysis from disk.
        
        Args:
            compset_dir: Directory containing the saved compset
            
        Returns:
            Dictionary containing the subject hotel, competitor hotels, and metadata
        """
        pickle_path = os.path.join(compset_dir, "compset_data.pkl")
        
        with open(pickle_path, 'rb') as f:
            return pickle.load(f)
    
    def list_saved_compsets(self) -> List[Dict[str, Any]]:
        """
        List all saved competitive sets with their metadata.
        
        Returns:
            List of dictionaries with compset metadata
        """
        compsets = []
        
        for item in os.listdir(self.base_dir):
            item_path = os.path.join(self.base_dir, item)
            
            if os.path.isdir(item_path):
                json_path = os.path.join(item_path, "compset_data.json")
                
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                        compsets.append({
                            "dir_name": item,
                            "full_path": item_path,
                            "subject_name": data["metadata"]["subject_name"],
                            "created_at": data["metadata"]["created_at"],
                            "competitor_count": data["metadata"]["competitor_count"]
                        })
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Error loading compset {item}: {e}")
        
        # Sort by creation date (newest first)
        compsets.sort(key=lambda x: x["created_at"], reverse=True)
        return compsets
    
    def export_to_excel(self, compset_dir: str, output_path: Optional[str] = None) -> str:
        """
        Export competitive set data to Excel.
        
        Args:
            compset_dir: Directory containing the saved compset
            output_path: Path to save the Excel file (optional)
            
        Returns:
            Path to the created Excel file
        """
        data = self.load_compset(compset_dir)
        
        if not output_path:
            output_path = os.path.join(compset_dir, "compset_analysis.xlsx")
        
        # Create Excel writer
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # Create main comparison sheet
            self._create_comparison_sheet(writer, data)
            
            # Create amenities sheet
            self._create_amenities_sheet(writer, data)
            
            # Create meeting space sheet
            self._create_meeting_space_sheet(writer, data)
            
            # Create reviews sheet
            self._create_reviews_sheet(writer, data)
            
            # Create metadata sheet
            self._create_metadata_sheet(writer, data)
        
        return output_path
    
    def _hotel_to_dict(self, hotel: Hotel) -> Dict[str, Any]:
        """Convert a Hotel object to a dictionary for serialization."""
        return {k: v for k, v in hotel.__dict__.items()}
    
    def _create_comparison_sheet(self, writer, data):
        """Create the main comparison sheet in Excel."""
        subject = data["subject_hotel"]
        competitors = data["competitor_hotels"]
        
        # Create DataFrame for comparison
        hotels = [subject] + competitors
        df = pd.DataFrame([{
            "Hotel Name": h.name,
            "Address": f"{h.address}, {h.city}, {h.state}",
            "Brand": h.brand_affiliation,
            "Chain Scale": h.chain_scale,
            "Room Count": h.room_count,
            "Suite %": h.suite_percentage,
            "Year Built": h.year_built,
            "Year Renovated": h.year_renovated,
            "Distance (mi)": h.distance_from_subject if not h.is_subject else 0,
            "Website": h.website
        } for h in hotels])
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Comparison", index=False)
    
    def _create_amenities_sheet(self, writer, data):
        """Create amenities comparison sheet in Excel."""
        subject = data["subject_hotel"]
        competitors = data["competitor_hotels"]
        
        # Create DataFrame for amenities
        hotels = [subject] + competitors
        df = pd.DataFrame([{
            "Hotel Name": h.name,
            "Restaurants": len(h.amenities.restaurants),
            "Bars/Lounges": len(h.amenities.bars_lounges),
            "Pool": h.amenities.pool,
            "Fitness Center": "Yes" if h.amenities.fitness_center else "No",
            "Spa": "Yes" if h.amenities.spa else "No",
            "Business Center": "Yes" if h.amenities.business_center else "No",
            "Club Lounge": "Yes" if h.amenities.club_lounge else "No",
            "Parking": h.amenities.parking_details,
            "Parking Cost": h.amenities.parking_cost,
            "Resort Fee": h.amenities.resort_fee,
            "Other Amenities": ", ".join(h.amenities.other_amenities)
        } for h in hotels])
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Amenities", index=False)
    
    def _create_meeting_space_sheet(self, writer, data):
        """Create meeting space comparison sheet in Excel."""
        subject = data["subject_hotel"]
        competitors = data["competitor_hotels"]
        
        # Create DataFrame for meeting space
        hotels = [subject] + competitors
        df = pd.DataFrame([{
            "Hotel Name": h.name,
            "Total Space (SF)": h.meeting_space.total_space_sf,
            "# of Meeting Rooms": h.meeting_space.total_rooms,
            "Largest Room (SF)": h.meeting_space.largest_room_sf,
            "Largest Room Capacity": h.meeting_space.largest_room_capacity,
            "SF per Key": h.meeting_space.meeting_space_per_key
        } for h in hotels])
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Meeting Space", index=False)
    
    def _create_reviews_sheet(self, writer, data):
        """Create reviews comparison sheet in Excel."""
        subject = data["subject_hotel"]
        competitors = data["competitor_hotels"]
        
        # Create DataFrame for reviews
        hotels = [subject] + competitors
        rows = []
        
        for h in hotels:
            for review in h.reviews:
                rows.append({
                    "Hotel Name": h.name,
                    "Platform": review.platform,
                    "Score": review.score,
                    "Total Reviews": review.total_reviews,
                    "Last Updated": review.last_updated,
                    "Common Themes": ", ".join(review.common_themes)
                })
        
        df = pd.DataFrame(rows)
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Reviews", index=False)
    
    def _create_metadata_sheet(self, writer, data):
        """Create metadata sheet in Excel."""
        metadata = data["metadata"]
        
        # Convert metadata to DataFrame
        df = pd.DataFrame([{"Key": k, "Value": v} for k, v in metadata.items()])
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Metadata", index=False)
#hotel_compset_analyzer/output/matrix_generator.py
"""
Matrix generator for the Hotel CompSet Analyzer.
Creates comparison matrices similar to the example in image 2.
"""

import os
import pandas as pd
from typing import Dict, List, Any, Optional
import logging

from data.hotel import Hotel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MatrixGenerator:
    """Matrix generator for the Hotel CompSet Analyzer."""
    
    def __init__(self, output_dir: str = "./output"):
        """
        Initialize the matrix generator.
        
        Args:
            output_dir: Directory where matrices will be saved
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def create_comparison_matrix(self, subject_hotel: Hotel, competitor_hotels: List[Hotel],
                               output_file: Optional[str] = None) -> Optional[str]:
        """
        Create a comparison matrix for the subject hotel and competitor hotels.
        
        Args:
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
            output_file: Path to save the output file (optional)
            
        Returns:
            Path to the created matrix file or None if matrix could not be created
        """
        # Set default output file if not provided
        if not output_file:
            output_file = os.path.join(self.output_dir, "comparison_matrix.xlsx")
        
        try:
            # Create Excel writer
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                # Get all hotels
                all_hotels = [subject_hotel] + competitor_hotels
                
                # Create main comparison sheet
                self._create_main_comparison(writer, all_hotels)
                
                # Create rooms sheet
                self._create_rooms_comparison(writer, all_hotels)
                
                # Create amenities sheet
                self._create_amenities_comparison(writer, all_hotels)
                
                # Create meeting space sheet
                self._create_meeting_space_comparison(writer, all_hotels)
                
                # Create reviews sheet
                self._create_reviews_comparison(writer, all_hotels)
                
                # Format the Excel file
                self._format_excel(writer, all_hotels)
            
            logger.info(f"Comparison matrix created and saved to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error creating comparison matrix: {e}")
            return None
    
    def _create_main_comparison(self, writer, hotels: List[Hotel]):
        """
        Create the main comparison sheet.
        
        Args:
            writer: Excel writer
            hotels: List of hotels (subject hotel first)
        """
        # Extract data for the main comparison
        data = []
        
        for hotel in hotels:
            data.append({
                "Hotel Name": hotel.name + (" (Subject)" if hotel.is_subject else ""),
                "Brand": hotel.brand_affiliation or "",
                "Chain Scale": hotel.chain_scale or "",
                "Address": hotel.address,
                "City, State": f"{hotel.city}, {hotel.state}",
                "Country": hotel.country,
                "Year Built": hotel.year_built,
                "Year Renovated": hotel.year_renovated,
                "Room Count": hotel.room_count,
                "Distance (mi)": hotel.distance_from_subject if not hotel.is_subject else 0,
                "Owner": hotel.owner or "",
                "Management": hotel.management_company or ""
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Main Comparison", index=False)
    
    def _create_rooms_comparison(self, writer, hotels: List[Hotel]):
        """
        Create the rooms comparison sheet.
        
        Args:
            writer: Excel writer
            hotels: List of hotels (subject hotel first)
        """
        # Extract data for rooms comparison
        data = []
        
        for hotel in hotels:
            # Calculate suite mix
            suite_mix = f"{hotel.suite_percentage:.1f}%" if hotel.suite_percentage is not None else ""
            
            # Get room types
            room_types = []
            for rt in hotel.room_types:
                size_str = f"{rt.size_sf} {rt.size_metric}" if rt.size_sf else ""
                room_types.append(f"{rt.room_type} ({size_str})")
            
            data.append({
                "Hotel Name": hotel.name + (" (Subject)" if hotel.is_subject else ""),
                "Room Count": hotel.room_count,
                "Suite Count": hotel.suite_count,
                "Suite Mix": suite_mix,
                "Room Types": ", ".join(room_types) if room_types else ""
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Rooms", index=False)
    
    def _create_amenities_comparison(self, writer, hotels: List[Hotel]):
        """
        Create the amenities comparison sheet.
        
        Args:
            writer: Excel writer
            hotels: List of hotels (subject hotel first)
        """
        # Extract data for amenities comparison
        data = []
        
        for hotel in hotels:
            # Get amenities
            amenities = hotel.amenities or None
            
            # Restaurant count
            restaurant_count = len(amenities.restaurants) if amenities and amenities.restaurants else 0
            
            # Restaurant names
            restaurant_names = []
            if amenities and amenities.restaurants:
                for r in amenities.restaurants:
                    if isinstance(r, dict):
                        name = r.get("name", "")
                        r_type = r.get("type", "")
                        restaurant_names.append(f"{name} ({r_type})" if r_type else name)
                    else:
                        restaurant_names.append(r)
            
            data.append({
                "Hotel Name": hotel.name + (" (Subject)" if hotel.is_subject else ""),
                "Restaurants": restaurant_count,
                "Restaurant Details": ", ".join(restaurant_names) if restaurant_names else "",
                "Bars/Lounges": ", ".join(amenities.bars_lounges) if amenities and amenities.bars_lounges else "",
                "Pool": amenities.pool if amenities else "",
                "Fitness Center": "Yes" if amenities and amenities.fitness_center else "No",
                "Spa": "Yes" if amenities and amenities.spa else "No",
                "Business Center": "Yes" if amenities and amenities.business_center else "No",
                "Club Lounge": "Yes" if amenities and amenities.club_lounge else "No",
                "Parking": amenities.parking_details if amenities else "",
                "Parking Cost": f"${amenities.parking_cost}" if amenities and amenities.parking_cost else "",
                "Resort Fee": f"${amenities.resort_fee}" if amenities and amenities.resort_fee else "",
                "Other Amenities": ", ".join(amenities.other_amenities) if amenities and amenities.other_amenities else ""
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Amenities", index=False)
    
    def _create_meeting_space_comparison(self, writer, hotels: List[Hotel]):
        """
        Create the meeting space comparison sheet.
        
        Args:
            writer: Excel writer
            hotels: List of hotels (subject hotel first)
        """
        # Extract data for meeting space comparison
        data = []
        
        for hotel in hotels:
            # Get meeting space
            meeting_space = hotel.meeting_space or None
            
            data.append({
                "Hotel Name": hotel.name + (" (Subject)" if hotel.is_subject else ""),
                "Total Meeting Space (SF)": meeting_space.total_space_sf if meeting_space else "",
                "Number of Meeting Rooms": meeting_space.total_rooms if meeting_space else "",
                "Largest Room (SF)": meeting_space.largest_room_sf if meeting_space else "",
                "Largest Room Capacity": meeting_space.largest_room_capacity if meeting_space else "",
                "SF per Key": meeting_space.meeting_space_per_key if meeting_space else ""
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Meeting Space", index=False)
    
    def _create_reviews_comparison(self, writer, hotels: List[Hotel]):
        """
        Create the reviews comparison sheet.
        
        Args:
            writer: Excel writer
            hotels: List of hotels (subject hotel first)
        """
        # Extract data for reviews comparison
        data = []
        
        for hotel in hotels:
            # Initialize review scores
            tripadvisor_score = ""
            tripadvisor_reviews = ""
            google_score = ""
            google_reviews = ""
            booking_score = ""
            booking_reviews = ""
            
            # Common themes
            themes = []
            
            # Process reviews
            if hotel.reviews:
                for review in hotel.reviews:
                    platform = review.platform.lower() if review.platform else ""
                    
                    if "tripadvisor" in platform:
                        tripadvisor_score = f"{review.score:.1f}" if review.score else ""
                        tripadvisor_reviews = review.total_reviews
                        themes.extend(review.common_themes or [])
                    elif "google" in platform:
                        google_score = f"{review.score:.1f}" if review.score else ""
                        google_reviews = review.total_reviews
                        themes.extend(review.common_themes or [])
                    elif "booking" in platform:
                        booking_score = f"{review.score:.1f}" if review.score else ""
                        booking_reviews = review.total_reviews
                        themes.extend(review.common_themes or [])
            
            data.append({
                "Hotel Name": hotel.name + (" (Subject)" if hotel.is_subject else ""),
                "TripAdvisor Score": tripadvisor_score,
                "TripAdvisor Reviews": tripadvisor_reviews,
                "Google Score": google_score,
                "Google Reviews": google_reviews,
                "Booking.com Score": booking_score,
                "Booking.com Reviews": booking_reviews,
                "Common Themes": ", ".join(themes[:5]) if themes else ""  # Limit to top 5 themes
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Reviews", index=False)
    
    def _format_excel(self, writer, hotels: List[Hotel]):
        """
        Format the Excel file.
        
        Args:
            writer: Excel writer
            hotels: List of hotels
        """
        # Get workbook and add formats
        workbook = writer.book
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        subject_format = workbook.add_format({
            'bg_color': '#FFFF99',
            'border': 1
        })
        
        border_format = workbook.add_format({
            'border': 1
        })
        
        # Format each worksheet
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            
            # Format the header row
            for col_num, value in enumerate(worksheet.table.columns):
                worksheet.write(0, col_num, value, header_format)
            
            # Format the subject hotel row (always the first data row)
            for col_num in range(len(worksheet.table.columns)):
                worksheet.write(1, col_num, worksheet.table[1][col_num], subject_format)
            
            # Format the rest of the cells with borders
            for row_num in range(2, len(hotels) + 1):
                for col_num in range(len(worksheet.table.columns)):
                    worksheet.write(row_num, col_num, worksheet.table[row_num][col_num], border_format)
            
            # Adjust column widths
            worksheet.set_column(0, 0, 30)  # Hotel Name
            worksheet.set_column(1, len(worksheet.table.columns) - 1, 15)  # Other columns
            
            # Freeze the top row
            worksheet.freeze_panes(1, 0)
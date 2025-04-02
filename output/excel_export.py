#hotel_compset_analyzer/output/excel_export.py
"""
Excel exporter for the Hotel CompSet Analyzer.
"""

import os
import pandas as pd
from typing import Dict, List, Any, Optional
import logging

from data.hotel import Hotel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ExcelExporter:
    """Excel exporter for the Hotel CompSet Analyzer."""
    
    def export(self, subject_hotel: Hotel, competitor_hotels: List[Hotel], 
              output_file: str) -> bool:
        """
        Export hotel data to Excel.
        
        Args:
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
            output_file: Path to save the Excel file
            
        Returns:
            Boolean indicating success
        """
        try:
            # Create Excel writer
            with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
                # Create summary sheet
                self._create_summary_sheet(writer, subject_hotel, competitor_hotels)
                
                # Create main comparison sheet
                self._create_main_comparison(writer, subject_hotel, competitor_hotels)
                
                # Create amenities sheet
                self._create_amenities_sheet(writer, subject_hotel, competitor_hotels)
                
                # Create rooms sheet
                self._create_rooms_sheet(writer, subject_hotel, competitor_hotels)
                
                # Create meeting space sheet
                self._create_meeting_space_sheet(writer, subject_hotel, competitor_hotels)
                
                # Create reviews sheet
                self._create_reviews_sheet(writer, subject_hotel, competitor_hotels)
                
                # Create sources sheet
                self._create_sources_sheet(writer, subject_hotel, competitor_hotels)
                
                # Format the workbook
                self._format_workbook(writer, subject_hotel, competitor_hotels)
            
            logger.info(f"Exported to Excel: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {e}")
            return False
    
    def _create_summary_sheet(self, writer, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Create the summary sheet.
        
        Args:
            writer: Excel writer
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
        # Create DataFrame with a single column for summary text
        data = [
            ["CompSet Analysis Summary"],
            [""],
            [f"Subject Hotel: {subject_hotel.name}"],
            [f"Location: {subject_hotel.city}, {subject_hotel.state}, {subject_hotel.country}"],
            [f"Number of Competitor Hotels: {len(competitor_hotels)}"],
            [""],
            ["Competitor Hotels:"]
        ]
        
        # Add competitor hotels
        for i, hotel in enumerate(competitor_hotels, 1):
            distance = hotel.distance_from_subject
            distance_str = f"{distance:.2f} miles" if distance is not None else "Unknown"
            data.append([f"{i}. {hotel.name} ({distance_str})"])
        
        # Add timestamp
        data.append([""])
        from datetime import datetime
        data.append([f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"])
        
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=["Summary"])
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Summary", index=False, header=False)
    
    def _create_main_comparison(self, writer, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Create the main comparison sheet.
        
        Args:
            writer: Excel writer
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
        # Create data for all hotels
        all_hotels = [subject_hotel] + competitor_hotels
        data = []
        
        for hotel in all_hotels:
            data.append({
                "Hotel Name": hotel.name + (" (Subject)" if hotel.is_subject else ""),
                "Brand": hotel.brand_affiliation or "",
                "Chain Scale": hotel.chain_scale or "",
                "Address": hotel.address,
                "City": hotel.city,
                "State": hotel.state,
                "Distance from Subject": hotel.distance_from_subject if not hotel.is_subject else 0,
                "Year Built": hotel.year_built,
                "Year Renovated": hotel.year_renovated,
                "Owner": hotel.owner or "",
                "Management": hotel.management_company or ""
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Hotel Overview", index=False)
    
    def _create_amenities_sheet(self, writer, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Create the amenities sheet.
        
        Args:
            writer: Excel writer
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
        # Create data for all hotels
        all_hotels = [subject_hotel] + competitor_hotels
        data = []
        
        for hotel in all_hotels:
            amenities = hotel.amenities or None
            
            data.append({
                "Hotel Name": hotel.name + (" (Subject)" if hotel.is_subject else ""),
                "Restaurant Count": len(amenities.restaurants) if amenities and amenities.restaurants else 0,
                "Bar/Lounge Count": len(amenities.bars_lounges) if amenities and amenities.bars_lounges else 0,
                "Pool": amenities.pool if amenities else "",
                "Fitness Center": "Yes" if amenities and amenities.fitness_center else "No",
                "Spa": "Yes" if amenities and amenities.spa else "No",
                "Business Center": "Yes" if amenities and amenities.business_center else "No",
                "Club Lounge": "Yes" if amenities and amenities.club_lounge else "No",
                "Parking": amenities.parking_details if amenities else "",
                "Parking Cost": amenities.parking_cost if amenities and amenities.parking_cost else "",
                "Resort Fee": amenities.resort_fee if amenities and amenities.resort_fee else "",
                "Other Amenities": ", ".join(amenities.other_amenities) if amenities and amenities.other_amenities else ""
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Amenities", index=False)
    
    def _create_rooms_sheet(self, writer, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Create the rooms sheet.
        
        Args:
            writer: Excel writer
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
        # Create data for all hotels
        all_hotels = [subject_hotel] + competitor_hotels
        data = []
        
        for hotel in all_hotels:
            # Calculate suite mix
            suite_mix = hotel.suite_percentage if hotel.suite_percentage is not None else None
            
            # Get room types as comma separated list
            room_types = []
            for rt in hotel.room_types:
                room_types.append(rt.room_type)
            
            data.append({
                "Hotel Name": hotel.name + (" (Subject)" if hotel.is_subject else ""),
                "Room Count": hotel.room_count,
                "Suite Count": hotel.suite_count,
                "Suite Mix (%)": suite_mix,
                "Room Types": ", ".join(room_types) if room_types else ""
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Rooms", index=False)
    
    def _create_meeting_space_sheet(self, writer, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Create the meeting space sheet.
        
        Args:
            writer: Excel writer
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
        # Create data for all hotels
        all_hotels = [subject_hotel] + competitor_hotels
        data = []
        
        for hotel in all_hotels:
            meeting_space = hotel.meeting_space or None
            
            data.append({
                "Hotel Name": hotel.name + (" (Subject)" if hotel.is_subject else ""),
                "Total Space (SF)": meeting_space.total_space_sf if meeting_space else None,
                "# of Meeting Rooms": meeting_space.total_rooms if meeting_space else None,
                "Largest Room (SF)": meeting_space.largest_room_sf if meeting_space else None,
                "Largest Room Capacity": meeting_space.largest_room_capacity if meeting_space else None,
                "SF per Key": meeting_space.meeting_space_per_key if meeting_space else None
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Meeting Space", index=False)
    
    def _create_reviews_sheet(self, writer, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Create the reviews sheet.
        
        Args:
            writer: Excel writer
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
        # Create data with all reviews
        data = []
        
        for hotel in [subject_hotel] + competitor_hotels:
            is_subject = hotel.is_subject
            
            for review in hotel.reviews:
                data.append({
                    "Hotel Name": hotel.name + (" (Subject)" if is_subject else ""),
                    "Platform": review.platform,
                    "Score": review.score,
                    "Total Reviews": review.total_reviews,
                    "Last Updated": review.last_updated.strftime("%Y-%m-%d") if hasattr(review.last_updated, "strftime") else "",
                    "Common Themes": ", ".join(review.common_themes) if review.common_themes else ""
                })
        
        # If no reviews, add a placeholder row
        if not data:
            data.append({
                "Hotel Name": "No review data available",
                "Platform": "",
                "Score": None,
                "Total Reviews": None,
                "Last Updated": "",
                "Common Themes": ""
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Reviews", index=False)
    
    def _create_sources_sheet(self, writer, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Create the sources sheet.
        
        Args:
            writer: Excel writer
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
        # Create data for all hotels
        all_hotels = [subject_hotel] + competitor_hotels
        data = []
        
        for hotel in all_hotels:
            sources = hotel.sources or {}
            
            for data_type, source_url in sources.items():
                data.append({
                    "Hotel Name": hotel.name + (" (Subject)" if hotel.is_subject else ""),
                    "Data Type": data_type,
                    "Source URL": source_url
                })
        
        # If no sources, add a placeholder row
        if not data:
            data.append({
                "Hotel Name": "No source data available",
                "Data Type": "",
                "Source URL": ""
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Write to Excel
        df.to_excel(writer, sheet_name="Sources", index=False)
    
    def _format_workbook(self, writer, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Format the workbook.
        
        Args:
            writer: Excel writer
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
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
            'bg_color': '#FFFFCC',
            'border': 1
        })
        
        # Format each worksheet
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            
            # Auto-fit columns
            for i, col in enumerate(worksheet.table.columns):
                max_len = len(col) + 2  # Add a little extra space
                worksheet.set_column(i, i, max_len)
            
            # Format header row
            for col_num, col in enumerate(worksheet.table.columns):
                worksheet.write(0, col_num, col, header_format)
            
            # Format subject hotel row if present
            if sheet_name not in ["Reviews", "Sources"]:
                # First data row is the subject hotel
                for col_num in range(len(worksheet.table.columns)):
                    worksheet.write(1, col_num, worksheet.table[1][col_num], subject_format)
            else:
                # For sheets with multiple rows per hotel, find subject hotel rows
                for row_num in range(1, len(worksheet.table)):
                    cell_value = worksheet.table[row_num][0]
                    if isinstance(cell_value, str) and "(Subject)" in cell_value:
                        for col_num in range(len(worksheet.table.columns)):
                            worksheet.write(row_num, col_num, worksheet.table[row_num][col_num], subject_format)
            
            # Freeze top row
            worksheet.freeze_panes(1, 0)
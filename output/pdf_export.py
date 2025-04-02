#hotel_compset_analyzer/output/pdf_exporter.py
"""
PDF exporter for the Hotel CompSet Analyzer.
"""

import os
from typing import Dict, List, Any, Optional
import logging
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image

from data.hotel import Hotel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PDFExporter:
    """PDF exporter for the Hotel CompSet Analyzer."""
    
    def export(self, subject_hotel: Hotel, competitor_hotels: List[Hotel], 
              output_file: str) -> bool:
        """
        Export hotel data to PDF.
        
        Args:
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
            output_file: Path to save the PDF file
            
        Returns:
            Boolean indicating success
        """
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                output_file,
                pagesize=landscape(letter),
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = styles["Title"]
            heading_style = styles["Heading1"]
            normal_style = styles["Normal"]
            
            # Create custom styles
            table_title_style = ParagraphStyle(
                'TableTitle',
                parent=styles['Heading2'],
                spaceAfter=10
            )
            
            # Create content elements
            elements = []
            
            # Add title
            elements.append(Paragraph(f"Hotel CompSet Analysis: {subject_hotel.name}", title_style))
            elements.append(Spacer(1, 0.25*inch))
            
            # Add summary section
            elements.append(Paragraph("Summary", heading_style))
            summary_text = f"""
            This analysis compares {subject_hotel.name} with {len(competitor_hotels)} competitor hotels in the {subject_hotel.city}, {subject_hotel.state} market.
            """
            elements.append(Paragraph(summary_text, normal_style))
            elements.append(Spacer(1, 0.25*inch))
            
            # Add hotel overview table
            elements.append(Paragraph("Hotel Overview", table_title_style))
            overview_table = self._create_overview_table(subject_hotel, competitor_hotels)
            elements.append(overview_table)
            elements.append(Spacer(1, 0.25*inch))
            
            # Add rooms comparison table
            elements.append(Paragraph("Rooms Comparison", table_title_style))
            rooms_table = self._create_rooms_table(subject_hotel, competitor_hotels)
            elements.append(rooms_table)
            elements.append(Spacer(1, 0.25*inch))
            
            # Add amenities comparison table
            elements.append(Paragraph("Amenities Comparison", table_title_style))
            amenities_table = self._create_amenities_table(subject_hotel, competitor_hotels)
            elements.append(amenities_table)
            elements.append(Spacer(1, 0.25*inch))
            
            # Add meeting space comparison table
            elements.append(Paragraph("Meeting Space Comparison", table_title_style))
            meeting_table = self._create_meeting_space_table(subject_hotel, competitor_hotels)
            elements.append(meeting_table)
            elements.append(Spacer(1, 0.25*inch))
            
            # Build the PDF
            doc.build(elements)
            
            logger.info(f"Exported to PDF: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to PDF: {e}")
            return False
    
    def _create_overview_table(self, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Create the hotel overview table.
        
        Args:
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
            
        Returns:
            Table element
        """
        # Define column headers
        headers = [
            "Hotel Name", "Brand", "Chain Scale", "Year Built", 
            "Year Renovated", "Room Count", "Distance (mi)"
        ]
        
        # Create data rows
        data = [headers]
        
        # Add subject hotel
        subject_row = [
            f"{subject_hotel.name} (Subject)",
            subject_hotel.brand_affiliation or "",
            subject_hotel.chain_scale or "",
            str(subject_hotel.year_built) if subject_hotel.year_built else "",
            str(subject_hotel.year_renovated) if subject_hotel.year_renovated else "",
            str(subject_hotel.room_count) if subject_hotel.room_count else "",
            "0.00"
        ]
        data.append(subject_row)
        
        # Add competitor hotels
        for hotel in competitor_hotels:
            distance = hotel.distance_from_subject
            distance_str = f"{distance:.2f}" if distance is not None else "N/A"
            
            row = [
                hotel.name,
                hotel.brand_affiliation or "",
                hotel.chain_scale or "",
                str(hotel.year_built) if hotel.year_built else "",
                str(hotel.year_renovated) if hotel.year_renovated else "",
                str(hotel.room_count) if hotel.room_count else "",
                distance_str
            ]
            data.append(row)
        
        # Create table
        table = Table(data, repeatRows=1)
        
        # Add style
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightyellow),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (3, 1), (-1, -1), 'CENTER')  # Align numeric columns
        ])
        table.setStyle(table_style)
        
        return table
    
    def _create_rooms_table(self, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Create the rooms comparison table.
        
        Args:
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
            
        Returns:
            Table element
        """
        # Define column headers
        headers = ["Hotel Name", "Room Count", "Suite Count", "Suite Mix (%)", "Room Types"]
        
        # Create data rows
        data = [headers]
        
        # Add subject hotel
        suite_pct = subject_hotel.suite_percentage
        suite_pct_str = f"{suite_pct:.1f}" if suite_pct is not None else ""
        
        room_types = [rt.room_type for rt in subject_hotel.room_types] if subject_hotel.room_types else []
        
        subject_row = [
            f"{subject_hotel.name} (Subject)",
            str(subject_hotel.room_count) if subject_hotel.room_count else "",
            str(subject_hotel.suite_count) if subject_hotel.suite_count else "",
            suite_pct_str,
            ", ".join(room_types)
        ]
        data.append(subject_row)
        
        # Add competitor hotels
        for hotel in competitor_hotels:
            suite_pct = hotel.suite_percentage
            suite_pct_str = f"{suite_pct:.1f}" if suite_pct is not None else ""
            
            room_types = [rt.room_type for rt in hotel.room_types] if hotel.room_types else []
            
            row = [
                hotel.name,
                str(hotel.room_count) if hotel.room_count else "",
                str(hotel.suite_count) if hotel.suite_count else "",
                suite_pct_str,
                ", ".join(room_types)
            ]
            data.append(row)
        
        # Create table
        table = Table(data, repeatRows=1)
        
        # Add style
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightyellow),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 1), (3, -1), 'CENTER')  # Align numeric columns
        ])
        table.setStyle(table_style)
        
        return table
    
    def _create_amenities_table(self, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Create the amenities comparison table.
        
        Args:
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
            
        Returns:
            Table element
        """
        # Define column headers
        headers = [
            "Hotel Name", "Restaurants", "Pool", "Fitness Center", 
            "Spa", "Business Ctr", "Club Lounge", "Resort Fee"
        ]
        
        # Create data rows
        data = [headers]
        
        # Helper function to get amenity info
        def get_amenity_info(hotel):
            amenities = hotel.amenities
            
            if not amenities:
                return ["No", "No", "No", "No", "No", "N/A"]
            
            restaurant_count = len(amenities.restaurants) if amenities.restaurants else 0
            pool = amenities.pool or "No"
            fitness = "Yes" if amenities.fitness_center else "No"
            spa = "Yes" if amenities.spa else "No"
            business = "Yes" if amenities.business_center else "No"
            club = "Yes" if amenities.club_lounge else "No"
            resort_fee = f"${amenities.resort_fee}" if amenities.resort_fee else "None"
            
            return [str(restaurant_count), pool, fitness, spa, business, club, resort_fee]
        
        # Add subject hotel
        subject_amenities = get_amenity_info(subject_hotel)
        subject_row = [f"{subject_hotel.name} (Subject)"] + subject_amenities
        data.append(subject_row)
        
        # Add competitor hotels
        for hotel in competitor_hotels:
            amenities = get_amenity_info(hotel)
            row = [hotel.name] + amenities
            data.append(row)
        
        # Create table
        table = Table(data, repeatRows=1)
        
        # Add style
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightyellow),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER')  # Align all amenity columns
        ])
        table.setStyle(table_style)
        
        return table
    
    def _create_meeting_space_table(self, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Create the meeting space comparison table.
        
        Args:
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
            
        Returns:
            Table element
        """
        # Define column headers
        headers = [
            "Hotel Name", "Total Space (SF)", "# of Rooms", 
            "Largest Room (SF)", "SF per Key"
        ]
        
        # Create data rows
        data = [headers]
        
        # Add subject hotel
        ms = subject_hotel.meeting_space
        subject_row = [
            f"{subject_hotel.name} (Subject)",
            str(ms.total_space_sf) if ms and ms.total_space_sf else "",
            str(ms.total_rooms) if ms and ms.total_rooms else "",
            str(ms.largest_room_sf) if ms and ms.largest_room_sf else "",
            f"{ms.meeting_space_per_key:.1f}" if ms and ms.meeting_space_per_key else ""
        ]
        data.append(subject_row)
        
        # Add competitor hotels
        for hotel in competitor_hotels:
            ms = hotel.meeting_space
            row = [
                hotel.name,
                str(ms.total_space_sf) if ms and ms.total_space_sf else "",
                str(ms.total_rooms) if ms and ms.total_rooms else "",
                str(ms.largest_room_sf) if ms and ms.largest_room_sf else "",
                f"{ms.meeting_space_per_key:.1f}" if ms and ms.meeting_space_per_key else ""
            ]
            data.append(row)
        
        # Create table
        table = Table(data, repeatRows=1)
        
        # Add style
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, 1), colors.lightyellow),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER')  # Align numeric columns
        ])
        table.setStyle(table_style)
        
        return table
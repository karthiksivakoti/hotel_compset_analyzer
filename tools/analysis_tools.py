#hotel_compset_analyzer/tools/analysis_tools.py
"""
Data analysis tools for the Hotel CompSet Analyzer.
"""

import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalysisTools:
    """Data analysis tools for the CompSet Analyzer."""
    
    @staticmethod
    def calculate_statistics(subject_hotel: Dict[str, Any], competitor_hotels: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics for the competitive set.
        
        Args:
            subject_hotel: Subject hotel data
            competitor_hotels: List of competitor hotel data
            
        Returns:
            Dictionary with calculated statistics
        """
        # Extract key metrics for analysis
        metrics = []
        
        for hotel in [subject_hotel] + competitor_hotels:
            metrics.append({
                'name': hotel['name'],
                'is_subject': hotel == subject_hotel,
                'room_count': hotel.get('room_count'),
                'suite_percentage': hotel.get('suite_percentage'),
                'year_built': hotel.get('year_built'),
                'year_renovated': hotel.get('year_renovated'),
                'meeting_space_sf': hotel.get('meeting_space', {}).get('total_space_sf'),
                'meeting_space_per_key': hotel.get('meeting_space', {}).get('meeting_space_per_key'),
                'has_restaurant': len(hotel.get('amenities', {}).get('restaurants', [])) > 0,
                'has_pool': hotel.get('amenities', {}).get('pool') is not None,
                'has_fitness_center': hotel.get('amenities', {}).get('fitness_center', False),
                'has_spa': hotel.get('amenities', {}).get('spa', False),
                'has_club_lounge': hotel.get('amenities', {}).get('club_lounge', False),
                'parking_cost': hotel.get('amenities', {}).get('parking_cost'),
                'resort_fee': hotel.get('amenities', {}).get('resort_fee'),
                'review_score': AnalysisTools._get_average_review_score(hotel.get('reviews', []))
            })
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(metrics)
        
        # Filter out subject hotel for comp set calculations
        comp_df = df[~df['is_subject']]
        
        # Calculate statistics
        stats = {}
        
        # Calculate numeric statistics
        for column in ['room_count', 'suite_percentage', 'meeting_space_sf', 
                       'meeting_space_per_key', 'parking_cost', 'resort_fee', 'review_score']:
            if comp_df[column].notna().any():
                stats[f'{column}_avg'] = comp_df[column].mean()
                stats[f'{column}_median'] = comp_df[column].median()
                stats[f'{column}_min'] = comp_df[column].min()
                stats[f'{column}_max'] = comp_df[column].max()
        
        # Calculate amenity percentages
        for column in ['has_restaurant', 'has_pool', 'has_fitness_center', 'has_spa', 'has_club_lounge']:
            if comp_df[column].notna().any():
                stats[f'{column}_percentage'] = comp_df[column].mean() * 100
        
        # Calculate age and renovation statistics
        current_year = pd.Timestamp.now().year
        
        if comp_df['year_built'].notna().any():
            stats['avg_age'] = current_year - comp_df['year_built'].mean()
            stats['median_age'] = current_year - comp_df['year_built'].median()
        
        if comp_df['year_renovated'].notna().any():
            stats['avg_years_since_renovation'] = current_year - comp_df['year_renovated'].mean()
            stats['median_years_since_renovation'] = current_year - comp_df['year_renovated'].median()
        
        # Add sample size
        stats['comp_set_size'] = len(comp_df)
        
        # Calculate subject hotel's position relative to comp set
        subject_hotel_row = df[df['is_subject']]
        if not subject_hotel_row.empty:
            for column in ['room_count', 'suite_percentage', 'meeting_space_sf', 
                           'meeting_space_per_key', 'parking_cost', 'resort_fee', 'review_score']:
                if subject_hotel_row[column].notna().any() and comp_df[column].notna().any():
                    subject_value = subject_hotel_row[column].values[0]
                    if not pd.isna(subject_value):
                        comp_values = comp_df[column].dropna()
                        if len(comp_values) > 0:
                            percentile = sum(subject_value >= comp_values) / len(comp_values) * 100
                            stats[f'subject_{column}_percentile'] = percentile
        
        return stats
    
    @staticmethod
    def _get_average_review_score(reviews: List[Dict[str, Any]]) -> Optional[float]:
        """
        Calculate average review score across platforms.
        
        Args:
            reviews: List of review data by platform
            
        Returns:
            Average review score or None if no reviews
        """
        if not reviews:
            return None
        
        # Normalize all scores to a 5-point scale
        normalized_scores = []
        
        for review in reviews:
            score = review.get('score')
            if score is None:
                continue
                
            platform = review.get('platform', '').lower()
            
            # TripAdvisor uses 5-point scale
            if 'tripadvisor' in platform:
                normalized_scores.append(score)
            
            # Google uses 5-point scale
            elif 'google' in platform:
                normalized_scores.append(score)
            
            # Booking.com uses 10-point scale
            elif 'booking' in platform:
                normalized_scores.append(score / 2)
            
            # Hotels.com uses 10-point scale
            elif 'hotels.com' in platform:
                normalized_scores.append(score / 2)
            
            # Expedia uses 5-point scale
            elif 'expedia' in platform:
                normalized_scores.append(score)
            
            # For unknown platforms, assume 5-point scale
            else:
                normalized_scores.append(score)
        
        if normalized_scores:
            return sum(normalized_scores) / len(normalized_scores)
        
        return None
    
    @staticmethod
    def identify_market_positioning(subject_hotel: Dict[str, Any], 
                                   competitor_hotels: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Identify market positioning and differentiators.
        
        Args:
            subject_hotel: Subject hotel data
            competitor_hotels: List of competitor hotel data
            
        Returns:
            Dictionary with positioning analysis
        """
        # Get basic statistics
        stats = AnalysisTools.calculate_statistics(subject_hotel, competitor_hotels)
        
        # Initialize positioning analysis
        positioning = {
            "relative_size": "",
            "age_position": "",
            "amenity_strengths": [],
            "amenity_weaknesses": [],
            "differentiators": [],
            "review_position": ""
        }
        
        # Analyze size positioning
        subject_rooms = subject_hotel.get('room_count')
        avg_comp_rooms = stats.get('room_count_avg')
        
        if subject_rooms and avg_comp_rooms:
            if subject_rooms < avg_comp_rooms * 0.75:
                positioning["relative_size"] = "Smaller than average"
            elif subject_rooms > avg_comp_rooms * 1.25:
                positioning["relative_size"] = "Larger than average"
            else:
                positioning["relative_size"] = "Average size"
        
        # Analyze age positioning
        subject_year_built = subject_hotel.get('year_built')
        subject_year_renovated = subject_hotel.get('year_renovated')
        avg_age = stats.get('avg_age')
        avg_years_since_renovation = stats.get('avg_years_since_renovation')
        
        if subject_year_built and avg_age:
            current_year = pd.Timestamp.now().year
            subject_age = current_year - subject_year_built
            
            if subject_age < avg_age * 0.75:
                positioning["age_position"] = "Newer than average"
            elif subject_age > avg_age * 1.25:
                positioning["age_position"] = "Older than average"
            else:
                positioning["age_position"] = "Average age"
                
            # Check renovation as a modifier
            if subject_year_renovated and avg_years_since_renovation:
                subject_years_since_renovation = current_year - subject_year_renovated
                
                if subject_years_since_renovation < avg_years_since_renovation * 0.5:
                    positioning["age_position"] += " (recently renovated)"
        
        # Analyze amenity strengths and weaknesses
        amenity_fields = [
            ('has_restaurant', 'Restaurant'),
            ('has_pool', 'Pool'),
            ('has_fitness_center', 'Fitness Center'),
            ('has_spa', 'Spa'),
            ('has_club_lounge', 'Club Lounge')
        ]
        
        for field, name in amenity_fields:
            subject_has = subject_hotel.get('amenities', {}).get(field.replace('has_', ''), False)
            comp_percentage = stats.get(f'{field}_percentage')
            
            if subject_has and comp_percentage and comp_percentage < 50:
                positioning["amenity_strengths"].append(name)
                positioning["differentiators"].append(f"Offers {name} unlike most competitors")
            elif not subject_has and comp_percentage and comp_percentage > 75:
                positioning["amenity_weaknesses"].append(name)
        
        # Analyze meeting space
        subject_meeting_space_per_key = subject_hotel.get('meeting_space', {}).get('meeting_space_per_key')
        avg_meeting_space_per_key = stats.get('meeting_space_per_key_avg')
        
        if subject_meeting_space_per_key and avg_meeting_space_per_key:
            if subject_meeting_space_per_key > avg_meeting_space_per_key * 1.5:
                positioning["differentiators"].append("Significantly more meeting space than competitors")
            elif subject_meeting_space_per_key < avg_meeting_space_per_key * 0.5:
                positioning["differentiators"].append("Significantly less meeting space than competitors")
        
        # Analyze review position
        subject_review_score = AnalysisTools._get_average_review_score(subject_hotel.get('reviews', []))
        avg_review_score = stats.get('review_score_avg')
        
        if subject_review_score and avg_review_score:
            if subject_review_score >= avg_review_score + 0.5:
                positioning["review_position"] = "Higher than average"
            elif subject_review_score <= avg_review_score - 0.5:
                positioning["review_position"] = "Lower than average"
            else:
                positioning["review_position"] = "Average"
        
        return positioning
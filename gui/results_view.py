#hotel_compset_analyzer/gui/results_view.py
"""
Results display for the Hotel CompSet Analyzer.
"""

import tkinter as tk
from tkinter import ttk
import webbrowser
from typing import Dict, List, Any, Optional
import os

from data.hotel import Hotel


class ResultsNotebook(ttk.Notebook):
    """Notebook for displaying analysis results."""
    
    def __init__(self, parent):
        """
        Initialize the results notebook.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.pack(fill=tk.BOTH, expand=True)
        
        # Create the tab frames
        self.summary_frame = ttk.Frame(self)
        self.map_frame = ttk.Frame(self)
        self.comparison_frame = ttk.Frame(self)
        self.details_frame = ttk.Frame(self)
        
        # Add tabs
        self.add(self.summary_frame, text="Summary")
        self.add(self.map_frame, text="Map")
        self.add(self.comparison_frame, text="Comparison")
        self.add(self.details_frame, text="Hotel Details")
        
        # Initialize with empty content
        self._create_empty_content()
    
    def _create_empty_content(self):
        """Create initial empty content for tabs."""
        # Summary tab
        ttk.Label(self.summary_frame, text="No analysis results to display.").pack(pady=50)
        
        # Map tab
        ttk.Label(self.map_frame, text="No map available. Run analysis to generate a map.").pack(pady=50)
        
        # Comparison tab
        ttk.Label(self.comparison_frame, text="No comparison data available. Run analysis to generate comparisons.").pack(pady=50)
        
        # Details tab
        ttk.Label(self.details_frame, text="No hotel details available. Run analysis to see detailed information.").pack(pady=50)
    
    def clear(self):
        """Clear all results."""
        # Clear existing widgets
        for frame in [self.summary_frame, self.map_frame, self.comparison_frame, self.details_frame]:
            for widget in frame.winfo_children():
                widget.destroy()
        
        # Reinitialize empty content
        self._create_empty_content()
    
    def display_results(self, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Display analysis results.
        
        Args:
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
        # Clear existing widgets
        self.clear()
        
        # Display results in each tab
        self._display_summary(subject_hotel, competitor_hotels)
        self._display_map(subject_hotel, competitor_hotels)
        self._display_comparison(subject_hotel, competitor_hotels)
        self._display_details(subject_hotel, competitor_hotels)
    
    def _display_summary(self, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Display summary information.
        
        Args:
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
        # Clear frame
        for widget in self.summary_frame.winfo_children():
            widget.destroy()
        
        # Create main content frame
        content_frame = ttk.Frame(self.summary_frame, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(content_frame)
        header_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(
            header_frame,
            text=f"CompSet Analysis: {subject_hotel.name}",
            font=("Arial", 14, "bold")
        ).pack(side=tk.LEFT)
        
        # Summary text
        summary_frame = ttk.LabelFrame(content_frame, text="Summary", padding=10)
        summary_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Generate summary text
        summary_text = tk.Text(summary_frame, wrap=tk.WORD, width=80, height=15)
        summary_text.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(summary_text, command=summary_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        summary_text.config(yscrollcommand=scrollbar.set)
        
        # Add summary content
        summary_content = self._generate_summary_text(subject_hotel, competitor_hotels)
        summary_text.insert(tk.END, summary_content)
        summary_text.config(state=tk.DISABLED)
        
        # Statistics
        stats_frame = ttk.LabelFrame(content_frame, text="Key Statistics", padding=10)
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Add statistics grid
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X, expand=True)
        
        # Column headers
        ttk.Label(stats_grid, text="Metric", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        ttk.Label(stats_grid, text="Subject Hotel", font=("Arial", 10, "bold")).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=5
        )
        
        ttk.Label(stats_grid, text="CompSet Average", font=("Arial", 10, "bold")).grid(
            row=0, column=2, sticky=tk.W, padx=5, pady=5
        )
        
        ttk.Label(stats_grid, text="Difference", font=("Arial", 10, "bold")).grid(
            row=0, column=3, sticky=tk.W, padx=5, pady=5
        )
        
        # Calculate key statistics
        metrics = self._calculate_key_metrics(subject_hotel, competitor_hotels)
        
        # Add statistics rows
        row_idx = 1
        for metric_name, values in metrics.items():
            ttk.Label(stats_grid, text=metric_name).grid(
                row=row_idx, column=0, sticky=tk.W, padx=5, pady=2
            )
            
            ttk.Label(stats_grid, text=values["subject"]).grid(
                row=row_idx, column=1, sticky=tk.W, padx=5, pady=2
            )
            
            ttk.Label(stats_grid, text=values["average"]).grid(
                row=row_idx, column=2, sticky=tk.W, padx=5, pady=2
            )
            
            ttk.Label(stats_grid, text=values["difference"]).grid(
                row=row_idx, column=3, sticky=tk.W, padx=5, pady=2
            )
            
            row_idx += 1
    
    def _display_map(self, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Display map information.
        
        Args:
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
        # Clear frame
        for widget in self.map_frame.winfo_children():
            widget.destroy()
        
        # Create main content frame
        content_frame = ttk.Frame(self.map_frame, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Check if coordinates are available
        if not subject_hotel.latitude or not subject_hotel.longitude:
            ttk.Label(
                content_frame,
                text="Geographic coordinates not available for subject hotel. Cannot display map."
            ).pack(pady=50)
            return
        
        # Create map using MapGenerator and check if successful
        from output.map_generator import MapGenerator
        
        map_generator = MapGenerator()
        map_file = map_generator.create_map(subject_hotel, competitor_hotels)
        
        if map_file and os.path.exists(map_file):
            # Create a frame for the map
            map_label_frame = ttk.LabelFrame(content_frame, text="Competitive Set Map", padding=10)
            map_label_frame.pack(fill=tk.BOTH, expand=True, pady=10)
            
            # Add instructions
            ttk.Label(
                map_label_frame,
                text="Map generated successfully. Click the button below to open in your web browser."
            ).pack(pady=10)
            
            # Add open in browser button
            open_button = ttk.Button(
                map_label_frame,
                text="Open Map in Browser",
                command=lambda: webbrowser.open(f"file://{os.path.abspath(map_file)}")
            )
            open_button.pack(pady=10)
            
            # Add distance information
            distance_frame = ttk.LabelFrame(content_frame, text="Distance from Subject Hotel", padding=10)
            distance_frame.pack(fill=tk.X, pady=10)
            
            # Create treeview for distances
            distance_tree = ttk.Treeview(
                distance_frame,
                columns=("hotel", "distance"),
                show="headings",
                height=len(competitor_hotels)
            )
            distance_tree.pack(fill=tk.BOTH, expand=True)
            
            # Configure columns
            distance_tree.heading("hotel", text="Hotel")
            distance_tree.heading("distance", text="Distance (miles)")
            
            distance_tree.column("hotel", width=300)
            distance_tree.column("distance", width=100, anchor=tk.E)
            
            # Add data
            for hotel in sorted(competitor_hotels, key=lambda h: h.distance_from_subject or float('inf')):
                distance = hotel.distance_from_subject
                distance_str = f"{distance:.2f}" if distance is not None else "N/A"
                
                distance_tree.insert("", tk.END, values=(hotel.name, distance_str))
        else:
            ttk.Label(
                content_frame,
                text="Could not generate map. Geographic coordinates may be missing."
            ).pack(pady=50)
    
    def _display_comparison(self, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Display comparison information.
        
        Args:
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
        # Clear frame
        for widget in self.comparison_frame.winfo_children():
            widget.destroy()
        
        # Create main content frame
        content_frame = ttk.Frame(self.comparison_frame, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for different comparison views
        comparison_notebook = ttk.Notebook(content_frame)
        comparison_notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create tabs
        basic_frame = ttk.Frame(comparison_notebook)
        room_frame = ttk.Frame(comparison_notebook)
        amenities_frame = ttk.Frame(comparison_notebook)
        reviews_frame = ttk.Frame(comparison_notebook)
        
        comparison_notebook.add(basic_frame, text="Basic Info")
        comparison_notebook.add(room_frame, text="Rooms")
        comparison_notebook.add(amenities_frame, text="Amenities")
        comparison_notebook.add(reviews_frame, text="Reviews")
        
        # Basic info comparison
        self._create_basic_comparison(basic_frame, subject_hotel, competitor_hotels)
        
        # Room comparison
        self._create_room_comparison(room_frame, subject_hotel, competitor_hotels)
        
        # Amenities comparison
        self._create_amenities_comparison(amenities_frame, subject_hotel, competitor_hotels)
        
        # Reviews comparison
        self._create_reviews_comparison(reviews_frame, subject_hotel, competitor_hotels)
    
    def _display_details(self, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Display detailed hotel information.
        
        Args:
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
        # Clear frame
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
        # Create main content frame
        content_frame = ttk.Frame(self.details_frame, padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create hotel selector
        selector_frame = ttk.Frame(content_frame)
        selector_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(selector_frame, text="Select Hotel:").pack(side=tk.LEFT)
        
        # Create dropdown with all hotels
        all_hotels = [subject_hotel] + competitor_hotels
        hotel_names = [f"{h.name} {'(Subject)' if h.is_subject else ''}" for h in all_hotels]
        
        hotel_var = tk.StringVar()
        hotel_dropdown = ttk.Combobox(
            selector_frame,
            textvariable=hotel_var,
            values=hotel_names,
            width=50,
            state="readonly"
        )
        hotel_dropdown.pack(side=tk.LEFT, padx=5)
        hotel_dropdown.current(0)  # Select subject hotel initially
        
        # Create details frame
        details_frame = ttk.LabelFrame(content_frame, text="Hotel Details", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create scrollable text widget for details
        details_text = tk.Text(details_frame, wrap=tk.WORD, width=80, height=30)
        details_text.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(details_text, command=details_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        details_text.config(yscrollcommand=scrollbar.set)
        
        # Function to display hotel details
        def show_hotel_details(event=None):
            # Get selected index
            idx = hotel_dropdown.current()
            if idx < 0:
                return
            
            # Get hotel
            hotel = all_hotels[idx]
            
            # Clear text
            details_text.config(state=tk.NORMAL)
            details_text.delete(1.0, tk.END)
            
            # Display details
            details_content = self._generate_hotel_details(hotel)
            details_text.insert(tk.END, details_content)
            details_text.config(state=tk.DISABLED)
        
        # Bind selection change
        hotel_dropdown.bind("<<ComboboxSelected>>", show_hotel_details)
        
        # Show initial details
        show_hotel_details()
    
    def _create_basic_comparison(self, parent, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Create basic info comparison.
        
        Args:
            parent: Parent widget
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
        # Create treeview
        columns = ("name", "brand", "chain_scale", "year_built", "year_renovated", "room_count", "distance")
        
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.config(yscrollcommand=scrollbar.set)
        
        # Configure columns
        tree.heading("name", text="Hotel Name")
        tree.heading("brand", text="Brand")
        tree.heading("chain_scale", text="Chain Scale")
        tree.heading("year_built", text="Year Built")
        tree.heading("year_renovated", text="Year Renovated")
        tree.heading("room_count", text="Room Count")
        tree.heading("distance", text="Distance (mi)")
        
        tree.column("name", width=200)
        tree.column("brand", width=150)
        tree.column("chain_scale", width=100)
        tree.column("year_built", width=80, anchor=tk.E)
        tree.column("year_renovated", width=100, anchor=tk.E)
        tree.column("room_count", width=80, anchor=tk.E)
        tree.column("distance", width=80, anchor=tk.E)
        
        # Add subject hotel
        tree.insert(
            "",
            tk.END,
            values=(
                f"{subject_hotel.name} (Subject)",
                subject_hotel.brand_affiliation or "",
                subject_hotel.chain_scale or "",
                subject_hotel.year_built or "",
                subject_hotel.year_renovated or "",
                subject_hotel.room_count or "",
                "0.00"
            ),
            tags=("subject",)
        )
        
        # Add competitor hotels
        for hotel in competitor_hotels:
            distance = hotel.distance_from_subject
            distance_str = f"{distance:.2f}" if distance is not None else "N/A"
            
            tree.insert(
                "",
                tk.END,
                values=(
                    hotel.name,
                    hotel.brand_affiliation or "",
                    hotel.chain_scale or "",
                    hotel.year_built or "",
                    hotel.year_renovated or "",
                    hotel.room_count or "",
                    distance_str
                )
            )
        
        # Configure tag for subject hotel
        tree.tag_configure("subject", background="#FFFF99")
    
    def _create_room_comparison(self, parent, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Create room comparison.
        
        Args:
            parent: Parent widget
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
        # Create treeview
        columns = ("name", "room_count", "suite_count", "suite_percentage", "room_types")
        
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.config(yscrollcommand=scrollbar.set)
        
        # Configure columns
        tree.heading("name", text="Hotel Name")
        tree.heading("room_count", text="Room Count")
        tree.heading("suite_count", text="Suite Count")
        tree.heading("suite_percentage", text="Suite %")
        tree.heading("room_types", text="Room Types")
        
        tree.column("name", width=200)
        tree.column("room_count", width=80, anchor=tk.E)
        tree.column("suite_count", width=80, anchor=tk.E)
        tree.column("suite_percentage", width=80, anchor=tk.E)
        tree.column("room_types", width=300)
        
        # Add subject hotel
        suite_pct = subject_hotel.suite_percentage
        suite_pct_str = f"{suite_pct:.1f}%" if suite_pct is not None else ""
        
        room_types_str = ", ".join([rt.room_type for rt in subject_hotel.room_types]) if subject_hotel.room_types else ""
        
        tree.insert(
            "",
            tk.END,
            values=(
                f"{subject_hotel.name} (Subject)",
                subject_hotel.room_count or "",
                subject_hotel.suite_count or "",
                suite_pct_str,
                room_types_str
            ),
            tags=("subject",)
        )
        
        # Add competitor hotels
        for hotel in competitor_hotels:
            suite_pct = hotel.suite_percentage
            suite_pct_str = f"{suite_pct:.1f}%" if suite_pct is not None else ""
            
            room_types_str = ", ".join([rt.room_type for rt in hotel.room_types]) if hotel.room_types else ""
            
            tree.insert(
                "",
                tk.END,
                values=(
                    hotel.name,
                    hotel.room_count or "",
                    hotel.suite_count or "",
                    suite_pct_str,
                    room_types_str
                )
            )
        
        # Configure tag for subject hotel
        tree.tag_configure("subject", background="#FFFF99")
    
    def _create_amenities_comparison(self, parent, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Create amenities comparison.
        
        Args:
            parent: Parent widget
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
        # Create treeview
        columns = ("name", "restaurants", "pool", "fitness", "spa", "business", "parking", "resort_fee")
        
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.config(yscrollcommand=scrollbar.set)
        
        # Configure columns
        tree.heading("name", text="Hotel Name")
        tree.heading("restaurants", text="Restaurants")
        tree.heading("pool", text="Pool")
        tree.heading("fitness", text="Fitness")
        tree.heading("spa", text="Spa")
        tree.heading("business", text="Business Center")
        tree.heading("parking", text="Parking")
        tree.heading("resort_fee", text="Resort Fee")
        
        tree.column("name", width=200)
        tree.column("restaurants", width=80, anchor=tk.CENTER)
        tree.column("pool", width=80, anchor=tk.CENTER)
        tree.column("fitness", width=80, anchor=tk.CENTER)
        tree.column("spa", width=80, anchor=tk.CENTER)
        tree.column("business", width=100, anchor=tk.CENTER)
        tree.column("parking", width=120)
        tree.column("resort_fee", width=80, anchor=tk.E)
        
        # Helper to get amenity display value
        def get_amenity_value(hotel):
            if not hotel.amenities:
                return ("", "", "", "", "", "", "")
            
            restaurants = str(len(hotel.amenities.restaurants)) if hotel.amenities.restaurants else "0"
            pool = hotel.amenities.pool or "No"
            fitness = "Yes" if hotel.amenities.fitness_center else "No"
            spa = "Yes" if hotel.amenities.spa else "No"
            business = "Yes" if hotel.amenities.business_center else "No"
            parking = hotel.amenities.parking_details or ""
            
            resort_fee = f"${hotel.amenities.resort_fee}" if hotel.amenities.resort_fee else "None"
            
            return (restaurants, pool, fitness, spa, business, parking, resort_fee)
        
        # Add subject hotel
        amenities = get_amenity_value(subject_hotel)
        
        tree.insert(
            "",
            tk.END,
            values=(
                f"{subject_hotel.name} (Subject)",
                amenities[0],
                amenities[1],
                amenities[2],
                amenities[3],
                amenities[4],
                amenities[5],
                amenities[6]
            ),
            tags=("subject",)
        )
        
        # Add competitor hotels
        for hotel in competitor_hotels:
            amenities = get_amenity_value(hotel)
            
            tree.insert(
                "",
                tk.END,
                values=(
                    hotel.name,
                    amenities[0],
                    amenities[1],
                    amenities[2],
                    amenities[3],
                    amenities[4],
                    amenities[5],
                    amenities[6]
                )
            )
        
        # Configure tag for subject hotel
        tree.tag_configure("subject", background="#FFFF99")
    
    def _create_reviews_comparison(self, parent, subject_hotel: Hotel, competitor_hotels: List[Hotel]):
        """
        Create reviews comparison.
        
        Args:
            parent: Parent widget
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
        """
        # Create treeview
        columns = ("name", "tripadvisor", "google", "booking", "themes")
        
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.config(yscrollcommand=scrollbar.set)
        
        # Configure columns
        tree.heading("name", text="Hotel Name")
        tree.heading("tripadvisor", text="TripAdvisor")
        tree.heading("google", text="Google")
        tree.heading("booking", text="Booking.com")
        tree.heading("themes", text="Common Themes")
        
        tree.column("name", width=200)
        tree.column("tripadvisor", width=80, anchor=tk.CENTER)
        tree.column("google", width=80, anchor=tk.CENTER)
        tree.column("booking", width=80, anchor=tk.CENTER)
        tree.column("themes", width=300)
        
        # Helper to get review data
        def get_review_data(hotel):
            tripadvisor = ""
            google = ""
            booking = ""
            themes = []
            
            for review in hotel.reviews:
                if "tripadvisor" in review.platform.lower():
                    tripadvisor = f"{review.score:.1f} ({review.total_reviews})"
                    themes.extend(review.common_themes)
                elif "google" in review.platform.lower():
                    google = f"{review.score:.1f} ({review.total_reviews})"
                    themes.extend(review.common_themes)
                elif "booking" in review.platform.lower():
                    booking = f"{review.score:.1f} ({review.total_reviews})"
                    themes.extend(review.common_themes)
            
            # Limit themes to top 5
            themes = themes[:5]
            themes_str = ", ".join(themes)
            
            return (tripadvisor, google, booking, themes_str)
        
        # Add subject hotel
        reviews = get_review_data(subject_hotel)
        
        tree.insert(
            "",
            tk.END,
            values=(
                f"{subject_hotel.name} (Subject)",
                reviews[0],
                reviews[1],
                reviews[2],
                reviews[3]
            ),
            tags=("subject",)
        )
        
        # Add competitor hotels
        for hotel in competitor_hotels:
            reviews = get_review_data(hotel)
            
            tree.insert(
                "",
                tk.END,
                values=(
                    hotel.name,
                    reviews[0],
                    reviews[1],
                    reviews[2],
                    reviews[3]
                )
            )
        
        # Configure tag for subject hotel
        tree.tag_configure("subject", background="#FFFF99")
    
    def _generate_summary_text(self, subject_hotel: Hotel, competitor_hotels: List[Hotel]) -> str:
        """
        Generate summary text for the analysis.
        
        Args:
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
            
        Returns:
            Summary text
        """
        from tools.analysis_tools import AnalysisTools
        
        # Get positioning analysis
        positioning = AnalysisTools.identify_market_positioning(subject_hotel, competitor_hotels)
        
        # Build summary text
        summary = f"""
CompSet Analysis Summary for {subject_hotel.name}

Overview:
This analysis compares {subject_hotel.name} with {len(competitor_hotels)} competitor hotels in the {subject_hotel.city}, {subject_hotel.state} market.

Subject Hotel:
{subject_hotel.name} is a {positioning.get('relative_size', 'N/A')} property with {subject_hotel.room_count or 'unknown'} rooms. 
It is {positioning.get('age_position', 'N/A')} compared to its competitive set.

Key Observations:
"""
        
        # Add strengths
        if positioning.get('amenity_strengths'):
            summary += f"\nStrengths:\n- {subject_hotel.name} offers {', '.join(positioning.get('amenity_strengths'))}, which are not common among competitors.\n"
        
        # Add weaknesses
        if positioning.get('amenity_weaknesses'):
            summary += f"\nWeaknesses:\n- {subject_hotel.name} lacks {', '.join(positioning.get('amenity_weaknesses'))}, which are common among competitors.\n"
        
        # Add differentiators
        if positioning.get('differentiators'):
            summary += f"\nDifferentiators:\n- {', '.join(positioning.get('differentiators'))}\n"
        
        # Add review position
        if positioning.get('review_position'):
            summary += f"\nGuest Perception:\n- {subject_hotel.name} has {positioning.get('review_position').lower()} guest ratings compared to competitors.\n"
        
        # Add competitor summary
        comp_brands = set(h.brand_affiliation for h in competitor_hotels if h.brand_affiliation)
        if comp_brands:
            summary += f"\nCompetitor Brands:\n- The competitive set includes hotels from: {', '.join(comp_brands)}\n"
        
        return summary
    
    def _calculate_key_metrics(self, subject_hotel: Hotel, competitor_hotels: List[Hotel]) -> Dict[str, Dict[str, str]]:
        """
        Calculate key metrics for comparison.
        
        Args:
            subject_hotel: Subject hotel
            competitor_hotels: List of competitor hotels
            
        Returns:
            Dictionary of metrics with subject, average, and difference values
        """
        metrics = {}
        
        # Room Count
        if subject_hotel.room_count:
            comp_room_counts = [h.room_count for h in competitor_hotels if h.room_count]
            if comp_room_counts:
                avg_room_count = sum(comp_room_counts) / len(comp_room_counts)
                difference = subject_hotel.room_count - avg_room_count
                
                metrics["Room Count"] = {
                    "subject": f"{subject_hotel.room_count}",
                    "average": f"{avg_room_count:.0f}",
                    "difference": f"{difference:+.0f}"
                }
        
        # Suite Percentage
        if subject_hotel.suite_percentage:
            comp_suite_pcts = [h.suite_percentage for h in competitor_hotels if h.suite_percentage is not None]
            if comp_suite_pcts:
                avg_suite_pct = sum(comp_suite_pcts) / len(comp_suite_pcts)
                difference = subject_hotel.suite_percentage - avg_suite_pct
                
                metrics["Suite %"] = {
                    "subject": f"{subject_hotel.suite_percentage:.1f}%",
                    "average": f"{avg_suite_pct:.1f}%",
                    "difference": f"{difference:+.1f}%"
                }
        
        # Age (based on Year Built)
        if subject_hotel.year_built:
            comp_years = [h.year_built for h in competitor_hotels if h.year_built]
            if comp_years:
                subject_age = 2025 - subject_hotel.year_built  # Using fixed year for calculation
                avg_year = sum(comp_years) / len(comp_years)
                avg_age = 2025 - avg_year
                difference = avg_age - subject_age  # Positive means subject is newer
                
                metrics["Age (years)"] = {
                    "subject": f"{subject_age:.0f}",
                    "average": f"{avg_age:.0f}",
                    "difference": f"{difference:+.0f}"
                }
        
        # Meeting Space per Key
        if subject_hotel.meeting_space and subject_hotel.meeting_space.meeting_space_per_key:
            comp_mtg_per_key = [h.meeting_space.meeting_space_per_key for h in competitor_hotels 
                               if h.meeting_space and h.meeting_space.meeting_space_per_key]
            if comp_mtg_per_key:
                avg_mtg_per_key = sum(comp_mtg_per_key) / len(comp_mtg_per_key)
                difference = subject_hotel.meeting_space.meeting_space_per_key - avg_mtg_per_key
                
                metrics["Meeting SF/Key"] = {
                    "subject": f"{subject_hotel.meeting_space.meeting_space_per_key:.1f}",
                    "average": f"{avg_mtg_per_key:.1f}",
                    "difference": f"{difference:+.1f}"
                }
        
        # Average Review Score
        def get_avg_score(hotel):
            if not hotel.reviews:
                return None
            
            scores = [r.score for r in hotel.reviews if r.score]
            if not scores:
                return None
            
            return sum(scores) / len(scores)
        
        subject_score = get_avg_score(subject_hotel)
        if subject_score:
            comp_scores = [get_avg_score(h) for h in competitor_hotels]
            comp_scores = [s for s in comp_scores if s is not None]
            
            if comp_scores:
                avg_score = sum(comp_scores) / len(comp_scores)
                difference = subject_score - avg_score
                
                metrics["Review Score"] = {
                    "subject": f"{subject_score:.1f}",
                    "average": f"{avg_score:.1f}",
                    "difference": f"{difference:+.1f}"
                }
        
        return metrics
    
    def _generate_hotel_details(self, hotel: Hotel) -> str:
        """
        Generate detailed information for a hotel.
        
        Args:
            hotel: Hotel object
            
        Returns:
            Detailed information as text
        """
        # Build detail text
        details = f"""
{'=' * 80}
{hotel.name.upper()} {'(SUBJECT HOTEL)' if hotel.is_subject else ''}
{'=' * 80}

Basic Information:
-----------------
Address: {hotel.address}, {hotel.city}, {hotel.state}, {hotel.country}
Brand: {hotel.brand_affiliation or 'Independent/Unknown'}
Chain Scale: {hotel.chain_scale or 'Unknown'}
Website: {hotel.website or 'Not available'}

Owner: {hotel.owner or 'Not available'}
Management: {hotel.management_company or 'Not available'}

Year Built: {hotel.year_built or 'Not available'}
Year Renovated: {hotel.year_renovated or 'Not available'}

Physical Characteristics:
------------------------
Room Count: {hotel.room_count or 'Not available'}
Suite Count: {hotel.suite_count or 'Not available'}
Suite Percentage: {f"{hotel.suite_percentage:.1f}%" if hotel.suite_percentage is not None else 'Not available'}

Room Types:
"""
        
        if hotel.room_types:
            for room_type in hotel.room_types:
                size_str = f"{room_type.size_sf} {room_type.size_metric}" if room_type.size_sf else "size unknown"
                details += f"- {room_type.room_type} ({size_str})\n"
        else:
            details += "- No room type information available\n"
        
        details += "\nMeeting Space:\n"
        
        if hotel.meeting_space:
            ms = hotel.meeting_space
            details += f"- Total Space: {ms.total_space_sf or 'Not available'} SF\n"
            details += f"- Total Meeting Rooms: {ms.total_rooms or 'Not available'}\n"
            details += f"- Largest Room: {ms.largest_room_sf or 'Not available'} SF\n"
            details += f"- SF per Key: {ms.meeting_space_per_key or 'Not available'}\n"
        else:
            details += "- No meeting space information available\n"
        
        details += "\nAmenities:\n"
        
        if hotel.amenities:
            am = hotel.amenities
            
            # Restaurants
            if am.restaurants:
                details += "\nRestaurants:\n"
                for restaurant in am.restaurants:
                    if isinstance(restaurant, dict):
                        details += f"- {restaurant.get('name', 'Unnamed')} ({restaurant.get('type', 'No type')})\n"
                    else:
                        details += f"- {restaurant}\n"
            
            # Bars/Lounges
            if am.bars_lounges:
                details += "\nBars/Lounges:\n"
                for bar in am.bars_lounges:
                    details += f"- {bar}\n"
            
            # Other amenities
            details += "\nOther Amenities:\n"
            details += f"- Pool: {am.pool or 'No'}\n"
            details += f"- Fitness Center: {'Yes' if am.fitness_center else 'No'}\n"
            details += f"- Spa: {'Yes' if am.spa else 'No'}\n"
            details += f"- Business Center: {'Yes' if am.business_center else 'No'}\n"
            details += f"- Club Lounge: {'Yes' if am.club_lounge else 'No'}\n"
            details += f"- Parking: {am.parking_details or 'Information not available'}\n"
            details += f"- Parking Cost: {f'${am.parking_cost}' if am.parking_cost else 'Not available'}\n"
            details += f"- Resort Fee: {f'${am.resort_fee}' if am.resort_fee else 'None/Not available'}\n"
            
            # Other amenities
            if am.other_amenities:
                details += "\nAdditional Amenities:\n"
                for amenity in am.other_amenities:
                    details += f"- {amenity}\n"
        else:
            details += "- No amenity information available\n"
        
        details += "\nLocation:\n"
        if hotel.latitude and hotel.longitude:
            details += f"- Coordinates: {hotel.latitude}, {hotel.longitude}\n"
        else:
            details += "- Coordinates not available\n"
        
        if hotel.distance_from_subject is not None and not hotel.is_subject:
            details += f"- Distance from Subject Hotel: {hotel.distance_from_subject:.2f} miles\n"
        
        if hotel.nearby_demand_generators:
            details += "\nNearby Demand Generators:\n"
            for generator in hotel.nearby_demand_generators:
                details += f"- {generator}\n"
        
        details += "\nReviews:\n"
        if hotel.reviews:
            for review in hotel.reviews:
                details += f"- {review.platform}: {review.score} ({review.total_reviews} reviews)\n"
                if review.common_themes:
                    details += "  Common themes: " + ", ".join(review.common_themes) + "\n"
        else:
            details += "- No review information available\n"
        
        details += "\nSources:\n"
        if hotel.sources:
            for key, source in hotel.sources.items():
                details += f"- {key}: {source}\n"
        else:
            details += "- No source information available\n"
        
        return details
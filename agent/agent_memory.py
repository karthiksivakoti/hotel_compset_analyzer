#hotel_compset_analyzer/agent/agent_memory.py
"""
Agent memory manager for the CompSet Analyzer.
Manages state and context for the LLM agent during a scraping session.
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class AgentMemory:
    """Class for managing agent state and memory across requests."""
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize agent memory.
        
        Args:
            session_id: Unique identifier for this scraping session
        """
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.memory_dir = os.path.join("./temp", f"session_{self.session_id}")
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # Tracks information about each hotel being processed
        self.hotels_processed: Dict[str, Dict[str, Any]] = {}
        
        # Tracks scraping history and progress
        self.scraping_history: List[Dict[str, Any]] = []
        
        # Tracks sources that have been visited
        self.visited_sources: Dict[str, Dict[str, Any]] = {}
    
    def add_hotel(self, hotel_name: str, initial_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a hotel to be processed.
        
        Args:
            hotel_name: Name of the hotel
            initial_data: Initial data about the hotel (optional)
        """
        if hotel_name not in self.hotels_processed:
            self.hotels_processed[hotel_name] = {
                "name": hotel_name,
                "data_collected": {},
                "sources_checked": [],
                "attempts": 0,
                "complete": False,
                "last_updated": datetime.now().isoformat()
            }
            
            if initial_data:
                self.update_hotel_data(hotel_name, initial_data)
    
    def update_hotel_data(self, hotel_name: str, data: Dict[str, Any], 
                          source: Optional[str] = None) -> None:
        """
        Update data for a hotel.
        
        Args:
            hotel_name: Name of the hotel
            data: New data to add/update
            source: Source of the data (optional)
        """
        if hotel_name not in self.hotels_processed:
            self.add_hotel(hotel_name)
        
        # Update data_collected with new information
        self.hotels_processed[hotel_name]["data_collected"].update(data)
        
        # Add source if provided
        if source and source not in self.hotels_processed[hotel_name]["sources_checked"]:
            self.hotels_processed[hotel_name]["sources_checked"].append(source)
        
        # Update timestamp
        self.hotels_processed[hotel_name]["last_updated"] = datetime.now().isoformat()
        self.hotels_processed[hotel_name]["attempts"] += 1
        
        # Save the updated memory
        self._save_memory()
    
    def record_scraping_attempt(self, hotel_name: str, source_url: str, 
                               success: bool, details: Dict[str, Any]) -> None:
        """
        Record a scraping attempt.
        
        Args:
            hotel_name: Name of the hotel
            source_url: URL that was scraped
            success: Whether the scraping was successful
            details: Additional details about the scraping attempt
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "hotel_name": hotel_name,
            "source_url": source_url,
            "success": success,
            "details": details
        }
        
        self.scraping_history.append(entry)
        
        # Update visited sources
        if source_url not in self.visited_sources:
            self.visited_sources[source_url] = {
                "first_visit": datetime.now().isoformat(),
                "visits": 0,
                "success_count": 0,
                "failure_count": 0
            }
        
        self.visited_sources[source_url]["visits"] += 1
        if success:
            self.visited_sources[source_url]["success_count"] += 1
        else:
            self.visited_sources[source_url]["failure_count"] += 1
        
        self.visited_sources[source_url]["last_visit"] = datetime.now().isoformat()
        
        # Add source to hotel's sources_checked
        if hotel_name in self.hotels_processed and source_url not in self.hotels_processed[hotel_name]["sources_checked"]:
            self.hotels_processed[hotel_name]["sources_checked"].append(source_url)
        
        # Save the updated memory
        self._save_memory()
    
    def mark_hotel_complete(self, hotel_name: str) -> None:
        """
        Mark a hotel as completely processed.
        
        Args:
            hotel_name: Name of the hotel
        """
        if hotel_name in self.hotels_processed:
            self.hotels_processed[hotel_name]["complete"] = True
            self.hotels_processed[hotel_name]["last_updated"] = datetime.now().isoformat()
            self._save_memory()
    
    def get_incomplete_hotels(self) -> List[str]:
        """
        Get a list of hotels that are not yet completely processed.
        
        Returns:
            List of hotel names
        """
        return [name for name, data in self.hotels_processed.items() 
                if not data["complete"]]
    
    def get_hotel_data(self, hotel_name: str) -> Dict[str, Any]:
        """
        Get all data collected for a hotel.
        
        Args:
            hotel_name: Name of the hotel
            
        Returns:
            Dictionary containing all collected hotel data
        """
        if hotel_name in self.hotels_processed:
            return self.hotels_processed[hotel_name]["data_collected"]
        return {}
    
    def _save_memory(self) -> None:
        """Save the current memory state to disk."""
        memory_path = os.path.join(self.memory_dir, "agent_memory.json")
        
        memory_data = {
            "session_id": self.session_id,
            "last_updated": datetime.now().isoformat(),
            "hotels_processed": self.hotels_processed,
            "scraping_history": self.scraping_history,
            "visited_sources": self.visited_sources
        }
        
        with open(memory_path, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f, indent=2)
    
    def load_memory(self, session_id: str) -> bool:
        """
        Load memory from a previous session.
        
        Args:
            session_id: ID of the session to load
            
        Returns:
            Boolean indicating whether the load was successful
        """
        memory_dir = os.path.join("./temp", f"session_{session_id}")
        memory_path = os.path.join(memory_dir, "agent_memory.json")
        
        if not os.path.exists(memory_path):
            return False
        
        try:
            with open(memory_path, 'r', encoding='utf-8') as f:
                memory_data = json.load(f)
            
            self.session_id = memory_data["session_id"]
            self.hotels_processed = memory_data["hotels_processed"]
            self.scraping_history = memory_data["scraping_history"]
            self.visited_sources = memory_data["visited_sources"]
            self.memory_dir = memory_dir
            
            return True
        
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading memory: {e}")
            return False
    
    def get_next_actions(self, hotel_name: str) -> List[Dict[str, Any]]:
        """
        Determine next actions for a hotel based on current state.
        
        Args:
            hotel_name: Name of the hotel
            
        Returns:
            List of suggested next actions
        """
        if hotel_name not in self.hotels_processed:
            return [{"type": "add_hotel", "hotel_name": hotel_name}]
        
        hotel_data = self.hotels_processed[hotel_name]
        collected_data = hotel_data["data_collected"]
        actions = []
        
        # Check for missing basic info
        if not collected_data.get("address") or not collected_data.get("room_count"):
            actions.append({
                "type": "scrape_basic_info",
                "hotel_name": hotel_name,
                "reason": "Missing basic hotel information"
            })
        
        # Check for missing amenities
        if "amenities" not in collected_data or not collected_data.get("amenities"):
            actions.append({
                "type": "scrape_amenities",
                "hotel_name": hotel_name,
                "reason": "Missing amenities information"
            })
        
        # Check for missing reviews
        if "reviews" not in collected_data or not collected_data.get("reviews"):
            actions.append({
                "type": "scrape_reviews",
                "hotel_name": hotel_name,
                "reason": "Missing review information"
            })
        
        # Check for missing photos
        if not collected_data.get("exterior_photo_url") or not collected_data.get("guestroom_photo_url"):
            actions.append({
                "type": "scrape_photos",
                "hotel_name": hotel_name,
                "reason": "Missing hotel photos"
            })
        
        # If no specific actions needed, suggest a general refresh
        if not actions and hotel_data["attempts"] < 3:
            actions.append({
                "type": "refresh_data",
                "hotel_name": hotel_name,
                "reason": "Periodic data refresh"
            })
        
        return actions
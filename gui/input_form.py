#hotel_compset_analyzer/gui/input_form.py
"""
Input forms for the Hotel CompSet Analyzer.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
from typing import Dict, List, Any, Optional

from data.hotel import Hotel, HotelAmenities, HotelMeetingSpace


class SubjectHotelFrame(ttk.LabelFrame):
    """Frame for entering subject hotel details."""
    
    def __init__(self, parent):
        """
        Initialize the subject hotel frame.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent, text="Subject Hotel Details", padding=10)
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create the form widgets."""
        # Create a frame for the form
        form_frame = ttk.Frame(self)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Row 0: Hotel Name
        ttk.Label(form_frame, text="Hotel Name:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(form_frame, textvariable=self.name_var, width=40)
        name_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Row 1: Address
        ttk.Label(form_frame, text="Address:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        self.address_var = tk.StringVar()
        address_entry = ttk.Entry(form_frame, textvariable=self.address_var, width=40)
        address_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Row 2: City, State
        ttk.Label(form_frame, text="City:").grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        self.city_var = tk.StringVar()
        city_entry = ttk.Entry(form_frame, textvariable=self.city_var, width=20)
        city_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(form_frame, text="State/Province:").grid(
            row=2, column=2, sticky=tk.W, padx=5, pady=5
        )
        
        self.state_var = tk.StringVar()
        state_entry = ttk.Entry(form_frame, textvariable=self.state_var, width=15)
        state_entry.grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Row 3: Country, Brand
        ttk.Label(form_frame, text="Country:").grid(
            row=3, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        self.country_var = tk.StringVar(value="United States")
        country_entry = ttk.Entry(form_frame, textvariable=self.country_var, width=20)
        country_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Brand:").grid(
            row=3, column=2, sticky=tk.W, padx=5, pady=5
        )
        
        self.brand_var = tk.StringVar()
        brand_entry = ttk.Entry(form_frame, textvariable=self.brand_var, width=20)
        brand_entry.grid(row=3, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Row 4: Chain Scale, Website
        ttk.Label(form_frame, text="Chain Scale:").grid(
            row=4, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        self.chain_scale_var = tk.StringVar()
        chain_scales = ["", "Luxury", "Upper Upscale", "Upscale", "Upper Midscale", "Midscale", "Economy", "Independent"]
        chain_scale_combo = ttk.Combobox(form_frame, textvariable=self.chain_scale_var, values=chain_scales, width=15)
        chain_scale_combo.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Website:").grid(
            row=4, column=2, sticky=tk.W, padx=5, pady=5
        )
        
        self.website_var = tk.StringVar()
        website_entry = ttk.Entry(form_frame, textvariable=self.website_var, width=25)
        website_entry.grid(row=4, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Row 5: Room Count, Year Built
        ttk.Label(form_frame, text="Room Count:").grid(
            row=5, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        self.room_count_var = tk.StringVar()
        room_count_entry = ttk.Entry(form_frame, textvariable=self.room_count_var, width=10)
        room_count_entry.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Year Built:").grid(
            row=5, column=2, sticky=tk.W, padx=5, pady=5
        )
        
        self.year_built_var = tk.StringVar()
        year_built_entry = ttk.Entry(form_frame, textvariable=self.year_built_var, width=10)
        year_built_entry.grid(row=5, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Row 6: Year Renovated, Meeting Space
        ttk.Label(form_frame, text="Year Renovated:").grid(
            row=6, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        self.year_renovated_var = tk.StringVar()
        year_renovated_entry = ttk.Entry(form_frame, textvariable=self.year_renovated_var, width=10)
        year_renovated_entry.grid(row=6, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Meeting Space (sf):").grid(
            row=6, column=2, sticky=tk.W, padx=5, pady=5
        )
        
        self.meeting_space_var = tk.StringVar()
        meeting_space_entry = ttk.Entry(form_frame, textvariable=self.meeting_space_var, width=10)
        meeting_space_entry.grid(row=6, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Row 7: Key Amenities
        ttk.Label(form_frame, text="Key Amenities:").grid(
            row=7, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        amenities_frame = ttk.Frame(form_frame)
        amenities_frame.grid(row=7, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Amenities checkboxes
        self.restaurant_var = tk.BooleanVar()
        restaurant_check = ttk.Checkbutton(
            amenities_frame,
            text="Restaurant",
            variable=self.restaurant_var
        )
        restaurant_check.pack(side=tk.LEFT, padx=5)
        
        self.pool_var = tk.BooleanVar()
        pool_check = ttk.Checkbutton(
            amenities_frame,
            text="Pool",
            variable=self.pool_var
        )
        pool_check.pack(side=tk.LEFT, padx=5)
        
        self.fitness_var = tk.BooleanVar()
        fitness_check = ttk.Checkbutton(
            amenities_frame,
            text="Fitness Center",
            variable=self.fitness_var
        )
        fitness_check.pack(side=tk.LEFT, padx=5)
        
        self.spa_var = tk.BooleanVar()
        spa_check = ttk.Checkbutton(
            amenities_frame,
            text="Spa",
            variable=self.spa_var
        )
        spa_check.pack(side=tk.LEFT, padx=5)
        
        self.business_var = tk.BooleanVar()
        business_check = ttk.Checkbutton(
            amenities_frame,
            text="Business Center",
            variable=self.business_var
        )
        business_check.pack(side=tk.LEFT, padx=5)
    
    def get_hotel(self) -> Optional[Hotel]:
        """
        Get the hotel data from the form.
        
        Returns:
            Hotel object or None if validation fails
        """
        # Validate required fields
        if not self.name_var.get() or not self.address_var.get() or not self.city_var.get() or not self.state_var.get():
            messagebox.showwarning("Input Error", "Please enter required fields: Hotel Name, Address, City, and State.")
            return None
        
        # Create hotel object
        hotel = Hotel(
            name=self.name_var.get(),
            address=self.address_var.get(),
            city=self.city_var.get(),
            state=self.state_var.get(),
            country=self.country_var.get(),
            website=self.website_var.get(),
            brand_affiliation=self.brand_var.get(),
            chain_scale=self.chain_scale_var.get(),
            is_subject=True
        )
        
        # Add room count if provided
        if self.room_count_var.get():
            try:
                hotel.room_count = int(self.room_count_var.get())
            except ValueError:
                pass
        
        # Add year built if provided
        if self.year_built_var.get():
            try:
                hotel.year_built = int(self.year_built_var.get())
            except ValueError:
                pass
        
        # Add year renovated if provided
        if self.year_renovated_var.get():
            try:
                hotel.year_renovated = int(self.year_renovated_var.get())
            except ValueError:
                pass
        
        # Add meeting space if provided
        if self.meeting_space_var.get():
            try:
                meeting_space = HotelMeetingSpace()
                meeting_space.total_space_sf = float(self.meeting_space_var.get())
                hotel.meeting_space = meeting_space
            except ValueError:
                pass
        
        # Add amenities
        amenities = HotelAmenities()
        
        if self.restaurant_var.get():
            amenities.restaurants = [{"name": "Restaurant", "type": "Restaurant"}]
        
        if self.pool_var.get():
            amenities.pool = "Yes"
        
        amenities.fitness_center = self.fitness_var.get()
        amenities.spa = self.spa_var.get()
        amenities.business_center = self.business_var.get()
        
        hotel.amenities = amenities
        
        return hotel
    
    def set_hotel(self, hotel: Hotel):
        """
        Set the form fields from a hotel object.
        
        Args:
            hotel: Hotel object
        """
        self.name_var.set(hotel.name)
        self.address_var.set(hotel.address)
        self.city_var.set(hotel.city)
        self.state_var.set(hotel.state)
        self.country_var.set(hotel.country)
        self.brand_var.set(hotel.brand_affiliation or "")
        self.chain_scale_var.set(hotel.chain_scale or "")
        self.website_var.set(hotel.website or "")
        
        self.room_count_var.set(str(hotel.room_count) if hotel.room_count else "")
        self.year_built_var.set(str(hotel.year_built) if hotel.year_built else "")
        self.year_renovated_var.set(str(hotel.year_renovated) if hotel.year_renovated else "")
        
        # Meeting space
        if hotel.meeting_space and hotel.meeting_space.total_space_sf:
            self.meeting_space_var.set(str(hotel.meeting_space.total_space_sf))
        else:
            self.meeting_space_var.set("")
        
        # Amenities
        self.restaurant_var.set(len(hotel.amenities.restaurants) > 0 if hotel.amenities else False)
        self.pool_var.set(bool(hotel.amenities.pool) if hotel.amenities else False)
        self.fitness_var.set(hotel.amenities.fitness_center if hotel.amenities else False)
        self.spa_var.set(hotel.amenities.spa if hotel.amenities else False)
        self.business_var.set(hotel.amenities.business_center if hotel.amenities else False)
    
    def clear(self):
        """Clear all form fields."""
        self.name_var.set("")
        self.address_var.set("")
        self.city_var.set("")
        self.state_var.set("")
        self.country_var.set("United States")
        self.brand_var.set("")
        self.chain_scale_var.set("")
        self.website_var.set("")
        self.room_count_var.set("")
        self.year_built_var.set("")
        self.year_renovated_var.set("")
        self.meeting_space_var.set("")
        
        self.restaurant_var.set(False)
        self.pool_var.set(False)
        self.fitness_var.set(False)
        self.spa_var.set(False)
        self.business_var.set(False)


class CompetitorHotelsFrame(ttk.LabelFrame):
    """Frame for entering competitor hotels."""
    
    def __init__(self, parent):
        """
        Initialize the competitor hotels frame.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent, text="Competitor Hotels", padding=10)
        
        self.hotels = []  # List of Hotel objects
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create the form widgets."""
        # Create a frame for the list and buttons
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create hotel list frame
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(list_frame, text="Added Hotels:").pack(anchor=tk.W)
        
        # Create listbox for hotels
        self.hotel_listbox = tk.Listbox(list_frame, height=10, width=50)
        self.hotel_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add scrollbar to listbox
        scrollbar = ttk.Scrollbar(self.hotel_listbox, command=self.hotel_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.hotel_listbox.config(yscrollcommand=scrollbar.set)
        
        # Create button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # Add hotel button
        add_button = ttk.Button(
            button_frame,
            text="Add Hotel",
            command=self._show_add_dialog
        )
        add_button.pack(fill=tk.X, pady=5)
        
        # Edit hotel button
        edit_button = ttk.Button(
            button_frame,
            text="Edit Hotel",
            command=self._edit_selected
        )
        edit_button.pack(fill=tk.X, pady=5)
        
        # Remove hotel button
        remove_button = ttk.Button(
            button_frame,
            text="Remove Hotel",
            command=self._remove_selected
        )
        remove_button.pack(fill=tk.X, pady=5)
    
    def _show_add_dialog(self):
        """Show dialog to add a new hotel."""
        dialog = tk.Toplevel(self)
        dialog.title("Add Competitor Hotel")
        dialog.geometry("500x300")
        dialog.transient(self.master)
        dialog.grab_set()
        
        # Create form
        form_frame = ttk.Frame(dialog, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Hotel Name
        ttk.Label(form_frame, text="Hotel Name:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        name_var = tk.StringVar()
        name_entry = ttk.Entry(form_frame, textvariable=name_var, width=40)
        name_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Address
        ttk.Label(form_frame, text="Address:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        address_var = tk.StringVar()
        address_entry = ttk.Entry(form_frame, textvariable=address_var, width=40)
        address_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # City, State
        ttk.Label(form_frame, text="City:").grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        city_var = tk.StringVar()
        city_entry = ttk.Entry(form_frame, textvariable=city_var, width=20)
        city_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(form_frame, text="State:").grid(
            row=3, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        state_var = tk.StringVar()
        state_entry = ttk.Entry(form_frame, textvariable=state_var, width=20)
        state_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Country
        ttk.Label(form_frame, text="Country:").grid(
            row=4, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        country_var = tk.StringVar(value="United States")
        country_entry = ttk.Entry(form_frame, textvariable=country_var, width=20)
        country_entry.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Brand
        ttk.Label(form_frame, text="Brand (optional):").grid(
            row=5, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        brand_var = tk.StringVar()
        brand_entry = ttk.Entry(form_frame, textvariable=brand_var, width=20)
        brand_entry.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        def add_hotel():
            """Add the hotel and close the dialog."""
            if not name_var.get() or not address_var.get() or not city_var.get() or not state_var.get():
                messagebox.showwarning("Input Error", "Please enter required fields: Hotel Name, Address, City, and State.")
                return
            
            hotel = Hotel(
                name=name_var.get(),
                address=address_var.get(),
                city=city_var.get(),
                state=state_var.get(),
                country=country_var.get(),
                brand_affiliation=brand_var.get(),
                is_subject=False
            )
            
            self.hotels.append(hotel)
            self._update_listbox()
            dialog.destroy()
        
        add_button = ttk.Button(
            button_frame,
            text="Add",
            command=add_hotel
        )
        add_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)
    
    def _edit_selected(self):
        """Edit the selected hotel."""
        selection = self.hotel_listbox.curselection()
        
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a hotel to edit.")
            return
        
        index = selection[0]
        hotel = self.hotels[index]
        
        # Create dialog
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Hotel: {hotel.name}")
        dialog.geometry("500x300")
        dialog.transient(self.master)
        dialog.grab_set()
        
        # Create form
        form_frame = ttk.Frame(dialog, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Hotel Name
        ttk.Label(form_frame, text="Hotel Name:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        name_var = tk.StringVar(value=hotel.name)
        name_entry = ttk.Entry(form_frame, textvariable=name_var, width=40)
        name_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Address
        ttk.Label(form_frame, text="Address:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        address_var = tk.StringVar(value=hotel.address)
        address_entry = ttk.Entry(form_frame, textvariable=address_var, width=40)
        address_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # City
        ttk.Label(form_frame, text="City:").grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        city_var = tk.StringVar(value=hotel.city)
        city_entry = ttk.Entry(form_frame, textvariable=city_var, width=20)
        city_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # State
        ttk.Label(form_frame, text="State:").grid(
            row=3, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        state_var = tk.StringVar(value=hotel.state)
        state_entry = ttk.Entry(form_frame, textvariable=state_var, width=20)
        state_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Country
        ttk.Label(form_frame, text="Country:").grid(
            row=4, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        country_var = tk.StringVar(value=hotel.country)
        country_entry = ttk.Entry(form_frame, textvariable=country_var, width=20)
        country_entry.grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Brand
        ttk.Label(form_frame, text="Brand (optional):").grid(
            row=5, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        brand_var = tk.StringVar(value=hotel.brand_affiliation or "")
        brand_entry = ttk.Entry(form_frame, textvariable=brand_var, width=20)
        brand_entry.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        def update_hotel():
            """Update the hotel and close the dialog."""
            if not name_var.get() or not address_var.get() or not city_var.get() or not state_var.get():
                messagebox.showwarning("Input Error", "Please enter required fields: Hotel Name, Address, City, and State.")
                return
            
            hotel.name = name_var.get()
            hotel.address = address_var.get()
            hotel.city = city_var.get()
            hotel.state = state_var.get()
            hotel.country = country_var.get()
            hotel.brand_affiliation = brand_var.get()
            
            self._update_listbox()
            dialog.destroy()
        
        update_button = ttk.Button(
            button_frame,
            text="Update",
            command=update_hotel
        )
        update_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=dialog.destroy
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)
    
    def _remove_selected(self):
        """Remove the selected hotel."""
        selection = self.hotel_listbox.curselection()
        
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a hotel to remove.")
            return
        
        index = selection[0]
        hotel = self.hotels[index]
        
        if messagebox.askyesno("Confirm Removal", f"Remove {hotel.name} from the list?"):
            self.hotels.pop(index)
            self._update_listbox()
    
    def _update_listbox(self):
        """Update the listbox with current hotels."""
        self.hotel_listbox.delete(0, tk.END)
        
        for hotel in self.hotels:
            self.hotel_listbox.insert(tk.END, f"{hotel.name} - {hotel.city}, {hotel.state}")
    
    def get_hotels(self) -> List[Hotel]:
        """
        Get the list of hotels.
        
        Returns:
            List of Hotel objects
        """
        return self.hotels
    
    def set_hotels(self, hotels: List[Hotel]):
        """
        Set the list of hotels.
        
        Args:
            hotels: List of Hotel objects
        """
        self.hotels = [h for h in hotels if not h.is_subject]
        self._update_listbox()
    
    def clear(self):
        """Clear the hotel list."""
        self.hotels = []
        self._update_listbox()
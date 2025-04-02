#hotel_compset_analyzer/gui/app.py
"""
Main GUI application for the Hotel CompSet Analyzer.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import queue
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from gui.input_form import SubjectHotelFrame, CompetitorHotelsFrame
from gui.results_view import ResultsNotebook
from agent.llm_controller import LLMController
from agent.agent_memory import AgentMemory
from tools.scraping_tools import WebScraper
from tools.geo_tools import GeoTools
from tools.analysis_tools import AnalysisTools
from data.hotel import Hotel
from data.storage import CompSetStorage
from output.map_generator import MapGenerator
from output.matrix_generator import MatrixGenerator
from output.excel_export import ExcelExporter
from output.pdf_export import PDFExporter
from output.web_dashboard import create_dashboard


class CompSetAnalyzerApp:
    """Main application for the Hotel CompSet Analyzer."""
    
    def __init__(self, root):
        """
        Initialize the application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Hotel CompSet Analyzer")
        
        # Create a queue for thread communication
        self.queue = queue.Queue()
        
        # Main frame
        self.main_frame = ttk.Frame(root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create components
        self._create_menu()
        self._create_notebook()
        self._create_status_bar()
        
        # Initialize components
        self.llm_controller = None
        self.agent_memory = None
        self.web_scraper = None
        self.geo_tools = None
        self.storage = CompSetStorage()
        
        # Check for API keys
        self._check_api_keys()
        
        # Process queue every 100ms
        self.root.after(100, self._process_queue)
    
    def _create_menu(self):
        """Create the application menu."""
        menu_bar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New Analysis", command=self._new_analysis)
        file_menu.add_command(label="Load Analysis", command=self._load_analysis)
        file_menu.add_command(label="Save Analysis", command=self._save_analysis)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Export menu
        export_menu = tk.Menu(menu_bar, tearoff=0)
        export_menu.add_command(label="Export to Excel", command=self._export_to_excel)
        export_menu.add_command(label="Export to PDF", command=self._export_to_pdf)
        export_menu.add_command(label="Export to Web Dashboard", command=self._export_to_dashboard)
        menu_bar.add_cascade(label="Export", menu=export_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="Settings", command=self._show_settings)
        tools_menu.add_command(label="API Key Setup", command=self._setup_api_keys)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)
        
        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Documentation", command=self._show_documentation)
        help_menu.add_command(label="About", command=self._show_about)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menu_bar)
    
    def _create_notebook(self):
        """Create the main notebook interface."""
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Input tab
        self.input_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.input_frame, text="Input")
        
        # Subject hotel frame
        self.subject_hotel_frame = SubjectHotelFrame(self.input_frame)
        self.subject_hotel_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Competitor hotels frame
        self.competitor_frame = CompetitorHotelsFrame(self.input_frame)
        self.competitor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Start analysis button
        self.analyze_button = ttk.Button(
            self.input_frame, 
            text="Start Analysis", 
            command=self._start_analysis
        )
        self.analyze_button.pack(pady=10)
        
        # Results tab (initially empty, populated after analysis)
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Results")
        self.results_view = ResultsNotebook(self.results_frame)
        self.results_view.pack(fill=tk.BOTH, expand=True)
        
        # Log tab
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="Log")
        
        self.log_text = tk.Text(self.log_frame, wrap=tk.WORD, width=80, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar to log
        log_scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        # Make log read-only
        self.log_text.config(state=tk.DISABLED)
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Status label
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.status_frame, 
            variable=self.progress_var,
            length=300,
            mode='determinate'
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
    
    def _check_api_keys(self):
        """Check if required API keys are available."""
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        if not anthropic_key:
            self._log("Warning: ANTHROPIC_API_KEY not found. Please set up API keys.")
            messagebox.showwarning(
                "API Key Missing", 
                "Anthropic API key not found. Some functionality may be limited.\n\n"
                "Go to Tools > API Key Setup to configure keys."
            )
    
    def _process_queue(self):
        """Process the message queue from background threads."""
        try:
            while True:
                message = self.queue.get_nowait()
                
                if message["type"] == "log":
                    self._log(message["text"])
                elif message["type"] == "status":
                    self.status_label.config(text=message["text"])
                elif message["type"] == "progress":
                    self.progress_var.set(message["value"])
                elif message["type"] == "error":
                    messagebox.showerror("Error", message["text"])
                elif message["type"] == "complete":
                    self._analysis_complete(message["data"])
                
                self.queue.task_done()
        except queue.Empty:
            # Queue is empty, check again after 100ms
            self.root.after(100, self._process_queue)
    
    def _log(self, message):
        """Add a message to the log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        logger.info(message)
    
    def _new_analysis(self):
        """Start a new analysis (clear all data)."""
        if messagebox.askyesno("New Analysis", "Start a new analysis? All unsaved data will be lost."):
            self.subject_hotel_frame.clear()
            self.competitor_frame.clear()
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)
            self.status_label.config(text="Ready")
            self.progress_var.set(0)
            
            # Reset results view
            self.results_view.clear()
            
            # Switch to input tab
            self.notebook.select(0)
            
            self._log("New analysis started.")
    
    def _load_analysis(self):
        """Load a saved analysis."""
        # Show list of saved analyses
        saved_compsets = self.storage.list_saved_compsets()
        
        if not saved_compsets:
            messagebox.showinfo("No Saved Analyses", "No saved analyses found.")
            return
        
        # Create dialog to select an analysis
        dialog = tk.Toplevel(self.root)
        dialog.title("Load Analysis")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create listbox
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Select an analysis to load:").pack(anchor=tk.W)
        
        listbox = tk.Listbox(frame, width=70, height=15)
        listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(listbox, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)
        
        # Populate listbox
        for i, compset in enumerate(saved_compsets):
            listbox.insert(tk.END, f"{compset['subject_name']} - {compset['created_at']}")
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        load_button = ttk.Button(
            button_frame, 
            text="Load", 
            command=lambda: self._do_load_analysis(dialog, saved_compsets, listbox.curselection())
        )
        load_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=dialog.destroy
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)
    
    def _do_load_analysis(self, dialog, saved_compsets, selection):
        """
        Actually load the selected analysis.
        
        Args:
            dialog: The dialog window
            saved_compsets: List of saved compsets
            selection: Selected index in the listbox
        """
        if not selection:
            messagebox.showwarning("No Selection", "Please select an analysis to load.")
            return
        
        selected_index = selection[0]
        selected_compset = saved_compsets[selected_index]
        
        # Close dialog
        dialog.destroy()
        
        # Load the analysis
        try:
            compset_data = self.storage.load_compset(selected_compset["full_path"])
            
            # Populate subject hotel
            subject_hotel = compset_data["subject_hotel"]
            competitor_hotels = compset_data["competitor_hotels"]
            
            # Update UI
            self.subject_hotel_frame.set_hotel(subject_hotel)
            self.competitor_frame.set_hotels(competitor_hotels)
            
            # Update results view
            self.results_view.display_results(subject_hotel, competitor_hotels)
            
            # Switch to results tab
            self.notebook.select(1)
            
            self._log(f"Loaded analysis: {selected_compset['subject_name']} from {selected_compset['created_at']}")
            
        except Exception as e:
            self._log(f"Error loading analysis: {e}")
            messagebox.showerror("Load Error", f"Error loading analysis: {e}")
    
    def _save_analysis(self):
        """Save the current analysis."""
        # Get subject hotel
        subject_hotel = self.subject_hotel_frame.get_hotel()
        if not subject_hotel:
            messagebox.showwarning("Save Error", "No subject hotel data to save.")
            return
        
        # Get competitor hotels
        competitor_hotels = self.competitor_frame.get_hotels()
        if not competitor_hotels:
            messagebox.showwarning("Save Error", "No competitor hotel data to save.")
            return
        
        # Save the data
        try:
            save_dir = self.storage.save_compset(subject_hotel, competitor_hotels)
            
            self._log(f"Analysis saved to: {save_dir}")
            messagebox.showinfo("Save Complete", f"Analysis saved successfully.")
            
        except Exception as e:
            self._log(f"Error saving analysis: {e}")
            messagebox.showerror("Save Error", f"Error saving analysis: {e}")
    
    def _export_to_excel(self):
        """Export the analysis to Excel."""
        # Get subject hotel
        subject_hotel = self.subject_hotel_frame.get_hotel()
        if not subject_hotel:
            messagebox.showwarning("Export Error", "No subject hotel data to export.")
            return
        
        # Get competitor hotels
        competitor_hotels = self.competitor_frame.get_hotels()
        if not competitor_hotels:
            messagebox.showwarning("Export Error", "No competitor hotel data to export.")
            return
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            title="Export to Excel",
            filetypes=[("Excel files", "*.xlsx")],
            defaultextension=".xlsx"
        )
        
        if not filename:
            return
        
        # Create exporter
        exporter = ExcelExporter()
        
        try:
            # Export to Excel
            exporter.export(subject_hotel, competitor_hotels, filename)
            
            self._log(f"Exported to Excel: {filename}")
            messagebox.showinfo("Export Complete", f"Analysis exported to Excel successfully.")
            
        except Exception as e:
            self._log(f"Error exporting to Excel: {e}")
            messagebox.showerror("Export Error", f"Error exporting to Excel: {e}")
    
    def _export_to_pdf(self):
        """Export the analysis to PDF."""
        # Get subject hotel
        subject_hotel = self.subject_hotel_frame.get_hotel()
        if not subject_hotel:
            messagebox.showwarning("Export Error", "No subject hotel data to export.")
            return
        
        # Get competitor hotels
        competitor_hotels = self.competitor_frame.get_hotels()
        if not competitor_hotels:
            messagebox.showwarning("Export Error", "No competitor hotel data to export.")
            return
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            title="Export to PDF",
            filetypes=[("PDF files", "*.pdf")],
            defaultextension=".pdf"
        )
        
        if not filename:
            return
        
        # Create exporter
        exporter = PDFExporter()
        
        try:
            # Export to PDF
            exporter.export(subject_hotel, competitor_hotels, filename)
            
            self._log(f"Exported to PDF: {filename}")
            messagebox.showinfo("Export Complete", f"Analysis exported to PDF successfully.")
            
        except Exception as e:
            self._log(f"Error exporting to PDF: {e}")
            messagebox.showerror("Export Error", f"Error exporting to PDF: {e}")
    
    def _export_to_dashboard(self):
        """Export the analysis to a web dashboard."""
        # Get subject hotel
        subject_hotel = self.subject_hotel_frame.get_hotel()
        if not subject_hotel:
            messagebox.showwarning("Export Error", "No subject hotel data to export.")
            return
        
        # Get competitor hotels
        competitor_hotels = self.competitor_frame.get_hotels()
        if not competitor_hotels:
            messagebox.showwarning("Export Error", "No competitor hotel data to export.")
            return
        
        # Ask for save location
        directory = filedialog.askdirectory(
            title="Select Directory for Web Dashboard"
        )
        
        if not directory:
            return
        
        try:
            # Create dashboard
            dashboard_path = create_dashboard(subject_hotel, competitor_hotels, directory)
            
            self._log(f"Created web dashboard: {dashboard_path}")
            messagebox.showinfo(
                "Dashboard Created", 
                f"Web dashboard created successfully at:\n{dashboard_path}\n\nOpen index.html in a web browser to view."
            )
            
        except Exception as e:
            self._log(f"Error creating dashboard: {e}")
            messagebox.showerror("Export Error", f"Error creating dashboard: {e}")
    
    def _show_settings(self):
        """Show settings dialog."""
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create settings form
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Application Settings", font=("Arial", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        
        # Scraping delay
        ttk.Label(frame, text="Scraping Delay (seconds):").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        
        delay_var = tk.StringVar(value=os.environ.get("SCRAPING_DELAY", "2"))
        delay_entry = ttk.Entry(frame, textvariable=delay_var, width=10)
        delay_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Use Selenium checkbox
        use_selenium_var = tk.BooleanVar(value=True)
        use_selenium_check = ttk.Checkbutton(
            frame, 
            text="Use Selenium for JavaScript-heavy sites",
            variable=use_selenium_var
        )
        use_selenium_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Headless mode checkbox
        headless_var = tk.BooleanVar(value=True)
        headless_check = ttk.Checkbutton(
            frame, 
            text="Run browser in headless mode",
            variable=headless_var
        )
        headless_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        save_button = ttk.Button(
            button_frame, 
            text="Save", 
            command=lambda: self._save_settings(dialog, delay_var.get(), 
                                              use_selenium_var.get(), headless_var.get())
        )
        save_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=dialog.destroy
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)
    
    def _save_settings(self, dialog, delay, use_selenium, headless):
        """
        Save settings.
        
        Args:
            dialog: The dialog window
            delay: Scraping delay in seconds
            use_selenium: Whether to use Selenium
            headless: Whether to run in headless mode
        """
        try:
            # Validate delay
            try:
                delay_float = float(delay)
                if delay_float < 0:
                    raise ValueError("Delay must be a positive number")
            except ValueError:
                messagebox.showwarning("Invalid Input", "Scraping delay must be a positive number.")
                return
            
            # Update environment variables
            os.environ["SCRAPING_DELAY"] = str(delay_float)
            
            # Close dialog
            dialog.destroy()
            
            self._log("Settings saved.")
            
        except Exception as e:
            messagebox.showerror("Settings Error", f"Error saving settings: {e}")
    
    def _setup_api_keys(self):
        """Show API key setup dialog."""
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("API Key Setup")
        dialog.geometry("500x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create form
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="API Key Configuration", font=("Arial", 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        
        # Anthropic API key
        ttk.Label(frame, text="Anthropic API Key:").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        
        anthropic_key_var = tk.StringVar(value=os.environ.get("ANTHROPIC_API_KEY", ""))
        anthropic_key_entry = ttk.Entry(frame, textvariable=anthropic_key_var, width=50)
        anthropic_key_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Google Maps API key
        ttk.Label(frame, text="Google Maps API Key:").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        
        google_key_var = tk.StringVar(value=os.environ.get("GOOGLE_MAPS_API_KEY", ""))
        google_key_entry = ttk.Entry(frame, textvariable=google_key_var, width=50)
        google_key_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Help text
        help_text = tk.Text(frame, wrap=tk.WORD, width=60, height=8)
        help_text.grid(row=3, column=0, columnspan=2, pady=10)
        help_text.insert(tk.END, 
            "Anthropic API Key: Required for the AI functionality. Get one at https://www.anthropic.com\n\n"
            "Google Maps API Key: Optional but recommended for better geocoding and map functionality. "
            "Get one at https://cloud.google.com/maps-platform/"
        )
        help_text.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        save_button = ttk.Button(
            button_frame, 
            text="Save", 
            command=lambda: self._save_api_keys(dialog, anthropic_key_var.get(), google_key_var.get())
        )
        save_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = ttk.Button(
            button_frame, 
            text="Cancel", 
            command=dialog.destroy
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)
    
    def _save_api_keys(self, dialog, anthropic_key, google_key):
        """
        Save API keys.
        
        Args:
            dialog: The dialog window
            anthropic_key: Anthropic API key
            google_key: Google Maps API key
        """
        # Update environment variables
        if anthropic_key:
            os.environ["ANTHROPIC_API_KEY"] = anthropic_key
        
        if google_key:
            os.environ["GOOGLE_MAPS_API_KEY"] = google_key
        
        # Write to .env file
        env_content = [
            f"ANTHROPIC_API_KEY={anthropic_key}",
            f"GOOGLE_MAPS_API_KEY={google_key}",
            f"SCRAPING_DELAY={os.environ.get('SCRAPING_DELAY', '2')}",
            "USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "DEBUG_MODE=False",
            "SAVE_DIRECTORY=./saved_compsets"
        ]
        
        try:
            with open(".env", "w") as f:
                f.write("\n".join(env_content))
            
            # Close dialog
            dialog.destroy()
            
            self._log("API keys saved.")
            
        except Exception as e:
            messagebox.showerror("API Key Error", f"Error saving API keys to .env file: {e}")
    
    def _show_documentation(self):
        """Show documentation."""
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Documentation")
        dialog.geometry("700x500")
        
        # Create documentation viewer
        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Documentation text
        doc_text = tk.Text(frame, wrap=tk.WORD, width=80, height=30)
        doc_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(doc_text, command=doc_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        doc_text.config(yscrollcommand=scrollbar.set)
        
        # Documentation content
        doc_content = """
        # Hotel CompSet Analyzer Documentation
        
        ## Overview
        
        The Hotel CompSet Analyzer is a tool for automating the market research phase of hotel deal underwriting.
        It gathers comprehensive data about potential competitor hotels for a given subject hotel.
        
        ## Getting Started
        
        1. Enter the details of your subject hotel in the "Subject Hotel" section.
        2. Add potential competitor hotels in the "Competitor Hotels" section.
        3. Click "Start Analysis" to begin the data collection process.
        4. Review the results in the "Results" tab.
        5. Export the analysis to Excel, PDF, or a web dashboard.
        
        ## Features
        
        - Automated data collection from public sources
        - Interactive map of competitive set properties
        - Detailed comparison matrix of hotel attributes
        - Export to Excel, PDF, and web dashboard
        
        ## Requirements
        
        - Anthropic API key for the AI functionality
        - Google Maps API key (optional) for better geocoding and map functionality
        
        ## Support
        
        For support, please contact your system administrator or refer to the project GitHub repository.
        """
        
        doc_text.insert(tk.END, doc_content)
        doc_text.config(state=tk.DISABLED)
        
        # Close button
        close_button = ttk.Button(frame, text="Close", command=dialog.destroy)
        close_button.pack(pady=10)
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "Hotel CompSet Analyzer\n\n"
            "An agentic web scraping tool for automating hotel competitive set analysis.\n\n"
            "Version 1.0.0\n\n"
            "Built with Python and Claude AI"
        )
    
    def _start_analysis(self):
        """Start the analysis process."""
        # Get subject hotel
        subject_hotel = self.subject_hotel_frame.get_hotel()
        if not subject_hotel:
            messagebox.showwarning("Input Error", "Please enter subject hotel details.")
            return
        
        # Get competitor hotels
        competitor_hotels = self.competitor_frame.get_hotels()
        if not competitor_hotels or len(competitor_hotels) == 0:
            messagebox.showwarning("Input Error", "Please add at least one competitor hotel.")
            return
        
        # Check for Anthropic API key
        if not os.environ.get("ANTHROPIC_API_KEY"):
            if not messagebox.askyesno(
                "API Key Missing",
                "Anthropic API key is missing. The analysis may not work properly.\n\n"
                "Do you want to continue anyway?"
            ):
                return
        
        # Disable UI during analysis
        self.analyze_button.config(state=tk.DISABLED)
        self.status_label.config(text="Analysis in progress...")
        self.progress_var.set(0)
        
        # Switch to log tab
        self.notebook.select(2)
        
        # Clear log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        self._log("Starting analysis...")
        
        # Start analysis in a separate thread
        threading.Thread(
            target=self._run_analysis,
            args=(subject_hotel, competitor_hotels),
            daemon=True
        ).start()
    
    def _run_analysis(self, subject_hotel, competitor_hotels):
        """
        Run the analysis in a background thread.
        
        Args:
            subject_hotel: Subject hotel data
            competitor_hotels: List of competitor hotel data
        """
        try:
            # Initialize components
            self.queue.put({"type": "log", "text": "Initializing components..."})
            
            # Create a new agent memory for this session
            self.agent_memory = AgentMemory()
            
            # Initialize LLM controller
            self.llm_controller = LLMController()
            
            # Initialize web scraper
            self.web_scraper = WebScraper(
                use_selenium=True,
                headless=True
            )
            
            # Initialize geo tools
            self.geo_tools = GeoTools()
            
            # Process each hotel
            total_hotels = len(competitor_hotels) + 1  # Including subject hotel
            hotels_processed = 0
            
            # Process subject hotel
            self.queue.put({"type": "log", "text": f"Processing subject hotel: {subject_hotel.name}"})
            self.queue.put({"type": "status", "text": f"Processing {subject_hotel.name}..."})
            self.queue.put({"type": "progress", "value": 0})
            
            # Add subject hotel to memory
            self.agent_memory.add_hotel(subject_hotel.name, subject_hotel.__dict__)
            
            # Mark subject hotel as complete (we already have its data)
            self.agent_memory.mark_hotel_complete(subject_hotel.name)
            
            hotels_processed += 1
            self.queue.put({"type": "progress", "value": (hotels_processed / total_hotels) * 100})
            
            # Process competitor hotels
            for hotel in competitor_hotels:
                self.queue.put({"type": "log", "text": f"Processing competitor hotel: {hotel.name}"})
                self.queue.put({"type": "status", "text": f"Processing {hotel.name}..."})
                
                # Check if we already have complete data for this hotel
                if hotel.name in self.agent_memory.get_incomplete_hotels():
                    # Process hotel
                    self._process_hotel(hotel)
                else:
                    self.queue.put({"type": "log", "text": f"Hotel {hotel.name} already processed. Skipping."})
                
                hotels_processed += 1
                self.queue.put({"type": "progress", "value": (hotels_processed / total_hotels) * 100})
            
            # Calculate distances
            self.queue.put({"type": "log", "text": "Calculating distances..."})
            
            if subject_hotel.latitude and subject_hotel.longitude:
                for hotel in competitor_hotels:
                    if hotel.latitude and hotel.longitude:
                        distance = self.geo_tools.calculate_distance(
                            {"lat": subject_hotel.latitude, "lng": subject_hotel.longitude},
                            {"lat": hotel.latitude, "lng": hotel.longitude}
                        )
                        hotel.distance_from_subject = distance
            
            # Analysis complete
            self.queue.put({"type": "log", "text": "Analysis complete!"})
            self.queue.put({"type": "status", "text": "Analysis complete"})
            self.queue.put({"type": "progress", "value": 100})
            
            # Pass results to main thread
            self.queue.put({
                "type": "complete", 
                "data": {
                    "subject_hotel": subject_hotel,
                    "competitor_hotels": competitor_hotels
                }
            })
            
        except Exception as e:
            self.queue.put({"type": "log", "text": f"Error during analysis: {e}"})
            self.queue.put({"type": "error", "text": f"Analysis failed: {e}"})
            self.queue.put({"type": "status", "text": "Analysis failed"})
            
            # Re-enable analyze button
            self.analyze_button.config(state=tk.NORMAL)
    
    def _process_hotel(self, hotel):
        """
        Process a single hotel.
        
        Args:
            hotel: Hotel to process
        """
        # Add hotel to memory
        self.agent_memory.add_hotel(hotel.name, hotel.__dict__)
        
        # Find hotel website
        self.queue.put({"type": "log", "text": f"Searching for {hotel.name} website..."})
        
        # Get the location string
        location = f"{hotel.city}, {hotel.state}"
        
        official_site = self.web_scraper.find_hotel_official_site(hotel.name, location)
        
        if official_site:
            self.queue.put({"type": "log", "text": f"Found official site: {official_site}"})
            
            # Get page content
            content, success = self.web_scraper.get_page_content(official_site)
            
            if content and success:
                # Extract hotel data using LLM
                self.queue.put({"type": "log", "text": "Extracting hotel data..."})
                
                extraction_results = self.llm_controller.extract_hotel_data(
                    content, hotel.name, official_site
                )
                
                if "error" not in extraction_results:
                    # Update hotel data
                    self.agent_memory.update_hotel_data(
                        hotel.name, extraction_results, official_site
                    )
                    
                    # Update actual hotel object
                    for key, value in extraction_results.items():
                        if hasattr(hotel, key) and value:
                            setattr(hotel, key, value)
                    
                    self.queue.put({"type": "log", "text": "Basic hotel data extracted successfully"})
                else:
                    self.queue.put({"type": "log", "text": f"Error extracting hotel data: {extraction_results.get('error')}"})
                
                # Extract amenities
                self.queue.put({"type": "log", "text": "Extracting amenities..."})
                
                amenities_results = self.llm_controller.extract_amenities(
                    content, hotel.name, official_site
                )
                
                if "error" not in amenities_results:
                    # Update amenities
                    for key, value in amenities_results.items():
                        if hasattr(hotel.amenities, key) and value:
                            setattr(hotel.amenities, key, value)
                    
                    self.queue.put({"type": "log", "text": "Amenities extracted successfully"})
                else:
                    self.queue.put({"type": "log", "text": f"Error extracting amenities: {amenities_results.get('error')}"})
                
                # Extract images
                self.queue.put({"type": "log", "text": "Extracting images..."})
                
                images = self.web_scraper.extract_images_from_page(content, official_site)
                
                if images["exterior"] and not hotel.exterior_photo_url:
                    hotel.exterior_photo_url = images["exterior"][0]
                
                if images["rooms"] and not hotel.guestroom_photo_url:
                    hotel.guestroom_photo_url = images["rooms"][0]
                
                self.queue.put({"type": "log", "text": f"Found {len(images['exterior'])} exterior and {len(images['rooms'])} room images"})
        else:
            self.queue.put({"type": "log", "text": f"Could not find official site for {hotel.name}"})
        
        # Find hotel on TripAdvisor
        self.queue.put({"type": "log", "text": f"Searching for {hotel.name} on TripAdvisor..."})
        
        tripadvisor_url = self.web_scraper.search_hotel_on_tripadvisor(hotel.name, location)
        
        if tripadvisor_url:
            self.queue.put({"type": "log", "text": f"Found on TripAdvisor: {tripadvisor_url}"})
            
            # Get page content
            content, success = self.web_scraper.get_page_content(tripadvisor_url, use_selenium=True)
            
            if content and success:
                # Extract reviews
                self.queue.put({"type": "log", "text": "Extracting reviews..."})
                
                reviews_results = self.llm_controller.summarize_reviews(
                    content, hotel.name, "TripAdvisor"
                )
                
                if "error" not in reviews_results:
                    # Add review
                    from data.hotel import HotelReview
                    from datetime import datetime
                    
                    hotel.reviews.append(HotelReview(
                        platform="TripAdvisor",
                        score=reviews_results.get("average_score", 0),
                        total_reviews=reviews_results.get("total_reviews", 0),
                        last_updated=datetime.now(),
                        common_themes=reviews_results.get("common_themes", [])
                    ))
                    
                    self.queue.put({"type": "log", "text": "TripAdvisor reviews extracted successfully"})
                else:
                    self.queue.put({"type": "log", "text": f"Error extracting TripAdvisor reviews: {reviews_results.get('error')}"})
        else:
            self.queue.put({"type": "log", "text": f"Could not find {hotel.name} on TripAdvisor"})
        
        # Geocode address
        if hotel.address and not (hotel.latitude and hotel.longitude):
            self.queue.put({"type": "log", "text": "Geocoding address..."})
            
            address = f"{hotel.address}, {hotel.city}, {hotel.state}, {hotel.country}"
            coordinates = self.geo_tools.geocode_address(address)
            
            if coordinates:
                hotel.latitude = coordinates["lat"]
                hotel.longitude = coordinates["lng"]
                
                self.queue.put({"type": "log", "text": f"Geocoded address: {coordinates['lat']}, {coordinates['lng']}"})
            else:
                self.queue.put({"type": "log", "text": "Could not geocode address"})
        
        # Mark hotel as complete
        self.agent_memory.mark_hotel_complete(hotel.name)
    
    def _analysis_complete(self, data):
        """
        Handle analysis completion.
        
        Args:
            data: Analysis results
        """
        subject_hotel = data["subject_hotel"]
        competitor_hotels = data["competitor_hotels"]
        
        # Update UI
        self.results_view.display_results(subject_hotel, competitor_hotels)
        
        # Switch to results tab
        self.notebook.select(1)
        
        # Re-enable analyze button
        self.analyze_button.config(state=tk.NORMAL)
        
        # Show completion message
        messagebox.showinfo(
            "Analysis Complete", 
            f"Analysis of {subject_hotel.name} and {len(competitor_hotels)} competitor hotels is complete."
        )
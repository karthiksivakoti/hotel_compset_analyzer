import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.automated_hotel_scraper import AutomatedHotelScraper
from data.storage import CompSetStorage
from output.map_generator import MapGenerator
from output.matrix_generator import MatrixGenerator
from output.excel_export import ExcelExporter
from output.web_dashboard import create_dashboard

def main():
    """
    Main entry point for the Hotel CompSet Analyzer.
    Automates competitive set analysis for a given location.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Set up output directories
    os.makedirs("./output", exist_ok=True)
    os.makedirs("./saved_compsets", exist_ok=True)

    try:
        # Read subject hotel details from environment variables
        if not os.environ.get("SUBJECT_HOTEL_NAME"):
            logger.error("SUBJECT_HOTEL_NAME environment variable is required")
            return
        
        # Build subject hotel info from environment variables
        subject_hotel_info = {
            "name": os.environ.get("SUBJECT_HOTEL_NAME"),
            "address": os.environ.get("SUBJECT_HOTEL_ADDRESS", ""),
            "city": os.environ.get("SUBJECT_HOTEL_CITY", ""),
            "state": os.environ.get("SUBJECT_HOTEL_STATE", ""),
            "brand": os.environ.get("SUBJECT_HOTEL_BRAND", ""),
            "chain_scale": os.environ.get("SUBJECT_HOTEL_CHAIN_SCALE", ""),
            "room_count": int(os.environ.get("SUBJECT_HOTEL_ROOM_COUNT", "0")) if os.environ.get("SUBJECT_HOTEL_ROOM_COUNT", "").isdigit() else None
        }
        
        # Parse amenities if provided
        if os.environ.get("SUBJECT_HOTEL_AMENITIES"):
            subject_hotel_info["amenities"] = os.environ.get("SUBJECT_HOTEL_AMENITIES").split(",")
        
        # Derive location from hotel info
        if not subject_hotel_info["city"] or not subject_hotel_info["state"]:
            if "," in subject_hotel_info["address"]:
                # Try to extract from address
                address_parts = subject_hotel_info["address"].split(",")
                if len(address_parts) >= 2:
                    address_parts = [part.strip() for part in address_parts]
                    # Assume last part contains state
                    state_part = address_parts[-1].split()
                    if len(state_part) >= 1:
                        subject_hotel_info["state"] = state_part[0]
                    # Assume second-to-last part contains city
                    if len(address_parts) >= 2:
                        subject_hotel_info["city"] = address_parts[-2]
        
        # Ensure we have at least city and state for location
        if not subject_hotel_info["city"] or not subject_hotel_info["state"]:
            logger.error("City and state must be provided in environment variables or extractable from address")
            return
        
        # Location and number of competitors
        location = f"{subject_hotel_info['city']}, {subject_hotel_info['state']}"
        num_competitors = int(os.environ.get('NUM_COMPETITORS', 5))

        # Initialize scraper
        logger.info(f"Starting competitive set analysis for {subject_hotel_info['name']} in {location}")
        scraper = AutomatedHotelScraper(location, num_competitors)
        
        # Set subject hotel
        scraper.set_subject_hotel(subject_hotel_info)
        
        # Run competitive set analysis
        results = scraper.run_competitive_set_analysis()
        
        # Export to JSON for reference
        json_file = scraper.export_to_json(results)
        logger.info(f"Exported raw data to: {json_file}")
        
        # If we found hotels, process further
        if results['competitor_hotels']:
            # Get subject hotel and competitor hotels
            subject_hotel = results['subject_hotel']
            competitor_hotels = results['competitor_hotels']
            
            # Storage
            storage = CompSetStorage()
            
            # Save the competitive set
            saved_path = storage.save_compset(subject_hotel, competitor_hotels)
            logger.info(f"Saved competitive set to: {saved_path}")
            
            # Generate map
            map_generator = MapGenerator()
            map_file = map_generator.create_map(subject_hotel, competitor_hotels)
            logger.info(f"Generated map: {map_file}")
            
            # Generate comparison matrix
            matrix_generator = MatrixGenerator()
            matrix_file = matrix_generator.create_comparison_matrix(subject_hotel, competitor_hotels)
            logger.info(f"Generated comparison matrix: {matrix_file}")
            
            # Excel export
            excel_exporter = ExcelExporter()
            excel_file = os.path.join(saved_path, "compset_analysis.xlsx")
            excel_exporter.export(subject_hotel, competitor_hotels, excel_file)
            logger.info(f"Exported Excel file: {excel_file}")
            
            # Web dashboard
            dashboard_dir = os.path.join(saved_path, "dashboard")
            create_dashboard(subject_hotel, competitor_hotels, dashboard_dir)
            logger.info(f"Created web dashboard: {dashboard_dir}")
            
            print("\n==== COMPETITIVE SET ANALYSIS COMPLETE ====")
            print(f"Subject Hotel: {subject_hotel.name}")
            print(f"Competitor Hotels: {len(competitor_hotels)}")
            print(f"\nResults available at:")
            print(f"- Dashboard: {dashboard_dir}/index.html")
            print(f"- Excel file: {excel_file}")
            print(f"- Map: {map_file}")
            print("========================================\n")
        
        else:
            logger.warning(f"No hotels found for location: {location}")
    
    except Exception as e:
        logger.error(f"An error occurred during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
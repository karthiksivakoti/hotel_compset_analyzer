#hotel_compset_analyzer/tools/scraping_tools.py
"""
Web scraping tools for the Hotel CompSet Analyzer.
"""

import os
import time
import random
import requests
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, urljoin
import logging
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Browser, Page
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebScraper:
    """Web scraping tools for the CompSet Analyzer."""
    
    def __init__(self, use_browser: bool = True, headless: bool = True):
        """
        Initialize the web scraper.
        
        Args:
            use_browser: Whether to use Playwright for JavaScript-heavy sites
            headless: Whether to run browser in headless mode
        """
        self.use_browser = use_browser
        self.headless = headless
        self.browser = None
        self.page = None
        
        # Default headers for requests
        self.headers = {
            'User-Agent': os.environ.get(
                'USER_AGENT', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Scraping delay (in seconds)
        self.delay = float(os.environ.get('SCRAPING_DELAY', '2'))
        
        if self.use_browser:
            self._init_browser()
    
    def _init_browser(self):
        """Initialize Playwright browser."""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=False)
            self.page = self.browser.new_page(
                user_agent=self.headers['User-Agent'],
                viewport={"width": 1920, "height": 1080}
            )
            logger.info("Playwright browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Playwright browser: {e}")
            self.use_browser = False
            self.browser = None
            self.page = None
    
    def close(self):
        """Close the browser if it's open."""
        if self.browser:
            try:
                self.browser.close()
                self.playwright.stop()
                logger.info("Playwright browser closed successfully")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
            finally:
                self.browser = None
                self.page = None
    
    def _get_with_browser(self, url: str) -> Tuple[Optional[str], bool]:
        """
        Get page content using Playwright browser.
        
        Args:
            url: URL to scrape
            
        Returns:
            Tuple of (HTML content or None, success boolean)
        """
        if not self.browser or not self.page:
            self._init_browser()
            if not self.browser or not self.page:
                return self._get_with_requests(url)
        
        try:
            # Navigate to the URL
            self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Check for CAPTCHA
            captcha_selectors = ["#captcha", "input[name='captcha']", "iframe[title*='captcha']", 
                                "iframe[src*='recaptcha']", "iframe[src*='captcha']"]
            
            captcha_detected = False
            for selector in captcha_selectors:
                try:
                    if self.page.query_selector(selector):
                        captcha_detected = True
                        break
                except:
                    pass
                    
            if captcha_detected or "recaptcha" in self.page.content().lower() or "captcha" in self.page.content().lower():
                logger.warning("CAPTCHA detected! Please solve it manually in the browser window.")
                print("\n==== CAPTCHA DETECTED ====")
                print("Please solve the CAPTCHA in the browser window.")
                print("Once solved, the script will continue automatically.")
                print("=============================\n")
                
                # Wait for navigation after CAPTCHA is solved
                try:
                    # Wait for a selector that would appear on a typical post-CAPTCHA page
                    self.page.wait_for_selector("body", timeout=300000)  # 5 min timeout
                    # Wait for network activity to settle
                    self.page.wait_for_load_state("networkidle")
                    logger.info("CAPTCHA solved, continuing")
                except Exception as e:
                    logger.warning(f"Timeout waiting for CAPTCHA to be solved: {e}")
                    # Try to get whatever content is available
                    return self.page.content(), False
            
            # Wait for page to load fully
            self.page.wait_for_load_state("networkidle")
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            # Get the page source
            page_source = self.page.content()
            
            return page_source, True
            
        except Exception as e:
            logger.warning(f"Playwright error for {url}: {e}")
            # Try to get whatever page source is available
            try:
                return self.page.content(), False
            except:
                return None, False
    
    def _get_with_requests(self, url: str) -> Tuple[Optional[str], bool]:
        """
        Get page content using the requests library.
        
        Args:
            url: URL to scrape
            
        Returns:
            Tuple of (HTML content or None, success boolean)
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                return response.text, True
            else:
                logger.warning(f"Failed to fetch {url}: Status code {response.status_code}")
                return None, False
                
        except requests.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            return None, False
    
    def _get_with_browser(self, url: str) -> Tuple[Optional[str], bool]:
        """
        Get page content using Playwright browser.
        
        Args:
            url: URL to scrape
            
        Returns:
            Tuple of (HTML content or None, success boolean)
        """
        if not self.browser or not self.page:
            self._init_browser()
            if not self.browser or not self.page:
                return self._get_with_requests(url)
        
        try:
            self.page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Wait for page to load (body element to be present)
            self.page.wait_for_selector("body", timeout=20000)
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            # Get the page source
            page_source = self.page.content()
            
            return page_source, True
            
        except Exception as e:
            logger.warning(f"Playwright error for {url}: {e}")
            # Try to get whatever page source is available
            try:
                return self.page.content(), False
            except:
                return None, False
    
    def search_hotel(self, hotel_name: str, location: str) -> List[Dict[str, str]]:
        """
        Search for a hotel and return potential URLs to scrape.
        
        Args:
            hotel_name: Name of the hotel or search query
            location: Location of the hotel (city, state)
            
        Returns:
            List of dictionaries with URL information
        """
        search_query = f"{hotel_name} {location}"
        search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        
        logger.info(f"Searching with URL: {search_url}")
        
        # Using browser for search to allow manual CAPTCHA solving
        if not self.browser or not self.page:
            self._init_browser()
            
        if not self.browser or not self.page:
            logger.error("Browser initialization failed")
            return []
        
        try:
            # Navigate to search URL
            self.page.goto(search_url, wait_until="networkidle", timeout=60000)
            
            # Check for CAPTCHA
            captcha_selectors = ["#captcha", "input[name='captcha']", "iframe[title*='captcha']", 
                                "iframe[src*='recaptcha']", "iframe[src*='captcha']"]
            
            captcha_detected = False
            for selector in captcha_selectors:
                try:
                    if self.page.query_selector(selector):
                        captcha_detected = True
                        break
                except:
                    pass
                    
            if captcha_detected or "recaptcha" in self.page.content().lower() or "captcha" in self.page.content().lower():
                logger.warning("CAPTCHA detected! Please solve it manually in the browser window.")
                print("\n==== CAPTCHA DETECTED ====")
                print("Please solve the CAPTCHA in the browser window.")
                print("Once solved, the script will continue automatically.")
                print("=============================\n")
                
                # Wait for navigation after CAPTCHA is solved
                # This could be when a selector that typically appears in search results is visible
                try:
                    self.page.wait_for_selector(".g, .Gx5Zad, #search", timeout=300000)  # 5 min timeout
                    logger.info("CAPTCHA solved, continuing with search")
                except Exception as e:
                    logger.warning(f"Timeout waiting for CAPTCHA to be solved: {e}")
                    return []
            
            # Wait a bit to ensure page is fully loaded
            self.page.wait_for_load_state("networkidle")
            
            # Get the page content
            content = self.page.content()
            
            # Save content to a debug file
            with open("search_debug.html", "w", encoding="utf-8") as f:
                f.write(content)
            
            # Parse the content with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            results = []
            
            # Try different Google search result selectors
            selectors = ['.g', '.srg .g', '.Gx5Zad', 'div[data-hveid]']
            found_items = []
            
            for selector in selectors:
                found_items = soup.select(selector)
                if found_items:
                    logger.info(f"Found {len(found_items)} results with selector: {selector}")
                    break
            
            # Extract search results from the found items
            for result in found_items:
                try:
                    # Find link - try multiple possible selectors
                    link_element = (result.select_one('.yuRUbf a') or 
                                result.select_one('a') or 
                                result.select_one('[href]'))
                    
                    if not link_element:
                        continue
                        
                    url = link_element.get('href', '')
                    if not url.startswith('http'):
                        continue
                    
                    # Get the title - try multiple selectors
                    title_element = (result.select_one('h3') or 
                                    result.select_one('.LC20lb') or
                                    link_element)
                    
                    title = title_element.text if title_element else "No title"
                    
                    # Get the snippet - try multiple selectors
                    snippet_element = (result.select_one('.IsZvec') or 
                                    result.select_one('.VwiC3b') or
                                    result.select_one('.st'))
                    
                    snippet = snippet_element.text if snippet_element else "No description"
                    
                    # Parse URL to get domain
                    parsed_url = urlparse(url)
                    domain = parsed_url.netloc
                    
                    results.append({
                        "url": url,
                        "title": title,
                        "snippet": snippet,
                        "domain": domain
                    })
                
                except Exception as e:
                    logger.error(f"Error parsing search result: {e}")
                    continue
            
            logger.info(f"Extracted {len(results)} results from search")
            return results
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def find_hotel_official_site(self, hotel_name: str, location: str) -> Optional[str]:
        """
        Find the official website for a hotel.
        
        Args:
            hotel_name: Name of the hotel
            location: Location of the hotel (city, state)
            
        Returns:
            URL of the official hotel website, or None if not found
        """
        search_results = self.search_hotel(hotel_name, location)
        
        # Look for official site - prioritize hotel brand domains
        common_hotel_domains = [
            'marriott.com', 'hilton.com', 'hyatt.com', 'ihg.com',
            'wyndham.com', 'choicehotels.com', 'radissonhotels.com',
            'accor.com', 'bestwestern.com', 'fourseasons.com', 
            'stregishotels.com', 'ritzcarlton.com', 'mandarinoriental.com'
        ]
        
        # First try to find a direct match with a common hotel domain
        for result in search_results:
            domain = result["domain"]
            
            for hotel_domain in common_hotel_domains:
                if hotel_domain in domain and hotel_name.lower() in result["title"].lower():
                    return result["url"]
        
        # Then look for hotel name in the domain
        for result in search_results:
            hotel_name_parts = hotel_name.lower().split()
            domain = result["domain"].lower()
            
            # Check if domain contains substantial parts of the hotel name
            if any(part in domain for part in hotel_name_parts if len(part) > 3):
                if "hotel" in domain or "resort" in domain or "inn" in domain:
                    return result["url"]
        
        # Fall back to first result if it seems relevant
        if search_results and hotel_name.lower() in search_results[0]["title"].lower():
            return search_results[0]["url"]
        
        return None
    
    def search_hotel_on_booking(self, hotel_name: str, location: str) -> Optional[str]:
        """
        Search for a hotel on Booking.com and return the URL to its page.
        
        Args:
            hotel_name: Name of the hotel
            location: Location of the hotel (city, state)
            
        Returns:
            URL to the hotel's page on Booking.com, or None if not found
        """
        search_query = f"{hotel_name} {location} site:booking.com"
        search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        
        content, success = self._get_with_browser(search_url) if self.use_browser else self._get_with_requests(search_url)
        
        if not content or not success:
            logger.warning(f"Failed to search for {hotel_name} on Booking.com")
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for Booking.com result
        for result in soup.select('.g'):
            link_element = result.select_one('.yuRUbf a')
            if not link_element:
                continue
                
            url = link_element.get('href', '')
            
            if 'booking.com' in url and '/hotel/' in url:
                return url
        
        return None
    
    def search_hotel_on_tripadvisor(self, hotel_name: str, location: str) -> Optional[str]:
        """
        Search for a hotel on TripAdvisor and return the URL to its page.
        
        Args:
            hotel_name: Name of the hotel
            location: Location of the hotel (city, state)
            
        Returns:
            URL to the hotel's page on TripAdvisor, or None if not found
        """
        search_query = f"{hotel_name} {location} site:tripadvisor.com"
        search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        
        content, success = self._get_with_browser(search_url) if self.use_browser else self._get_with_requests(search_url)
        
        if not content or not success:
            logger.warning(f"Failed to search for {hotel_name} on TripAdvisor")
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for TripAdvisor result
        for result in soup.select('.g'):
            link_element = result.select_one('.yuRUbf a')
            if not link_element:
                continue
                
            url = link_element.get('href', '')
            
            if 'tripadvisor.com' in url and ('/Hotel_Review-' in url or '/h' in url):
                return url
        
        return None
    
    def extract_images_from_page(self, html_content: str, base_url: str) -> Dict[str, List[str]]:
        """
        Extract images from a webpage.
        
        Args:
            html_content: HTML content of the page
            base_url: Base URL for resolving relative URLs
            
        Returns:
            Dictionary with exterior and room image URLs
        """
        if not html_content:
            return {"exterior": [], "rooms": []}
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        image_urls = []
        exterior_keywords = ['exterior', 'outside', 'building', 'hotel-', 'facade', 'front']
        room_keywords = ['room', 'guest', 'suite', 'bedroom', 'king', 'queen', 'double', 'twin']
        
        # Find all images
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if not src:
                data_src = img.get('data-src', '')
                if data_src:
                    src = data_src
                else:
                    continue
            
            # Resolve relative URLs
            if src.startswith('/'):
                src = urljoin(base_url, src)
            
            # Skip tiny images, icons, logos
            if 'icon' in src.lower() or 'logo' in src.lower():
                continue
                
            # Skip images that are clearly too small (often icons)
            width = img.get('width', '')
            height = img.get('height', '')
            if width and height:
                try:
                    if int(width) < 100 or int(height) < 100:
                        continue
                except ValueError:
                    pass
            
            image_urls.append({
                'src': src,
                'alt': img.get('alt', '').lower(),
                'class': ' '.join(img.get('class', [])).lower() if img.get('class') else ''
            })
        
        # Categorize images
        exterior_images = []
        room_images = []
        
        for img in image_urls:
            text = f"{img['alt']} {img['class']}"
            
            # Check for exterior images
            if any(keyword in text for keyword in exterior_keywords):
                exterior_images.append(img['src'])
            
            # Check for room images
            if any(keyword in text for keyword in room_keywords):
                room_images.append(img['src'])
        
        return {
            "exterior": exterior_images[:5],  # Limit to top 5
            "rooms": room_images[:10]  # Limit to top 10
        }
    
    def __del__(self):
        """Cleanup when the object is garbage collected."""
        self.close()
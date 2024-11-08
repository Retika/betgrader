import requests
from bs4 import BeautifulSoup
import pandas as pd
from typing import Optional, Dict, Any
from io import StringIO

class TableExtractor:
    def __init__(self, debug=False):
        self.debug = debug
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetch the webpage content."""
        try:
            if self.debug:
                print(f"\nFetching URL: {url}")
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            if self.debug:
                print(f"Status Code: {response.status_code}")
            
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return None

    def extract_table(self, html_content: str) -> Optional[Dict[str, Any]]:
        """Extract the first table from the HTML and convert it to JSON format."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            table = soup.find('table')
            if not table:
                if self.debug:
                    print("No table found on the page")
                return None

            # Fix the FutureWarning by using StringIO
            df = pd.read_html(StringIO(str(table)))[0]
            
            result = {
                'table_data': df.to_dict(orient='records'),
                'columns': df.columns.tolist()
            }
            
            if self.debug:
                print("\nExtracted Table Data:")
                print(f"Columns: {result['columns']}")
                print("Data:")
                print(df.to_string())
            
            return result

        except Exception as e:
            print(f"Error extracting table: {e}")
            return None

    def get_table_from_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Main method to get table data from a URL."""
        html_content = self.fetch_page(url)
        if html_content:
            return self.extract_table(html_content)
        return None
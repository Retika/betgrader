from typing import Optional, Dict, Any
from groq import Groq
from data_statmuse_tablepull import TableExtractor

class BetGrader:
    def __init__(self, api_key: str, debug=True):
        self.client = Groq(api_key=api_key)
        self.table_extractor = TableExtractor(debug=debug)
        self.debug = debug
        self.model = "llama-3.1-70b-versatile"
        self.debug_output = []  # Store debug messages

    def log_debug(self, message: str):
        """Add debug message to debug_output list"""
        if self.debug:
            print(message)
            self.debug_output.append(message)

    def generate_query(self, sportsbet_prompt: str) -> str:
        """Generate a query question based on the sports bet prompt."""
        prompt = f"""Create a query to get player statistics for this bet. The query should:
1. Ask for the specific stat mentioned in the bet
2. Include the player's name and team matchup
3. Specify the exact date
4. Be phrased as a direct question about the statistic

Bet: {sportsbet_prompt}

Return ONLY the question, nothing else."""

        self.log_debug(f"\nGenerating Query for: {sportsbet_prompt}")
        self.log_debug(f"Prompt: {prompt}")

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            stream=False
        )
        
        query = response.choices[0].message.content.strip()
        self.log_debug(f"Generated Query: {query}")
        return query

    def generate_statmuse_url(self, query: str) -> str:
        """Convert the query into a Statmuse URL."""
        prompt = f"""Convert this query to a Statmuse URL. Use the format:
https://www.statmuse.com/[sport]/ask/[query]

Important:
- Replace spaces with +
- Use proper URL encoding
- Include date in MM/DD/YYYY format
- Use @ symbol for team matchups

Query: {query}

Return only the URL, nothing else."""

        self.log_debug(f"\nGenerating URL for: {query}")
        self.log_debug(f"Prompt: {prompt}")

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            stream=False
        )
        
        url = response.choices[0].message.content.strip()
        self.log_debug(f"Generated URL: {url}")
        return url

    def grade_bet(self, table_data: Dict[str, Any], sportsbet_prompt: str) -> str:
        """Grade the bet based on the table data."""
        prompt = f"""Grade this sports bet based on the statistical data.

Bet Format Explanation:
- 'o' means over (bet wins if actual value is GREATER than the number)
- 'u' means under (bet wins if actual value is LESS than the number)
- Exact match equals a 'Push'
- If data is unclear or missing, return 'N/A'

Original Bet: {sportsbet_prompt}
Statistical Data: {table_data}

Analyze the data carefully and respond with ONLY one of these options: 'Win', 'Loss', 'Push', or 'N/A'"""

        self.log_debug(f"\nGrading Bet: {sportsbet_prompt}")
        self.log_debug(f"Table Data: {table_data}")
        self.log_debug(f"Grading Prompt: {prompt}")

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            stream=False
        )
        
        result = response.choices[0].message.content.strip()
        self.log_debug(f"Grade Result: {result}")
        return result

    def process_bet(self, sportsbet_prompt: str) -> tuple[str, Optional[Dict[str, Any]]]:
    """Process the entire bet grading workflow."""
    try:
        self.debug_output = []  # Clear previous debug output
        self.log_debug(f"\n=== Processing Bet: {sportsbet_prompt} ===")

        query = self.generate_query(sportsbet_prompt)
        url = self.generate_statmuse_url(query)
        table_data = self.table_extractor.get_table_from_url(url)
        
        if not table_data:
            self.log_debug("No table data found - returning N/A")
            return "N/A", None
        
        result = self.grade_bet(table_data, sportsbet_prompt)
        self.log_debug(f"\n=== Final Result: {result} ===")
        
        return result, table_data
        
    except Exception as e:
        self.log_debug(f"Error processing bet: {str(e)}")
        return "N/A", None
from typing import Optional, Dict, Any, Tuple
from groq import Groq
from data_statmuse_tablepull import TableExtractor

class BetGrader:
    def __init__(self, api_key: str, debug=True):
        self.client = Groq(api_key=api_key)
        self.table_extractor = TableExtractor(debug=debug)
        self.debug = debug
        self.model = "llama-3.1-70b-versatile"
        self.debug_output = []
        self.max_retries = 3

    def log_debug(self, message: str):
        if self.debug:
            print(message)
            self.debug_output.append(message)

    def generate_query(self, sportsbet_prompt: str, attempt: int = 1) -> str:
        """Generate query with different phrasings based on attempt number"""
        
        base_prompts = {
            1: f"""Create a query to get player statistics for this bet. The query should:
1. Ask for the specific stat mentioned in the bet
2. Include the player's name and team matchup
3. Specify the exact date
4. Be phrased as a direct question about the statistic

Bet: {sportsbet_prompt}

Return ONLY the question, nothing else.""",

            2: f"""Rephrase the following bet into a statistical query. Focus on:
1. The exact player name
2. The specific game date
3. The team matchup
4. The core statistic needed
Use common statistical abbreviations (pts, ast, reb, sog, etc.)

Bet: {sportsbet_prompt}

Return ONLY the question, nothing else.""",

            3: f"""Create a basic query for Statmuse about this player's performance. Make it:
1. Simple and direct
2. Use the most common stat terminology
3. Focus on the exact date and teams
4. Include only essential information

Bet: {sportsbet_prompt}

Return ONLY the question, nothing else."""
        }

        prompt = base_prompts.get(attempt, base_prompts[1])
        self.log_debug(f"\nGenerating Query (Attempt {attempt}) for: {sportsbet_prompt}")
        self.log_debug(f"Prompt: {prompt}")

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            stream=False
        )
        
        query = response.choices[0].message.content.strip()
        self.log_debug(f"Generated Query (Attempt {attempt}): {query}")
        return query

    def generate_statmuse_url(self, query: str, attempt: int = 1) -> str:
        """Generate URL with different formats based on attempt number"""
        
        base_prompts = {
            1: """Use format: https://www.statmuse.com/[sport]/ask/[query]""",
            2: """Use format: https://www.statmuse.com/[sport]/ask?q=[query]""",
            3: """Use format: https://www.statmuse.com/[sport]/players/[player]/game-log"""
        }

        prompt = f"""Convert this query to a Statmuse URL. {base_prompts[attempt]}

Important:
- Replace spaces with +
- Use proper URL encoding
- Include date in MM/DD/YYYY format
- Use @ symbol for team matchups

Query: {query}

Return only the URL, nothing else."""

        self.log_debug(f"\nGenerating URL (Attempt {attempt}) for: {query}")
        self.log_debug(f"Prompt: {prompt}")

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            stream=False
        )
        
        url = response.choices[0].message.content.strip()
        self.log_debug(f"Generated URL (Attempt {attempt}): {url}")
        return url

    def try_get_table(self, sportsbet_prompt: str) -> Tuple[Optional[Dict[str, Any]], str, str]:
        """Try different approaches to get table data"""
        for attempt in range(1, self.max_retries + 1):
            self.log_debug(f"\n=== Attempt {attempt} of {self.max_retries} ===")
            
            query = self.generate_query(sportsbet_prompt, attempt)
            url = self.generate_statmuse_url(query, attempt)
            table_data = self.table_extractor.get_table_from_url(url)
            
            if table_data:
                self.log_debug(f"Successfully got table data on attempt {attempt}")
                return table_data, query, url
            
            self.log_debug(f"Attempt {attempt} failed to get table data")
        
        return None, "", ""

    def grade_bet(self, table_data: Dict[str, Any], sportsbet_prompt: str) -> str:
        prompt = f"""Grade this sports bet based on the statistical data.

Bet Format Explanation:
- 'o' means over (bet wins if actual value is GREATER than the number)
- 'u' means under (bet wins if actual value is LESS than the number)
- Exact match equals a 'Push'
- If data is unclear or missing, return 'N/A'

Original Bet: {sportsbet_prompt}
Statistical Data: {table_data}

Use your best judgement based on the data available, sometimes PTS is represented as P, or SOG is Shots on Goal, so you're really looking for Shots, or S.  Review the data carefully and come to a proper conclusion with your knowledge of the sport and how its statistics are commonly tracked.  You are a professional sports better, sports analyst, and also a professional statistician.

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
            self.debug_output = []
            self.log_debug(f"\n=== Processing Bet: {sportsbet_prompt} ===")

            table_data, final_query, final_url = self.try_get_table(sportsbet_prompt)
            
            if not table_data:
                self.log_debug("Failed to get table data after all attempts - returning N/A")
                return "N/A", None
            
            self.log_debug(f"Successfully retrieved table using query: {final_query}")
            self.log_debug(f"Final URL used: {final_url}")
            
            result = self.grade_bet(table_data, sportsbet_prompt)
            self.log_debug(f"\n=== Final Result: {result} ===")
            
            return result, table_data
            
        except Exception as e:
            self.log_debug(f"Error processing bet: {str(e)}")
            return "N/A", None
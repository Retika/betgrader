from typing import Optional, Dict, Any
from groq import Groq
from data_statmuse_tablepull import TableExtractor

class BetGrader:
    def __init__(self, api_key: str, debug=True):
        self.client = Groq(api_key=api_key)
        self.table_extractor = TableExtractor(debug=debug)
        self.debug = debug
        self.model = "llama-3.1-70b-versatile"  # Updated model

    def generate_query(self, sportsbet_prompt: str) -> str:
        """Generate a query question based on the sports bet prompt."""
        prompt = f"""I'm trying to create a query to figure out if this sports bet won. Please generate a single question for an online player stats database for this. Phrase the question clearly and concisely, asking for data so it shouldn't be a yes/no question. Return ONLY the question and nothing else as I'm passing the output directly to another function.

Bet: {sportsbet_prompt}"""

        if self.debug:
            print("\nGenerating Query:")
            print(f"Input Prompt: {sportsbet_prompt}")
            print(f"Full LLM Prompt: {prompt}")

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            stream=False
        )
        
        query = response.choices[0].message.content.strip()
        
        if self.debug:
            print(f"Generated Query: {query}")
        
        return query

    def generate_statmuse_url(self, query: str) -> str:
        """Convert the query into a Statmuse URL."""
        prompt = f"""I want to convert this to a proper Statmuse URL output, here is an example: "https://www.statmuse.com/nhl/ask?q=what+is+the+number+of+shots+on+goal+scored+by+d.+pastrnak+in+the+cgy%40bos+game+played+on+11%2F7%2F2024". Please only output the URL and nothing else as I'm passing the output straight into another function

Query: {query}"""

        if self.debug:
            print("\nGenerating Statmuse URL:")
            print(f"Input Query: {query}")
            print(f"Full LLM Prompt: {prompt}")

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            stream=False
        )
        
        url = response.choices[0].message.content.strip()
        
        if self.debug:
            print(f"Generated URL: {url}")
        
        return url

    def grade_bet(self, table_data: Dict[str, Any], sportsbet_prompt: str) -> str:
        """Grade the bet based on the table data."""
        prompt = f"""Grade this bet based on the table data and the query, using your best knowledge of what each stat represents in the standard form.  Reply ONLY with one of these four options: 'Win', 'Loss', 'Push', or 'N/A'

Original Bet: {sportsbet_prompt}
Statistical Data: {table_data}"""

        if self.debug:
            print("\nGrading Bet:")
            print(f"Original Bet: {sportsbet_prompt}")
            print(f"Table Data: {table_data}")
            print(f"Full LLM Prompt: {prompt}")

        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            stream=False
        )
        
        result = response.choices[0].message.content.strip()
        
        if self.debug:
            print(f"Grading Result: {result}")
        
        return result

    def process_bet(self, sportsbet_prompt: str) -> str:
        """Process the entire bet grading workflow."""
        try:
            if self.debug:
                print("\n=== Starting Bet Processing ===")
                print(f"Input Bet: {sportsbet_prompt}")

            # Step 1: Generate the initial query
            query = self.generate_query(sportsbet_prompt)
            
            # Step 2: Convert query to Statmuse URL
            url = self.generate_statmuse_url(query)
            
            # Step 3: Extract table data
            table_data = self.table_extractor.get_table_from_url(url)
            
            if not table_data:
                if self.debug:
                    print("\nNo table data found - returning N/A")
                return "N/A"
            
            # Step 4: Grade the bet
            result = self.grade_bet(table_data, sportsbet_prompt)
            
            if self.debug:
                print("\n=== Bet Processing Complete ===")
                print(f"Final Result: {result}")
            
            return result
            
        except Exception as e:
            print(f"Error processing bet: {e}")
            return "N/A"

def main():
    # Example usage
    api_key = "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"
    grader = BetGrader(api_key)
    
    # Example bet
    sportsbet_prompt = "11/7/2024   E.Lindholm Anytime Goal Scorer Yes (Live) | CGY@BOS NHL Prop"
    
    result = grader.process_bet(sportsbet_prompt)
    print(f"Bet Result: {result}")

if __name__ == "__main__":
    main()
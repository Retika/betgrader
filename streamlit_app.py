import streamlit as st
from groq import Groq
from data_statmuse_tablepull import TableExtractor
from groq_bet_grader import BetGrader
import os
import pandas as pd
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Sports Bet Grader",
    page_icon="🎲",
    layout="wide"
)

# Initialize session state for storing API key
if 'groq_api_key' not in st.session_state:
    st.session_state.groq_api_key = st.secrets["GROQ_API_KEY"]
if 'history' not in st.session_state:
    st.session_state.history = []

def grade_bet(bet: str, api_key: str, show_debug: bool = False) -> tuple[str, list, dict]:
    """Grade a single bet and return result, debug info, and table data"""
    grader = BetGrader(api_key, debug=show_debug)
    result, table_data = grader.process_bet(bet)  # Modified to return table_data
    return result, grader.debug_output, table_data

def display_table_data(table_data: dict):
    """Display table data in a formatted way"""
    if table_data and 'table_data' in table_data:
        df = pd.DataFrame(table_data['table_data'])
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No table data available")

def main():
    st.title("🎲 Sports Bet Grader")
    
    # Sidebar for API key and history
    with st.sidebar:
        st.header("Settings")
        api_key = st.text_input(
            "Enter Groq API Key",
            type="password",
            value=st.session_state.groq_api_key,
            help="Enter your Groq API key. It will be stored in the session state."
        )
        st.session_state.groq_api_key = api_key
        
        if st.button("Clear History") and st.session_state.history:
            st.session_state.history = []
            st.success("History cleared!")

    # Main content
    tab1, tab2 = st.tabs(["Grade Bets", "History"])

    with tab1:
        st.markdown("""
        ### Enter Your Bet Details
        Format: `DATE    PLAYER o/u NUMBER STAT | TEAMS    LEAGUE`
        
        Example: `11/7/2024    A.Iosivas o21.5 Rec Yds | CIN@BAL    NFL`
        """)

        with st.form("bet_form"):
            bet_input = st.text_area(
                "Bet Details",
                height=100,
                help="Enter one bet per line in the specified format"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                show_debug = st.checkbox("Show Debug Output", value=False)
            with col2:
                auto_archive = st.checkbox("Auto-save to History", value=True)
            
            submitted = st.form_submit_button("Grade Bet(s)")

        if submitted:
            if not st.session_state.groq_api_key:
                st.error("Please enter your Groq API key in the sidebar first!")
                return

            try:
                bets = [bet.strip() for bet in bet_input.split('\n') if bet.strip()]
                
                if not bets:
                    st.warning("Please enter at least one bet to grade.")
                    return
                
                st.markdown("### Results")
                
                for bet in bets:
                    with st.expander(f"Bet: {bet}", expanded=True):
                        with st.spinner("Grading..."):
                            result, debug_output, table_data = grade_bet(
                                bet, 
                                st.session_state.groq_api_key, 
                                show_debug
                            )
                            
                            # Display Original Bet
                            st.markdown("#### Original Bet")
                            st.code(bet)
                            
                            # Display Data Used for Grading
                            st.markdown("#### Statistical Data")
                            display_table_data(table_data)
                            
                            # Display Result with Explanation
                            st.markdown("#### Result")
                            col1, col2 = st.columns([1, 4])
                            
                            with col1:
                                if result == "Win":
                                    st.success("WIN")
                                elif result == "Loss":
                                    st.error("LOSS")
                                elif result == "Push":
                                    st.warning("PUSH")
                                else:
                                    st.info("N/A")
                            
                            with col2:
                                # Extract bet details
                                bet_parts = bet.split()
                                for part in bet_parts:
                                    if 'o' in part or 'u' in part:
                                        threshold = part
                                        break
                                else:
                                    threshold = "unknown"
                                
                                if table_data and 'table_data' in table_data and table_data['table_data']:
                                    actual_value = table_data['table_data'][0]  # Get first row of data
                                    st.markdown(f"""
                                    **Bet Details:**
                                    - Threshold: {threshold}
                                    - Actual Value: {actual_value}
                                    """)
                            
                            # Display Debug Information
                            if show_debug:
                                st.markdown("#### Debug Output")
                                for msg in debug_output:
                                    st.text(msg)
                            
                            if auto_archive:
                                st.session_state.history.append({
                                    'bet': bet,
                                    'result': result,
                                    'data': table_data,
                                    'timestamp': datetime.now()
                                })

            except Exception as e:
                st.error(f"Error: {str(e)}")
                if show_debug:
                    st.exception(e)

    with tab2:
        if st.session_state.history:
            st.markdown("### Bet History")
            
            history_df = pd.DataFrame(st.session_state.history)
            
            for _, row in history_df.iterrows():
                with st.expander(f"{row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {row['bet']}", expanded=False):
                    st.code(row['bet'])  # Show original bet
                    if 'data' in row:
                        st.markdown("#### Statistical Data")
                        display_table_data(row['data'])
                    st.markdown("#### Result")
                    if row['result'] == "Win":
                        st.success(f"Result: {row['result']}")
                    elif row['result'] == "Loss":
                        st.error(f"Result: {row['result']}")
                    elif row['result'] == "Push":
                        st.warning(f"Result: {row['result']}")
                    else:
                        st.info(f"Result: {row['result']}")
        else:
            st.info("No history available yet.")

if __name__ == "__main__":
    main()
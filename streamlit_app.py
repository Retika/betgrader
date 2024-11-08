import streamlit as st
from groq import Groq
from data_statmuse_tablepull import TableExtractor
from groq_bet_grader import BetGrader
import os

# Set page config
st.set_page_config(
    page_title="Sports Bet Grader",
    page_icon="🎲",
    layout="wide"
)

# Initialize session state for storing API key and history
if 'groq_api_key' not in st.session_state:
    st.session_state.groq_api_key = os.getenv('GROQ_API_KEY', '')
if 'history' not in st.session_state:
    st.session_state.history = []

def main():
    st.title("🎲 Sports Bet Grader")
    
    # Sidebar for API key and history
    with st.sidebar:
        st.header("Settings")
        
        # API Key input
        api_key = st.text_input(
            "Enter Groq API Key",
            type="password",
            value=st.session_state.groq_api_key,
            help="Enter your Groq API key. It will be stored in the session state."
        )
        st.session_state.groq_api_key = api_key
        
        # Clear history button
        if st.button("Clear History") and st.session_state.history:
            st.session_state.history = []
            st.success("History cleared!")

    # Main content area tabs
    tab1, tab2 = st.tabs(["Grade Bets", "History"])

    with tab1:
        st.markdown("""
        ### Enter Your Bet Details
        Format: `DATE    PLAYER o/u NUMBER STAT | TEAMS    LEAGUE`
        
        Example: `11/7/2024    A.Iosivas o21.5 Rec Yds | CIN@BAL    NFL`
        """)

        # Input form
        with st.form("bet_form"):
            bet_input = st.text_area(
                "Bet Details",
                height=100,
                help="Enter one bet per line in the specified format"
            )
            
            # Additional options
            col1, col2 = st.columns(2)
            with col1:
                show_debug = st.checkbox("Show Debug Output", value=False)
            with col2:
                auto_archive = st.checkbox("Auto-save to History", value=True)
            
            submitted = st.form_submit_button("Grade Bet(s)")

        # Process bets when form is submitted
        if submitted:
            if not st.session_state.groq_api_key:
                st.error("Please enter your Groq API key in the sidebar first!")
                return

            try:
                grader = BetGrader(st.session_state.groq_api_key, debug=show_debug)
                
                # Process each bet
                bets = [bet.strip() for bet in bet_input.split('\n') if bet.strip()]
                
                if not bets:
                    st.warning("Please enter at least one bet to grade.")
                    return
                
                # Results section
                st.markdown("### Results")
                
                # Create a container for results
                results_container = st.container()
                
                with results_container:
                    for bet in bets:
                        # Create expander for each bet
                        with st.expander(f"Bet: {bet}", expanded=True):
                            with st.spinner("Grading..."):
                                result = grader.process_bet(bet)
                                
                                # Display result with appropriate styling
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.markdown(f"**Original Bet:** `{bet}`")
                                
                                with col2:
                                    if result == "Win":
                                        st.success("WIN")
                                    elif result == "Loss":
                                        st.error("LOSS")
                                    elif result == "Push":
                                        st.warning("PUSH")
                                    else:  # N/A
                                        st.info("N/A")
                                
                                # Show debug output if enabled
                                if show_debug:
                                    st.code(grader.debug_output)  # You'll need to add this attribute to your BetGrader class
                                
                                # Add to history if auto-archive is enabled
                                if auto_archive:
                                    st.session_state.history.append({
                                        'bet': bet,
                                        'result': result,
                                        'timestamp': pd.Timestamp.now()
                                    })

            except Exception as e:
                st.error(f"Error: {str(e)}")
                if show_debug:
                    st.exception(e)

    # History tab
    with tab2:
        if st.session_state.history:
            st.markdown("### Bet History")
            
            # Convert history to DataFrame for easy display
            import pandas as pd
            history_df = pd.DataFrame(st.session_state.history)
            
            # Display history with colored results
            for _, row in history_df.iterrows():
                with st.expander(f"{row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {row['bet']}", expanded=False):
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
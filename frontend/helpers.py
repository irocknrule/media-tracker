"""Helper functions for common UI patterns."""
import streamlit as st
from datetime import date
from query_params import get_filter_from_query_params, update_query_params


def get_year_filter(filter_key: str):
    """Get and manage year filter with session state tracking.
    
    Args:
        filter_key: The query parameter key for the filter (e.g., 'movie_year', 'tv_year')
    
    Returns:
        The selected year filter value (int or "All (year)" string)
    """
    current_year = date.today().year
    year_options = [f"All ({current_year})"] + list(reversed(range(2020, current_year + 2)))
    persisted_year = get_filter_from_query_params(filter_key, f"All ({current_year})")
    
    # Normalize persisted_year to match year_options format
    if persisted_year == "All" or str(persisted_year).startswith("All ("):
        persisted_year = f"All ({current_year})"
    elif isinstance(persisted_year, (int, str)):
        try:
            year_int = int(persisted_year)
            if year_int in year_options:
                persisted_year = year_int
            else:
                persisted_year = f"All ({current_year})"
        except (ValueError, TypeError):
            persisted_year = f"All ({current_year})"
    else:
        persisted_year = f"All ({current_year})"
    
    # Use session state to track the selected year to avoid query param timing issues
    session_key = f"{filter_key}_selected"
    if session_key not in st.session_state:
        st.session_state[session_key] = persisted_year
    
    default_index = year_options.index(st.session_state[session_key]) if st.session_state[session_key] in year_options else 0
    
    # Make dropdown smaller using column layout
    col1, col2, col3 = st.columns([1, 2, 2])
    with col1:
        year_filter = st.selectbox("Filter by Year", year_options, index=default_index, key=f"{filter_key}_filter_widget")
    
    # Update session state and query params when selection changes
    if year_filter != st.session_state[session_key]:
        st.session_state[session_key] = year_filter
        update_query_params(**{filter_key: year_filter})
        st.rerun()
    
    # Return the session state value for filtering
    return st.session_state[session_key]

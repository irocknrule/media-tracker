"""Query parameter management for state persistence."""
import streamlit as st


def get_query_params():
    """Get query parameters with compatibility for old and new Streamlit versions"""
    try:
        # Try old experimental API (Streamlit < 1.30.0)
        if hasattr(st, 'experimental_get_query_params'):
            return st.experimental_get_query_params()
    except:
        pass
    
    try:
        # Try new API (Streamlit 1.30.0+)
        if hasattr(st, 'query_params'):
            return st.query_params
    except:
        pass
    
    # Return empty dict-like object if neither works
    class EmptyQueryParams:
        def __getitem__(self, key):
            raise KeyError(key)
        def __contains__(self, key):
            return False
        def to_dict(self):
            return {}
        def update(self, **kwargs):
            pass
    
    return EmptyQueryParams()


def initialize_state_from_query_params():
    """Initialize session state from query parameters to persist state across refreshes
    Query params always take precedence - they represent the "source of truth" for refresh scenarios"""
    query_params = get_query_params()
    
    # Check if query params exist - if they do, use them (this handles page refresh)
    has_query_params = False
    try:
        if "category" in query_params or "page" in query_params:
            has_query_params = True
    except:
        pass
    
    # Initialize category - query params take precedence
    if "category" in query_params:
        category = query_params["category"]
        # Handle list values from old API
        if isinstance(category, list) and len(category) > 0:
            category = category[0]
        valid_categories = ["Media Tracker", "Habit Tracker", "Portfolio Tracker"]
        if category in valid_categories:
            st.session_state["selected_category"] = category
        else:
            # Invalid category in query params, use default
            if "selected_category" not in st.session_state:
                st.session_state["selected_category"] = "Media Tracker"
    elif "selected_category" not in st.session_state:
        # No query param and no session state - use default
        st.session_state["selected_category"] = "Media Tracker"
    
    # Initialize page - query params take precedence
    if "page" in query_params:
        page = query_params["page"]
        # Handle list values from old API
        if isinstance(page, list) and len(page) > 0:
            page = page[0]
        category = st.session_state["selected_category"]
        
        # Validate page against category
        if category == "Media Tracker":
            valid_pages = ["Movies", "TV Shows", "Books", "Music", "Manual Entry", "Analytics"]
            if page in valid_pages:
                st.session_state["selected_page"] = page
            else:
                # Invalid page for category, use default
                if "selected_page" not in st.session_state:
                    st.session_state["selected_page"] = "Movies"
        elif category == "Habit Tracker":
            valid_pages = ["Log Habits", "Calendar", "Analytics"]
            if page in valid_pages:
                st.session_state["selected_page"] = page
            else:
                if "selected_page" not in st.session_state:
                    st.session_state["selected_page"] = "Log Habits"
        else:  # Portfolio Tracker
            valid_pages = ["Overview", "Transactions", "Upload Data", "Individual Holdings"]
            if page in valid_pages:
                st.session_state["selected_page"] = page
            else:
                if "selected_page" not in st.session_state:
                    st.session_state["selected_page"] = "Overview"
    elif "selected_page" not in st.session_state:
        # No query param and no session state - set default based on category
        category = st.session_state["selected_category"]
        if category == "Media Tracker":
            st.session_state["selected_page"] = "Movies"
        elif category == "Habit Tracker":
            st.session_state["selected_page"] = "Log Habits"
        else:
            st.session_state["selected_page"] = "Overview"


def update_query_params(category: str = None, page: str = None, **filters):
    """Update query parameters to persist state - returns True if update was needed"""
    params = {}
    
    # Always include category - use passed value, then session state, then query params
    if category:
        params["category"] = category
    elif "selected_category" in st.session_state:
        params["category"] = st.session_state["selected_category"]
    else:
        # Try to get from current query params
        try:
            query_params = get_query_params()
            if "category" in query_params:
                cat = query_params["category"]
                if isinstance(cat, list) and len(cat) > 0:
                    cat = cat[0]
                params["category"] = cat
        except:
            pass
    
    # Always include page - use passed value, then session state, then query params
    if page:
        params["page"] = page
    elif "selected_page" in st.session_state:
        params["page"] = st.session_state["selected_page"]
    else:
        # Try to get from current query params
        try:
            query_params = get_query_params()
            if "page" in query_params:
                pg = query_params["page"]
                if isinstance(pg, list) and len(pg) > 0:
                    pg = pg[0]
                params["page"] = pg
        except:
            pass
    
    # Add filter parameters
    for key, value in filters.items():
        # Skip if None or if it's an "All (year)" format
        if value is not None and value != "All" and not str(value).startswith("All ("):
            params[key] = str(value)
    
    # Try experimental API first (Streamlit < 1.30.0)
    try:
        if hasattr(st, 'experimental_set_query_params'):
            st.experimental_set_query_params(**params)
            return True
    except Exception as e:
        pass
    
    # Try new API (Streamlit 1.30.0+)
    try:
        if hasattr(st, 'query_params'):
            # First, clear year filter params if they're not in the new params
            # This handles the case when switching back to "All"
            year_filter_keys = ['tv_year', 'movie_year', 'book_year', 'music_year']
            for filter_key in year_filter_keys:
                if filter_key not in params and filter_key in st.query_params:
                    del st.query_params[filter_key]
            
            # Set each parameter individually for better reliability
            for key, value in params.items():
                st.query_params[key] = value
            return True
    except Exception as e:
        pass
    
    # If query params aren't available, just store in session state
    return False


def get_filter_from_query_params(filter_key: str, default_value=None):
    """Get filter value from query parameters"""
    query_params = get_query_params()
    try:
        if filter_key in query_params:
            value = query_params[filter_key]
            # Handle both single values and lists (old API returns lists)
            if isinstance(value, list) and len(value) > 0:
                value = value[0]
            # Try to convert to int if it's a number
            try:
                return int(value)
            except ValueError:
                return value
    except (KeyError, TypeError):
        pass
    return default_value

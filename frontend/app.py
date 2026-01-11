import streamlit as st
import requests
from datetime import date, datetime, timedelta
from typing import Optional
from collections import defaultdict
import json
import base64
import os

# Configuration
# Use environment variable if set, otherwise default to localhost
# For Docker: set API_BASE_URL=http://backend:8000 (internal Docker network)
# For external access: set API_BASE_URL=http://<host-ip>:8000
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="Personal Media Tracker",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


def make_authenticated_request(method: str, endpoint: str, **kwargs):
    """Make an API request"""
    url = f"{API_BASE_URL}{endpoint}"
    
    if method == "GET":
        response = requests.get(url, **kwargs)
    elif method == "POST":
        response = requests.post(url, **kwargs)
    elif method == "PUT":
        response = requests.put(url, **kwargs)
    elif method == "DELETE":
        response = requests.delete(url, **kwargs)
    else:
        raise ValueError(f"Unsupported method: {method}")
    
    return response


def search_media(media_type: str, query: str):
    """Search for media using the backend search API"""
    if not query or len(query) < 2:
        return []
    
    try:
        endpoint = f"/search/{media_type}"
        response = make_authenticated_request("GET", endpoint, params={"query": query})
        if response.status_code == 200:
            return response.json().get("results", [])
        return []
    except Exception as e:
        return []


def get_tv_show_seasons(tvmaze_id: int):
    """Get all seasons for a TV show"""
    try:
        endpoint = f"/search/tv-shows/{tvmaze_id}/seasons"
        response = make_authenticated_request("GET", endpoint)
        if response.status_code == 200:
            return response.json().get("seasons", [])
        return []
    except Exception as e:
        return []


def get_tv_show_thumbnail(title: str):
    """Get thumbnail URL for a TV show by title"""
    try:
        endpoint = "/search/tv-shows/thumbnail"
        response = make_authenticated_request("GET", endpoint, params={"title": title})
        if response.status_code == 200:
            return response.json().get("thumbnail_url")
        return None
    except Exception as e:
        return None


def display_search_results(results: list, key_prefix: str):
    """Display search results with thumbnails in a grid"""
    if not results:
        return None
    
    st.markdown("### Search Results")
    cols = st.columns(min(3, len(results)))
    
    selected_result = None
    session_key = f"{key_prefix}_selected_result"
    
    for idx, result in enumerate(results):
        col = cols[idx % len(cols)]
        with col:
            # Display thumbnail
            thumbnail = result.get("thumbnail", "")
            
            if thumbnail and thumbnail.strip() and thumbnail != "N/A":
                # Check if it's a valid HTTP URL
                if thumbnail.startswith("http://") or thumbnail.startswith("https://"):
                    # Try multiple methods to display the image
                    image_displayed = False
                    
                    # Method 1: Try HTML img tag (works better with external URLs)
                    try:
                        st.markdown(
                            f'<img src="{thumbnail}" width="150" style="border-radius: 8px; object-fit: cover;">', 
                            unsafe_allow_html=True
                        )
                        image_displayed = True
                    except:
                        pass
                    
                    # Method 2: Fallback to st.image if HTML fails
                    if not image_displayed:
                        try:
                            st.image(thumbnail, width=150, use_container_width=True)
                            image_displayed = True
                        except:
                            pass
                    
                    # Method 3: If both fail, show placeholder
                    if not image_displayed:
                        st.write("📷")
                else:
                    # Invalid URL format
                    st.write("📷")
            else:
                # No thumbnail available
                st.write("📷")
            
            # Display title and info
            title = result.get("title", "")
            year = result.get("year", "")
            author = result.get("author", "")
            artist = result.get("artist", "")
            
            # Show title
            st.write(f"**{title}**")
            if year:
                st.caption(f"Year: {year}")
            if author:
                st.caption(f"Author: {author}")
            if artist:
                st.caption(f"Artist: {artist}")
            
            if st.button(f"Select", key=f"{key_prefix}_select_{idx}"):
                st.session_state[session_key] = result
                st.rerun()
    
    # Check if result was previously selected
    if session_key in st.session_state:
        selected_result = st.session_state[session_key]
        st.success(f"✅ Selected: {selected_result.get('title', '')}")
        if st.button("Clear Selection", key=f"{key_prefix}_clear"):
            del st.session_state[session_key]
            st.rerun()
    
    return selected_result


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
    
    # Debug: Show what we're trying to set
    # st.write(f"DEBUG: Setting query params: {params}")
    
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


def main_app():
    """Main application"""
    # Initialize state from query parameters (persists across refreshes)
    initialize_state_from_query_params()
    
    # Ensure query params are set to match current state (for first load scenario)
    # This ensures that even on first load, the URL has query params that persist on refresh
    try:
        query_params = get_query_params()
        if "category" not in query_params or "page" not in query_params:
            # Query params missing - sync them with current session state
            update_query_params()
    except:
        pass
    
    # Top-level category selection - styled as tabs
    st.markdown("""
        <style>
        .category-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .category-tab {
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            text-align: center;
            flex: 1;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Define callbacks for category buttons
    def switch_to_media_tracker():
        st.session_state["selected_category"] = "Media Tracker"
        st.session_state["selected_page"] = "Movies"
        st.experimental_set_query_params(category="Media Tracker", page="Movies")
    
    def switch_to_habit_tracker():
        st.session_state["selected_category"] = "Habit Tracker"
        st.session_state["selected_page"] = "Log Habits"
        st.experimental_set_query_params(category="Habit Tracker", page="Log Habits")
    
    def switch_to_portfolio_tracker():
        st.session_state["selected_category"] = "Portfolio Tracker"
        st.session_state["selected_page"] = "Overview"
        st.experimental_set_query_params(category="Portfolio Tracker", page="Overview")
    
    def switch_to_workout_tracker():
        st.session_state["selected_category"] = "Workout Tracker"
        st.session_state["selected_page"] = "Log Workout"
        st.experimental_set_query_params(category="Workout Tracker", page="Log Workout")
    
    # Top-level tabs using columns for better layout
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.button("📚 Media Tracker", use_container_width=True, 
                  type="primary" if st.session_state["selected_category"] == "Media Tracker" else "secondary", 
                  key="btn_media_tracker",
                  on_click=switch_to_media_tracker)
    with col2:
        st.button("📅 Habit Tracker", use_container_width=True, 
                  type="primary" if st.session_state["selected_category"] == "Habit Tracker" else "secondary", 
                  key="btn_habit_tracker",
                  on_click=switch_to_habit_tracker)
    with col3:
        st.button("💼 Portfolio Tracker", use_container_width=True, 
                  type="primary" if st.session_state["selected_category"] == "Portfolio Tracker" else "secondary", 
                  key="btn_portfolio_tracker",
                  on_click=switch_to_portfolio_tracker)
    with col4:
        st.button("💪 Workout Tracker", use_container_width=True, 
                  type="primary" if st.session_state["selected_category"] == "Workout Tracker" else "secondary", 
                  key="btn_workout_tracker",
                  on_click=switch_to_workout_tracker)
    
    st.markdown("---")
    
    # Sidebar - dynamic based on category
    with st.sidebar:
        st.title("📊 Personal Tracker")
        st.markdown("---")
        
        # Show current category
        if st.session_state["selected_category"] == "Media Tracker":
            st.markdown("### 📚 Media Tracker")
            st.markdown("---")
            # Get current page from session state
            current_page = st.session_state.get("selected_page", "Movies")
            page_options = ["Movies", "TV Shows", "Books", "Music", "Manual Entry", "Analytics"]
            default_index = page_options.index(current_page) if current_page in page_options else 0
            
            page = st.radio(
                "Select Option",
                page_options,
                index=default_index,
                label_visibility="collapsed",
                key="media_tracker_page_radio"
            )
            
            # Always check and update if page changed
            if page != current_page:
                st.session_state["selected_page"] = page
                # Update query params with both category and page
                st.experimental_set_query_params(
                    category=st.session_state["selected_category"],
                    page=page
                )
        elif st.session_state["selected_category"] == "Habit Tracker":
            st.markdown("### 📅 Habit Tracker")
            st.markdown("---")
            current_page = st.session_state.get("selected_page", "Log Habits")
            page_options = ["Log Habits", "Calendar", "Analytics"]
            default_index = page_options.index(current_page) if current_page in page_options else 0
            
            page = st.radio(
                "Select Option",
                page_options,
                index=default_index,
                label_visibility="collapsed",
                key="habit_tracker_page_radio"
            )
            
            if page != current_page:
                st.session_state["selected_page"] = page
                st.experimental_set_query_params(
                    category=st.session_state["selected_category"],
                    page=page
                )
        else:  # Portfolio Tracker
            st.markdown("### 💼 Portfolio Tracker")
            st.markdown("---")
            current_page = st.session_state.get("selected_page", "Overview")
            page_options = ["Overview", "Asset Allocation", "Transactions", "Upload Data", "Individual Holdings"]
            default_index = page_options.index(current_page) if current_page in page_options else 0
            
            page = st.radio(
                "Select Option",
                page_options,
                index=default_index,
                label_visibility="collapsed",
                key="portfolio_tracker_page_radio"
            )
            
            if page != current_page:
                st.session_state["selected_page"] = page
                st.experimental_set_query_params(
                    category=st.session_state["selected_category"],
                    page=page
                )
    
    # Workout Tracker sidebar
    if st.session_state["selected_category"] == "Workout Tracker":
        with st.sidebar:
            st.markdown("### 💪 Workout Tracker")
            st.markdown("---")
            current_page = st.session_state.get("selected_page", "Log Workout")
            page_options = ["Log Workout", "Workout History", "Exercises", "Workouts", "Progress", "Analytics"]
            default_index = page_options.index(current_page) if current_page in page_options else 0
            
            page = st.radio(
                "Select Option",
                page_options,
                index=default_index,
                label_visibility="collapsed",
                key="workout_tracker_page_radio"
            )
            
            if page != current_page:
                st.session_state["selected_page"] = page
                st.experimental_set_query_params(
                    category=st.session_state["selected_category"],
                    page=page
                )
    
    # Main content routing - use persisted page from session state
    current_page = st.session_state.get("selected_page", page)
    if st.session_state["selected_category"] == "Media Tracker":
        if current_page == "Movies":
            movies_page()
        elif current_page == "TV Shows":
            tv_shows_page()
        elif current_page == "Books":
            books_page()
        elif current_page == "Music":
            music_page()
        elif current_page == "Manual Entry":
            manual_entry_page()
        elif current_page == "Analytics":
            analytics_page()
    elif st.session_state["selected_category"] == "Habit Tracker":
        if current_page == "Log Habits":
            log_habits_tab()
        elif current_page == "Calendar":
            calendar_tab()
        elif current_page == "Analytics":
            habit_analytics_tab()
    elif st.session_state["selected_category"] == "Workout Tracker":
        if current_page == "Log Workout":
            log_workout_page()
        elif current_page == "Workout History":
            workout_history_page()
        elif current_page == "Exercises":
            exercises_page()
        elif current_page == "Workouts":
            workout_templates_page()
        elif current_page == "Progress":
            workout_progress_page()
        elif current_page == "Analytics":
            workout_analytics_page()
    else:  # Portfolio Tracker
        if current_page == "Overview":
            portfolio_overview_page()
        elif current_page == "Asset Allocation":
            portfolio_allocation_page()
        elif current_page == "Transactions":
            portfolio_transactions_page()
        elif current_page == "Upload Data":
            portfolio_upload_page()
        elif current_page == "Individual Holdings":
            portfolio_individual_holdings_page()


def movies_page():
    """Movies tracking page"""
    st.title("🎬 Movies")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["View Movies", "Add Movie"])
    
    with tab1:
        st.subheader("Your Movies")
        # Get persisted year filter from query params
        # Reverse the range so newer years appear first
        current_year = date.today().year
        year_options = [f"All ({current_year})"] + list(reversed(range(2020, current_year + 2)))
        persisted_year = get_filter_from_query_params("movie_year", f"All ({current_year})")
        
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
        if "movie_year_selected" not in st.session_state:
            st.session_state["movie_year_selected"] = persisted_year
        
        default_index = year_options.index(st.session_state["movie_year_selected"]) if st.session_state["movie_year_selected"] in year_options else 0
        
        # Make dropdown smaller using column layout
        col1, col2, col3 = st.columns([1, 2, 2])
        with col1:
            year_filter = st.selectbox("Filter by Year", year_options, index=default_index, key="movie_year_filter_widget")
        
        # Update session state and query params when selection changes
        if year_filter != st.session_state["movie_year_selected"]:
            st.session_state["movie_year_selected"] = year_filter
            update_query_params(movie_year=year_filter)
            st.rerun()
        
        # Use the session state value for filtering
        year_filter = st.session_state["movie_year_selected"]
        
        try:
            params = {}
            # Check if year_filter is not "All (YYYY)" format
            if not str(year_filter).startswith("All"):
                params["year"] = year_filter
            
            response = make_authenticated_request("GET", "/movies/", params=params)
            if response.status_code == 200:
                movies = response.json()
                
                if movies:
                    # Display movies in grid layout
                    st.markdown("### Your Movies")
                    cols_per_row = 4
                    
                    for i in range(0, len(movies), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, movie in enumerate(movies[i:i+cols_per_row]):
                            with cols[j]:
                                thumbnail_url = movie.get("thumbnail_url")
                                
                                # Display thumbnail
                                image_displayed = False
                                if thumbnail_url and thumbnail_url.strip() and thumbnail_url != "N/A":
                                    if thumbnail_url.startswith("http://") or thumbnail_url.startswith("https://"):
                                        try:
                                            st.markdown(
                                                f'<img src="{thumbnail_url}" style="width:100%;height:auto;border-radius:8px;display:block;margin-bottom:10px;max-height:350px;object-fit:contain;">', 
                                                unsafe_allow_html=True
                                            )
                                            image_displayed = True
                                        except:
                                            pass
                                        
                                        if not image_displayed:
                                            try:
                                                st.image(thumbnail_url, use_container_width=True)
                                                image_displayed = True
                                            except:
                                                pass
                                    elif thumbnail_url.startswith("data:"):
                                        # Handle base64 data URLs
                                        try:
                                            st.markdown(
                                                f'<img src="{thumbnail_url}" style="width:100%;height:auto;border-radius:8px;display:block;margin-bottom:10px;max-height:350px;object-fit:contain;">', 
                                                unsafe_allow_html=True
                                            )
                                            image_displayed = True
                                        except:
                                            pass
                                
                                if not image_displayed:
                                    st.markdown(
                                        f'<div style="width:100%;height:250px;background:#f0f0f0;display:flex;align-items:center;justify-content:center;border-radius:8px;font-size:48px;margin-bottom:10px;">🎬</div>', 
                                        unsafe_allow_html=True
                                    )
                                
                                # Show title
                                st.write(f"**{movie['title']}**")
                                
                                # Show year
                                if movie.get('year'):
                                    st.caption(f"Year: {movie['year']}")
                                
                                # Show watched date
                                st.caption(f"Watched: {movie['watched_date']}")
                                
                                # Show rating
                                rating = movie.get('rating')
                                if rating:
                                    st.caption(f"Rating: {rating}/10")
                    
                    # Details section below
                    st.markdown("---")
                    st.markdown("### Movie Details")
                    
                    for movie in movies:
                        year_str = f" ({movie.get('year')})" if movie.get('year') else ""
                        with st.expander(f"**{movie['title']}**{year_str} - {movie['watched_date']}"):
                            col1, col2, col3 = st.columns([2, 2, 1])
                            with col1:
                                st.write(f"**Watched:** {movie['watched_date']}")
                            with col2:
                                rating = movie.get('rating')
                                st.write(f"**Rating:** {rating}/10" if rating else "**Rating:** N/A")
                            with col3:
                                if st.button("Delete", key=f"delete_movie_{movie['id']}"):
                                    delete_response = make_authenticated_request("DELETE", f"/movies/{movie['id']}")
                                    if delete_response.status_code == 204:
                                        st.success("Movie deleted!")
                                        st.rerun()
                            
                            if movie.get('notes'):
                                st.write(f"**Notes:** {movie['notes']}")
                else:
                    st.info("No movies found. Add your first movie in the 'Add Movie' tab!")
            else:
                st.error("Failed to load movies")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API. Make sure the backend is running.")
    
    with tab2:
        st.subheader("Add New Movie")
        
        # Search functionality
        search_query = st.text_input("🔍 Search for a movie", key="movie_search", placeholder="Type movie name to search...")
        search_results = []
        selected_result = None
        
        if search_query:
            with st.spinner("Searching..."):
                search_results = search_media("movies", search_query)
                if search_results:
                    display_search_results(search_results, "movie")
        
        # Initialize form values from selected result
        default_title = ""
        default_year = date.today().year
        default_thumbnail = None
        
        # Check session state for selected result
        if "movie_selected_result" in st.session_state:
            selected_result = st.session_state["movie_selected_result"]
            default_title = selected_result.get("title", "")
            default_thumbnail = selected_result.get("thumbnail", None)
            year_str = selected_result.get("year", "")
            if year_str:
                try:
                    # Extract year from string (handle formats like "2023" or "2023-2024")
                    year_val = int(year_str.split("-")[0])
                    if 1900 <= year_val <= date.today().year + 1:
                        default_year = year_val
                except:
                    pass
        
        with st.form("add_movie_form"):
            title = st.text_input("Title *", value=default_title, placeholder="Movie title")
            year = st.number_input("Year", min_value=1900, max_value=date.today().year + 1, value=default_year)
            status = st.selectbox("Status *", ["currently_watching", "want_to_watch", "watched", "dropped"], index=2, key="movie_status", help="Current watching status")
            watched_date = st.date_input("Watched Date", value=None, key="movie_date", help="Optional: Date when you watched")
            rating = st.slider("Rating (0-10)", 0.0, 10.0, 5.0, 0.5)
            notes = st.text_area("Notes", placeholder="Optional notes about the movie")
            
            submit = st.form_submit_button("Add Movie")
            
            if submit:
                if not title:
                    st.error("Title is required!")
                else:
                    data = {
                        "title": title,
                        "year": int(year) if year else None,
                        "status": status,
                        "watched_date": str(watched_date) if watched_date else None,
                        "rating": float(rating) if rating else None,
                        "notes": notes if notes else None,
                        "thumbnail_url": default_thumbnail if default_thumbnail and default_thumbnail.strip() else None
                    }
                    try:
                        response = make_authenticated_request("POST", "/movies/", json=data)
                        if response.status_code == 201:
                            if "movie_selected_result" in st.session_state:
                                del st.session_state["movie_selected_result"]
                            st.success("Movie added successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to add movie: {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to API. Make sure the backend is running.")


def tv_shows_page():
    """TV Shows tracking page - Plex-style with show and season posters"""
    st.title("📺 TV Shows")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["View TV Shows", "Add TV Show"])
    
    with tab1:
        st.subheader("Your TV Shows")
        # Get persisted year filter from query params
        # Reverse the range so newer years appear first
        current_year = date.today().year
        year_options = [f"All ({current_year})"] + list(reversed(range(2020, current_year + 2)))
        persisted_year = get_filter_from_query_params("tv_year", f"All ({current_year})")
        
        # Normalize persisted_year to match year_options format
        # Convert to same type as year_options items for proper comparison
        if persisted_year == "All" or str(persisted_year).startswith("All ("):
            persisted_year = f"All ({current_year})"
        elif isinstance(persisted_year, (int, str)):
            # Try to convert to int and check if it's in year_options
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
        if "tv_year_selected" not in st.session_state:
            st.session_state["tv_year_selected"] = persisted_year
        
        default_index = year_options.index(st.session_state["tv_year_selected"]) if st.session_state["tv_year_selected"] in year_options else 0
        
        # Make dropdown smaller using column layout
        col1, col2, col3 = st.columns([1, 2, 2])
        with col1:
            year_filter = st.selectbox("Filter by Year", year_options, index=default_index, key="tv_year_filter_widget")
        
        # Update session state and query params when selection changes
        if year_filter != st.session_state["tv_year_selected"]:
            st.session_state["tv_year_selected"] = year_filter
            update_query_params(tv_year=year_filter)
            st.rerun()
        
        # Use the session state value for filtering
        year_filter = st.session_state["tv_year_selected"]
        
        try:
            params = {}
            # Check if year_filter is not "All (YYYY)" format
            if not str(year_filter).startswith("All"):
                params["year"] = year_filter
            
            response = make_authenticated_request("GET", "/tv-shows/", params=params)
            if response.status_code == 200:
                tv_shows = response.json()
                
                if tv_shows:
                    # Separate currently watching shows from all shows
                    currently_watching = [show for show in tv_shows if show.get('status') == 'currently_watching']
                    all_shows = tv_shows
                    
                    # Display Currently Watching section if there are any
                    if currently_watching:
                        st.markdown("### 📺 Currently Watching")
                        cols_per_row = 4
                        
                        for i in range(0, len(currently_watching), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j, show in enumerate(currently_watching[i:i+cols_per_row]):
                                with cols[j]:
                                    # Display show poster
                                    show_poster = show.get("show_thumbnail_url")
                                    image_displayed = False
                                    
                                    if show_poster and show_poster.strip() and show_poster != "N/A":
                                        if show_poster.startswith("http://") or show_poster.startswith("https://"):
                                            try:
                                                st.markdown(
                                                    f'<img src="{show_poster}" style="width:100%;height:auto;border-radius:8px;display:block;margin-bottom:10px;max-height:350px;object-fit:contain;">', 
                                                    unsafe_allow_html=True
                                                )
                                                image_displayed = True
                                            except:
                                                pass
                                            
                                            if not image_displayed:
                                                try:
                                                    st.image(show_poster, use_container_width=True)
                                                    image_displayed = True
                                                except:
                                                    pass
                                        elif show_poster.startswith("data:"):
                                            try:
                                                st.markdown(
                                                    f'<img src="{show_poster}" style="width:100%;height:auto;border-radius:8px;display:block;margin-bottom:10px;max-height:350px;object-fit:contain;">', 
                                                    unsafe_allow_html=True
                                                )
                                                image_displayed = True
                                            except:
                                                pass
                                    
                                    if not image_displayed:
                                        st.markdown(
                                            f'<div style="width:100%;height:250px;background:#f0f0f0;display:flex;align-items:center;justify-content:center;border-radius:8px;font-size:48px;margin-bottom:10px;">📺</div>', 
                                            unsafe_allow_html=True
                                        )
                                    
                                    # Show title
                                    st.write(f"**{show['title']}**")
                                    
                                    # Show year and genres
                                    if show.get('year'):
                                        st.caption(f"Year: {show['year']}")
                                    if show.get('genres'):
                                        st.caption(f"Genres: {show['genres']}")
                                    
                                    # Count seasons
                                    season_count = len(show.get('seasons', []))
                                    if season_count == 1:
                                        st.caption(f"1 season")
                                    elif season_count > 1:
                                        st.caption(f"{season_count} seasons")
                                    
                                    # Show overall rating
                                    overall_rating = show.get('overall_rating')
                                    if overall_rating:
                                        st.caption(f"Rating: {overall_rating}/10")
                        
                        st.markdown("---")
                    
                    # Display all TV shows in grid layout with show posters
                    st.markdown("### All TV Shows")
                    cols_per_row = 4
                    
                    for i in range(0, len(tv_shows), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, show in enumerate(tv_shows[i:i+cols_per_row]):
                            with cols[j]:
                                # Display show poster
                                show_poster = show.get("show_thumbnail_url")
                                image_displayed = False
                                
                                if show_poster and show_poster.strip() and show_poster != "N/A":
                                    if show_poster.startswith("http://") or show_poster.startswith("https://"):
                                        try:
                                            st.markdown(
                                                f'<img src="{show_poster}" style="width:100%;height:auto;border-radius:8px;display:block;margin-bottom:10px;max-height:350px;object-fit:contain;">', 
                                                unsafe_allow_html=True
                                            )
                                            image_displayed = True
                                        except:
                                            pass
                                        
                                        if not image_displayed:
                                            try:
                                                st.image(show_poster, use_container_width=True)
                                                image_displayed = True
                                            except:
                                                pass
                                    elif show_poster.startswith("data:"):
                                        try:
                                            st.markdown(
                                                f'<img src="{show_poster}" style="width:100%;height:auto;border-radius:8px;display:block;margin-bottom:10px;max-height:350px;object-fit:contain;">', 
                                                unsafe_allow_html=True
                                            )
                                            image_displayed = True
                                        except:
                                            pass
                                
                                if not image_displayed:
                                    st.markdown(
                                        f'<div style="width:100%;height:250px;background:#f0f0f0;display:flex;align-items:center;justify-content:center;border-radius:8px;font-size:48px;margin-bottom:10px;">📺</div>', 
                                        unsafe_allow_html=True
                                    )
                                
                                # Show title
                                st.write(f"**{show['title']}**")
                                
                                # Show year and genres
                                if show.get('year'):
                                    st.caption(f"Year: {show['year']}")
                                if show.get('genres'):
                                    st.caption(f"Genres: {show['genres']}")
                                
                                # Count seasons
                                season_count = len(show.get('seasons', []))
                                if season_count == 1:
                                    st.caption(f"1 season")
                                elif season_count > 1:
                                    st.caption(f"{season_count} seasons")
                                
                                # Show overall rating
                                overall_rating = show.get('overall_rating')
                                if overall_rating:
                                    st.caption(f"Rating: {overall_rating}/10")
                    
                    # Details section below - Plex-style with seasons grouped by year
                    st.markdown("---")
                    st.markdown("### Show & Season Details")
                    
                    for show in tv_shows:
                        seasons = show.get('seasons', [])
                        show_year = show.get('year', '')
                        year_str = f" ({show_year})" if show_year else ""
                        
                        with st.expander(f"**{show['title']}**{year_str}"):
                            # Show-level information
                            col1, col2, col3 = st.columns([2, 2, 1])
                            with col1:
                                if show.get('genres'):
                                    st.write(f"**Genres:** {show['genres']}")
                            with col2:
                                overall_rating = show.get('overall_rating')
                                if overall_rating:
                                    st.write(f"**Overall Rating:** {overall_rating}/10")
                            with col3:
                                if st.button("Delete Show", key=f"delete_show_{show['id']}"):
                                    delete_response = make_authenticated_request("DELETE", f"/tv-shows/{show['id']}")
                                    if delete_response.status_code == 204:
                                        st.success("Show deleted!")
                                        st.rerun()
                            
                            if seasons:
                                st.markdown("---")
                                st.markdown("#### Seasons")
                                
                                # Group seasons by year (from watched_date)
                                seasons_by_year = defaultdict(list)
                                for season in seasons:
                                    watched_date = season.get('watched_date', '')
                                    if watched_date:
                                        year = str(watched_date).split('-')[0]
                                        seasons_by_year[year].append(season)
                                    else:
                                        seasons_by_year['Unknown'].append(season)
                                
                                # Display seasons grouped by year
                                for year in sorted(seasons_by_year.keys(), reverse=True):
                                    year_seasons = sorted(seasons_by_year[year], key=lambda x: x.get('season_number', 0))
                                    
                                    st.markdown(f"**{year}**")
                                    
                                    # Display season posters in a grid
                                    cols_per_row_seasons = 6
                                    for i in range(0, len(year_seasons), cols_per_row_seasons):
                                        cols = st.columns(cols_per_row_seasons)
                                        for j, season in enumerate(year_seasons[i:i+cols_per_row_seasons]):
                                            with cols[j]:
                                                # Display season poster
                                                season_poster = season.get("season_thumbnail_url")
                                                image_displayed = False
                                                
                                                if season_poster and season_poster.strip() and season_poster != "N/A":
                                                    if season_poster.startswith("http://") or season_poster.startswith("https://"):
                                                        try:
                                                            st.markdown(
                                                                f'<img src="{season_poster}" style="width:100%;height:auto;border-radius:8px;display:block;margin-bottom:5px;max-height:150px;object-fit:contain;">', 
                                                                unsafe_allow_html=True
                                                            )
                                                            image_displayed = True
                                                        except:
                                                            pass
                                                    elif season_poster.startswith("data:"):
                                                        try:
                                                            st.markdown(
                                                                f'<img src="{season_poster}" style="width:100%;height:auto;border-radius:8px;display:block;margin-bottom:5px;max-height:150px;object-fit:contain;">', 
                                                                unsafe_allow_html=True
                                                            )
                                                            image_displayed = True
                                                        except:
                                                            pass
                                                
                                                if not image_displayed:
                                                    st.markdown(
                                                        f'<div style="width:100%;height:100px;background:#f0f0f0;display:flex;align-items:center;justify-content:center;border-radius:8px;font-size:24px;margin-bottom:5px;">S{season.get("season_number", "?")}</div>', 
                                                        unsafe_allow_html=True
                                                    )
                                                
                                                # Season info
                                                st.caption(f"**S{season.get('season_number', '?')}**")
                                                st.caption(f"{season.get('watched_date', 'N/A')}")
                                                rating = season.get('rating')
                                                if rating:
                                                    st.caption(f"⭐ {rating}/10")
                                                
                                                # Delete button for season
                                                if st.button("×", key=f"delete_season_{season['id']}", help="Delete this season"):
                                                    delete_response = make_authenticated_request("DELETE", f"/tv-shows/seasons/{season['id']}")
                                                    if delete_response.status_code == 204:
                                                        st.success("Season deleted!")
                                                        st.rerun()
                                                
                                                # Show notes if any
                                                if season.get('notes'):
                                                    with st.expander("Notes"):
                                                        st.caption(season['notes'])
                                    
                                    st.markdown("")  # Add spacing between years
                            else:
                                st.info("No seasons tracked yet for this show.")
                else:
                    st.info("No TV shows found. Add your first TV show in the 'Add TV Show' tab!")
            else:
                st.error("Failed to load TV shows")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API. Make sure the backend is running.")
    
    with tab2:
        st.subheader("Add New TV Show")
        
        # Search functionality
        search_query = st.text_input("🔍 Search for a TV show", key="tv_search", placeholder="Type TV show name to search...")
        search_results = []
        selected_result = None
        
        if search_query:
            with st.spinner("Searching..."):
                search_results = search_media("tv-shows", search_query)
                if search_results:
                    display_search_results(search_results, "tv")
        
        # Check if a TV show is selected
        if "tv_selected_result" in st.session_state:
            selected_result = st.session_state["tv_selected_result"]
            tvmaze_id = selected_result.get("tvmaze_id")
            
            if tvmaze_id:
                # Fetch seasons for the selected TV show
                if "tv_seasons" not in st.session_state or st.session_state.get("tv_selected_tvmaze_id") != tvmaze_id:
                    with st.spinner("Loading seasons..."):
                        seasons = get_tv_show_seasons(tvmaze_id)
                        st.session_state["tv_seasons"] = seasons
                        st.session_state["tv_selected_tvmaze_id"] = tvmaze_id
                else:
                    seasons = st.session_state.get("tv_seasons", [])
                
                # Display selected show info
                st.success(f"✅ Selected: **{selected_result.get('title', '')}**")
                if st.button("Clear Selection", key="tv_clear_selection"):
                    if "tv_selected_result" in st.session_state:
                        del st.session_state["tv_selected_result"]
                    if "tv_seasons" in st.session_state:
                        del st.session_state["tv_seasons"]
                    if "tv_selected_tvmaze_id" in st.session_state:
                        del st.session_state["tv_selected_tvmaze_id"]
                    if "tv_selected_season" in st.session_state:
                        del st.session_state["tv_selected_season"]
                    st.rerun()
                
                st.markdown("---")
                st.subheader("Select a Season")
                
                if seasons:
                    # Display seasons in a grid
                    cols_per_row = 4
                    for i in range(0, len(seasons), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, season in enumerate(seasons[i:i+cols_per_row]):
                            with cols[j]:
                                # Display season image or placeholder
                                season_image = season.get("image", "")
                                image_displayed = False
                                
                                if season_image and season_image.strip() and season_image != "N/A":
                                    # Check if it's a valid HTTP URL
                                    if season_image.startswith("http://") or season_image.startswith("https://"):
                                        # Method 1: Try HTML img tag (works better with external URLs)
                                        try:
                                            st.markdown(
                                                f'<img src="{season_image}" width="150" style="border-radius: 8px; object-fit: cover; height: 200px; display: block; margin: 0 auto;">', 
                                                unsafe_allow_html=True
                                            )
                                            image_displayed = True
                                        except:
                                            pass
                                        
                                        # Method 2: Fallback to st.image if HTML fails
                                        if not image_displayed:
                                            try:
                                                st.image(season_image, width=150, use_container_width=True)
                                                image_displayed = True
                                            except:
                                                pass
                                
                                # Method 3: Show placeholder if no image or if display failed
                                if not image_displayed:
                                    st.markdown(
                                        f'<div style="width:150px;height:200px;background:#f0f0f0;display:flex;align-items:center;justify-content:center;border-radius:8px;font-size:48px;margin: 0 auto;">📺</div>', 
                                        unsafe_allow_html=True
                                    )
                                
                                # Season number and name
                                season_num = season.get("number", 0)
                                season_name = season.get("name", f"Season {season_num}")
                                st.write(f"**{season_name}**")
                                
                                # Episode count
                                episode_count = season.get("episode_count") or 0
                                if episode_count and episode_count > 0:
                                    st.caption(f"{episode_count} episodes")
                                
                                # Select button
                                button_key = f"select_season_{season_num}"
                                if st.button("Select", key=button_key):
                                    st.session_state["tv_selected_season"] = season
                                    st.rerun()
                    
                    # Show form for selected season
                    if "tv_selected_season" in st.session_state:
                        selected_season = st.session_state["tv_selected_season"]
                        st.markdown("---")
                        st.subheader(f"Add Season {selected_season.get('number', '?')}")
                        
                        with st.form("add_tv_show_form"):
                            title = st.text_input("Title *", value=selected_result.get("title", ""), placeholder="TV Show title")
                            season = st.number_input("Season", min_value=1, value=selected_season.get("number", 1), disabled=True)
                            status = st.selectbox("Show Status *", ["currently_watching", "want_to_watch", "watched", "dropped"], index=2, key="tv_status", help="Current watching status for the show")
                            watched_date = st.date_input("Watched Date", value=None, key="tv_date", help="Optional: Date when you watched this season")
                            rating = st.slider("Rating (0-10)", 0.0, 10.0, 5.0, 0.5, key="tv_rating")
                            notes = st.text_area("Notes", placeholder="Optional notes", key="tv_notes")
                            
                            submit = st.form_submit_button("Add TV Show Season")
                            
                            if submit:
                                if not title:
                                    st.error("Title is required!")
                                else:
                                    data = {
                                        "title": title,
                                        "season": int(season) if season else None,
                                        "status": status,
                                        "watched_date": str(watched_date) if watched_date else None,
                                        "rating": float(rating) if rating else None,
                                        "notes": notes if notes else None,
                                        "thumbnail_url": selected_season.get("image", "") if selected_season.get("image") else None
                                    }
                                    try:
                                        response = make_authenticated_request("POST", "/tv-shows/legacy", json=data)
                                        if response.status_code == 201:
                                            # Clear all TV show related session state
                                            if "tv_selected_result" in st.session_state:
                                                del st.session_state["tv_selected_result"]
                                            if "tv_seasons" in st.session_state:
                                                del st.session_state["tv_seasons"]
                                            if "tv_selected_tvmaze_id" in st.session_state:
                                                del st.session_state["tv_selected_tvmaze_id"]
                                            if "tv_selected_season" in st.session_state:
                                                del st.session_state["tv_selected_season"]
                                            st.success("TV Show Season added successfully!")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to add TV show: {response.text}")
                                    except requests.exceptions.ConnectionError:
                                        st.error("Cannot connect to API. Make sure the backend is running.")
                else:
                    st.info("No seasons found for this TV show.")
            else:
                # Fallback to old form if no tvmaze_id
                default_title = selected_result.get("title", "")
                with st.form("add_tv_show_form_fallback"):
                    title = st.text_input("Title *", value=default_title, placeholder="TV Show title")
                    season = st.number_input("Season", min_value=1, value=1)
                    status = st.selectbox("Show Status *", ["currently_watching", "want_to_watch", "watched", "dropped"], index=2, key="tv_status_fallback", help="Current watching status for the show")
                    watched_date = st.date_input("Watched Date", value=None, key="tv_date_fallback", help="Optional: Date when you watched this season")
                    rating = st.slider("Rating (0-10)", 0.0, 10.0, 5.0, 0.5, key="tv_rating_fallback")
                    notes = st.text_area("Notes", placeholder="Optional notes", key="tv_notes_fallback")
                    
                    submit = st.form_submit_button("Add TV Show Season")
                    
                    if submit:
                        if not title:
                            st.error("Title is required!")
                        else:
                            data = {
                                "title": title,
                                "season": int(season) if season else None,
                                "status": status,
                                "watched_date": str(watched_date) if watched_date else None,
                                "rating": float(rating) if rating else None,
                                "notes": notes if notes else None
                            }
                            try:
                                response = make_authenticated_request("POST", "/tv-shows/legacy", json=data)
                                if response.status_code == 201:
                                    if "tv_selected_result" in st.session_state:
                                        del st.session_state["tv_selected_result"]
                                    st.success("TV Show Season added successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to add TV show: {response.text}")
                            except requests.exceptions.ConnectionError:
                                st.error("Cannot connect to API. Make sure the backend is running.")
        else:
            # No selection - show manual form
            with st.form("add_tv_show_form"):
                title = st.text_input("Title *", placeholder="TV Show title")
                season = st.number_input("Season", min_value=1, value=1)
                status = st.selectbox("Show Status *", ["currently_watching", "want_to_watch", "watched", "dropped"], index=2, key="tv_status_manual", help="Current watching status for the show")
                watched_date = st.date_input("Watched Date", value=None, key="tv_date_manual", help="Optional: Date when you watched this season")
                rating = st.slider("Rating (0-10)", 0.0, 10.0, 5.0, 0.5, key="tv_rating_manual")
                notes = st.text_area("Notes", placeholder="Optional notes", key="tv_notes_manual")
                
                submit = st.form_submit_button("Add TV Show Season")
                
                if submit:
                    if not title:
                        st.error("Title is required!")
                    else:
                        data = {
                            "title": title,
                            "season": int(season) if season else None,
                            "status": status,
                            "watched_date": str(watched_date) if watched_date else None,
                            "rating": float(rating) if rating else None,
                            "notes": notes if notes else None
                        }
                        try:
                            response = make_authenticated_request("POST", "/tv-shows/legacy", json=data)
                            if response.status_code == 201:
                                st.success("TV Show Season added successfully!")
                                st.rerun()
                            else:
                                st.error(f"Failed to add TV show: {response.text}")
                        except requests.exceptions.ConnectionError:
                            st.error("Cannot connect to API. Make sure the backend is running.")


def books_page():
    """Books tracking page"""
    st.title("📖 Books")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["View Books", "Add Book"])
    
    with tab1:
        st.subheader("Your Books")
        # Get persisted year filter from query params
        # Reverse the range so newer years appear first
        current_year = date.today().year
        year_options = [f"All ({current_year})"] + list(reversed(range(2020, current_year + 2)))
        persisted_year = get_filter_from_query_params("book_year", f"All ({current_year})")
        
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
        if "book_year_selected" not in st.session_state:
            st.session_state["book_year_selected"] = persisted_year
        
        default_index = year_options.index(st.session_state["book_year_selected"]) if st.session_state["book_year_selected"] in year_options else 0
        
        # Make dropdown smaller using column layout
        col1, col2, col3 = st.columns([1, 2, 2])
        with col1:
            year_filter = st.selectbox("Filter by Year", year_options, index=default_index, key="book_year_filter_widget")
        
        # Update session state and query params when selection changes
        if year_filter != st.session_state["book_year_selected"]:
            st.session_state["book_year_selected"] = year_filter
            update_query_params(book_year=year_filter)
            st.rerun()
        
        # Use the session state value for filtering
        year_filter = st.session_state["book_year_selected"]
        
        try:
            params = {}
            # Check if year_filter is not "All (YYYY)" format
            if not str(year_filter).startswith("All"):
                params["year"] = year_filter
            
            response = make_authenticated_request("GET", "/books/", params=params)
            if response.status_code == 200:
                books = response.json()
                
                if books:
                    # Separate currently reading books from all books
                    currently_reading = [book for book in books if book.get('status') == 'currently_reading']
                    all_books = books
                    
                    # Display Currently Reading section if there are any
                    if currently_reading:
                        st.markdown("### 📖 Currently Reading")
                        cols_per_row = 4
                        
                        for i in range(0, len(currently_reading), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j, book in enumerate(currently_reading[i:i+cols_per_row]):
                                with cols[j]:
                                    thumbnail_url = book.get("thumbnail_url")
                                    
                                    # Display thumbnail
                                    image_displayed = False
                                    if thumbnail_url and thumbnail_url.strip() and thumbnail_url != "N/A":
                                        if thumbnail_url.startswith("http://") or thumbnail_url.startswith("https://"):
                                            try:
                                                st.markdown(
                                                    f'<img src="{thumbnail_url}" style="width:100%;height:auto;border-radius:8px;display:block;margin-bottom:10px;max-height:350px;object-fit:contain;">', 
                                                    unsafe_allow_html=True
                                                )
                                                image_displayed = True
                                            except:
                                                pass
                                            
                                            if not image_displayed:
                                                try:
                                                    st.image(thumbnail_url, use_container_width=True)
                                                    image_displayed = True
                                                except:
                                                    pass
                                        elif thumbnail_url.startswith("data:"):
                                            # Handle base64 data URLs
                                            try:
                                                st.markdown(
                                                    f'<img src="{thumbnail_url}" style="width:100%;height:auto;border-radius:8px;display:block;margin-bottom:10px;max-height:350px;object-fit:contain;">', 
                                                    unsafe_allow_html=True
                                                )
                                                image_displayed = True
                                            except:
                                                pass
                                    
                                    if not image_displayed:
                                        st.markdown(
                                            f'<div style="width:100%;height:250px;background:#f0f0f0;display:flex;align-items:center;justify-content:center;border-radius:8px;font-size:48px;margin-bottom:10px;">📖</div>', 
                                            unsafe_allow_html=True
                                        )
                                    
                                    # Show title
                                    st.write(f"**{book['title']}**")
                                    
                                    # Show author
                                    if book.get('author'):
                                        st.caption(f"by {book['author']}")
                                    
                                    # Show pages
                                    if book.get('pages'):
                                        st.caption(f"Pages: {book['pages']}")
                                    
                                    # Show finished date if available
                                    if book.get('finished_date'):
                                        st.caption(f"Finished: {book['finished_date']}")
                                    
                                    # Show rating
                                    rating = book.get('rating')
                                    if rating:
                                        st.caption(f"Rating: {rating}/10")
                        
                        st.markdown("---")
                    
                    # Display all books in grid layout
                    st.markdown("### All Books")
                    cols_per_row = 4
                    
                    for i in range(0, len(books), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, book in enumerate(books[i:i+cols_per_row]):
                            with cols[j]:
                                thumbnail_url = book.get("thumbnail_url")
                                
                                # Display thumbnail
                                image_displayed = False
                                if thumbnail_url and thumbnail_url.strip() and thumbnail_url != "N/A":
                                    if thumbnail_url.startswith("http://") or thumbnail_url.startswith("https://"):
                                        try:
                                            st.markdown(
                                                f'<img src="{thumbnail_url}" style="width:100%;height:auto;border-radius:8px;display:block;margin-bottom:10px;max-height:350px;object-fit:contain;">', 
                                                unsafe_allow_html=True
                                            )
                                            image_displayed = True
                                        except:
                                            pass
                                        
                                        if not image_displayed:
                                            try:
                                                st.image(thumbnail_url, use_container_width=True)
                                                image_displayed = True
                                            except:
                                                pass
                                    elif thumbnail_url.startswith("data:"):
                                        # Handle base64 data URLs
                                        try:
                                            st.markdown(
                                                f'<img src="{thumbnail_url}" style="width:100%;height:auto;border-radius:8px;display:block;margin-bottom:10px;max-height:350px;object-fit:contain;">', 
                                                unsafe_allow_html=True
                                            )
                                            image_displayed = True
                                        except:
                                            pass
                                
                                if not image_displayed:
                                    st.markdown(
                                        f'<div style="width:100%;height:250px;background:#f0f0f0;display:flex;align-items:center;justify-content:center;border-radius:8px;font-size:48px;margin-bottom:10px;">📖</div>', 
                                        unsafe_allow_html=True
                                    )
                                
                                # Show title
                                st.write(f"**{book['title']}**")
                                
                                # Show author
                                if book.get('author'):
                                    st.caption(f"by {book['author']}")
                                
                                # Show pages
                                if book.get('pages'):
                                    st.caption(f"Pages: {book['pages']}")
                                
                                # Show finished date
                                st.caption(f"Finished: {book['finished_date']}")
                                
                                # Show rating
                                rating = book.get('rating')
                                if rating:
                                    st.caption(f"Rating: {rating}/10")
                    
                    # Details section below
                    st.markdown("---")
                    st.markdown("### Book Details")
                    
                    for book in books:
                        author_str = f" by {book.get('author')}" if book.get('author') else ""
                        with st.expander(f"**{book['title']}**{author_str} - {book['finished_date']}"):
                            col1, col2, col3 = st.columns([2, 2, 1])
                            with col1:
                                st.write(f"**Finished:** {book['finished_date']}")
                                if book.get('pages'):
                                    st.write(f"**Pages:** {book['pages']}")
                            with col2:
                                rating = book.get('rating')
                                st.write(f"**Rating:** {rating}/10" if rating else "**Rating:** N/A")
                            with col3:
                                if st.button("Delete", key=f"delete_book_{book['id']}"):
                                    delete_response = make_authenticated_request("DELETE", f"/books/{book['id']}")
                                    if delete_response.status_code == 204:
                                        st.success("Book deleted!")
                                        st.rerun()
                            
                            if book.get('notes'):
                                st.write(f"**Notes:** {book['notes']}")
                else:
                    st.info("No books found. Add your first book in the 'Add Book' tab!")
            else:
                st.error("Failed to load books")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API. Make sure the backend is running.")
    
    with tab2:
        st.subheader("Add New Book")
        
        # Search functionality
        search_query = st.text_input("🔍 Search for a book", key="book_search", placeholder="Type book name to search...")
        search_results = []
        selected_result = None
        
        if search_query:
            with st.spinner("Searching..."):
                search_results = search_media("books", search_query)
                if search_results:
                    display_search_results(search_results, "book")
        
        # Initialize form values from selected result
        default_title = ""
        default_author = ""
        default_thumbnail = None
        if "book_selected_result" in st.session_state:
            selected_result = st.session_state["book_selected_result"]
            default_title = selected_result.get("title", "")
            default_author = selected_result.get("author", "")
            default_thumbnail = selected_result.get("thumbnail", None)
        
        with st.form("add_book_form"):
            title = st.text_input("Title *", value=default_title, placeholder="Book title")
            author = st.text_input("Author", value=default_author, placeholder="Author name")
            pages = st.number_input("Number of Pages", min_value=1, value=None, step=1, key="book_pages", help="Optional: Enter the total number of pages")
            status = st.selectbox("Status *", ["currently_reading", "want_to_read", "finished", "dropped"], index=2, key="book_status", help="Current reading status")
            finished_date = st.date_input("Finished Date", value=None, key="book_date", help="Optional: Date when you finished reading")
            rating = st.slider("Rating (0-10)", 0.0, 10.0, 5.0, 0.5, key="book_rating")
            notes = st.text_area("Notes", placeholder="Optional notes", key="book_notes")
            
            submit = st.form_submit_button("Add Book")
            
            if submit:
                if not title:
                    st.error("Title is required!")
                else:
                    data = {
                        "title": title,
                        "author": author if author else None,
                        "pages": int(pages) if pages else None,
                        "status": status,
                        "finished_date": str(finished_date) if finished_date else None,
                        "rating": float(rating) if rating else None,
                        "notes": notes if notes else None,
                        "thumbnail_url": default_thumbnail if default_thumbnail and default_thumbnail.strip() else None
                    }
                    try:
                        response = make_authenticated_request("POST", "/books/", json=data)
                        if response.status_code == 201:
                            if "book_selected_result" in st.session_state:
                                del st.session_state["book_selected_result"]
                            st.success("Book added successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to add book: {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to API. Make sure the backend is running.")


def music_page():
    """Music tracking page"""
    st.title("🎵 Music")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["View Music", "Add Music"])
    
    with tab1:
        st.subheader("Your Music")
        # Get persisted year filter from query params
        # Reverse the range so newer years appear first
        current_year = date.today().year
        year_options = [f"All ({current_year})"] + list(reversed(range(2020, current_year + 2)))
        persisted_year = get_filter_from_query_params("music_year", f"All ({current_year})")
        
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
        if "music_year_selected" not in st.session_state:
            st.session_state["music_year_selected"] = persisted_year
        
        default_index = year_options.index(st.session_state["music_year_selected"]) if st.session_state["music_year_selected"] in year_options else 0
        
        # Make dropdown smaller using column layout
        col1, col2, col3 = st.columns([1, 2, 2])
        with col1:
            year_filter = st.selectbox("Filter by Year", year_options, index=default_index, key="music_year_filter_widget")
        
        # Update session state and query params when selection changes
        if year_filter != st.session_state["music_year_selected"]:
            st.session_state["music_year_selected"] = year_filter
            update_query_params(music_year=year_filter)
            st.rerun()
        
        # Use the session state value for filtering
        year_filter = st.session_state["music_year_selected"]
        
        try:
            params = {}
            # Check if year_filter is not "All (YYYY)" format
            if not str(year_filter).startswith("All"):
                params["year"] = year_filter
            
            response = make_authenticated_request("GET", "/music/", params=params)
            if response.status_code == 200:
                music_list = response.json()
                
                if music_list:
                    # Display music in grid layout
                    st.markdown("### Your Music")
                    cols_per_row = 4
                    
                    for i in range(0, len(music_list), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, music in enumerate(music_list[i:i+cols_per_row]):
                            with cols[j]:
                                thumbnail_url = music.get("thumbnail_url")
                                
                                # Display thumbnail
                                image_displayed = False
                                if thumbnail_url and thumbnail_url.strip() and thumbnail_url != "N/A":
                                    if thumbnail_url.startswith("http://") or thumbnail_url.startswith("https://"):
                                        try:
                                            st.markdown(
                                                f'<img src="{thumbnail_url}" style="width:100%;height:auto;border-radius:8px;display:block;margin-bottom:10px;max-height:350px;object-fit:contain;">', 
                                                unsafe_allow_html=True
                                            )
                                            image_displayed = True
                                        except:
                                            pass
                                        
                                        if not image_displayed:
                                            try:
                                                st.image(thumbnail_url, use_container_width=True)
                                                image_displayed = True
                                            except:
                                                pass
                                    elif thumbnail_url.startswith("data:"):
                                        # Handle base64 data URLs
                                        try:
                                            st.markdown(
                                                f'<img src="{thumbnail_url}" style="width:100%;height:auto;border-radius:8px;display:block;margin-bottom:10px;max-height:350px;object-fit:contain;">', 
                                                unsafe_allow_html=True
                                            )
                                            image_displayed = True
                                        except:
                                            pass
                                
                                if not image_displayed:
                                    st.markdown(
                                        f'<div style="width:100%;height:250px;background:#f0f0f0;display:flex;align-items:center;justify-content:center;border-radius:8px;font-size:48px;margin-bottom:10px;">🎵</div>', 
                                        unsafe_allow_html=True
                                    )
                                
                                # Show title
                                st.write(f"**{music['title']}**")
                                
                                # Show artist
                                if music.get('artist'):
                                    st.caption(f"by {music['artist']}")
                                
                                # Show album
                                if music.get('album'):
                                    st.caption(f"Album: {music['album']}")
                                
                                # Show listened date
                                st.caption(f"Listened: {music['listened_date']}")
                                
                                # Show rating
                                rating = music.get('rating')
                                if rating:
                                    st.caption(f"Rating: {rating}/10")
                    
                    # Details section below
                    st.markdown("---")
                    st.markdown("### Music Details")
                    
                    for music in music_list:
                        artist_str = f" by {music.get('artist')}" if music.get('artist') else ""
                        album_str = f" ({music.get('album')})" if music.get('album') else ""
                        with st.expander(f"**{music['title']}**{artist_str}{album_str} - {music['listened_date']}"):
                            col1, col2, col3 = st.columns([2, 2, 1])
                            with col1:
                                st.write(f"**Listened:** {music['listened_date']}")
                            with col2:
                                rating = music.get('rating')
                                st.write(f"**Rating:** {rating}/10" if rating else "**Rating:** N/A")
                            with col3:
                                if st.button("Delete", key=f"delete_music_{music['id']}"):
                                    delete_response = make_authenticated_request("DELETE", f"/music/{music['id']}")
                                    if delete_response.status_code == 204:
                                        st.success("Music entry deleted!")
                                        st.rerun()
                            
                            if music.get('notes'):
                                st.write(f"**Notes:** {music['notes']}")
                else:
                    st.info("No music entries found. Add your first music entry in the 'Add Music' tab!")
            else:
                st.error("Failed to load music")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API. Make sure the backend is running.")
    
    with tab2:
        st.subheader("Add New Music Entry")
        
        # Search functionality
        search_query = st.text_input("🔍 Search for music", key="music_search", placeholder="Type song/album/artist name to search...")
        search_results = []
        selected_result = None
        
        if search_query:
            with st.spinner("Searching..."):
                search_results = search_media("music", search_query)
                if search_results:
                    display_search_results(search_results, "music")
        
        # Initialize form values from selected result
        default_title = ""
        default_artist = ""
        default_thumbnail = None
        if "music_selected_result" in st.session_state:
            selected_result = st.session_state["music_selected_result"]
            default_title = selected_result.get("title", "")
            default_artist = selected_result.get("artist", "")
            default_thumbnail = selected_result.get("thumbnail", None)
        
        with st.form("add_music_form"):
            title = st.text_input("Title *", value=default_title, placeholder="Song/Album/Band name")
            artist = st.text_input("Artist/Band", value=default_artist, placeholder="Artist or band name")
            album = st.text_input("Album", placeholder="Album name (if applicable)")
            status = st.selectbox("Status *", ["currently_listening", "want_to_listen", "listened", "dropped"], index=2, key="music_status", help="Current listening status")
            listened_date = st.date_input("Listened Date", value=None, key="music_date", help="Optional: Date when you listened")
            rating = st.slider("Rating (0-10)", 0.0, 10.0, 5.0, 0.5, key="music_rating")
            notes = st.text_area("Notes", placeholder="Optional notes", key="music_notes")
            
            submit = st.form_submit_button("Add Music")
            
            if submit:
                if not title:
                    st.error("Title is required!")
                else:
                    data = {
                        "title": title,
                        "artist": artist if artist else None,
                        "album": album if album else None,
                        "status": status,
                        "listened_date": str(listened_date) if listened_date else None,
                        "rating": float(rating) if rating else None,
                        "notes": notes if notes else None,
                        "thumbnail_url": default_thumbnail if default_thumbnail and default_thumbnail.strip() else None
                    }
                    try:
                        response = make_authenticated_request("POST", "/music/", json=data)
                        if response.status_code == 201:
                            if "music_selected_result" in st.session_state:
                                del st.session_state["music_selected_result"]
                            st.success("Music entry added successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to add music: {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to API. Make sure the backend is running.")


def manual_entry_page():
    """Manual Entry page for adding media with custom metadata and thumbnails"""
    st.title("➕ Manual Entry")
    st.markdown("---")
    st.markdown("Enter media metadata manually and upload custom thumbnails")
    
    # Media type selector
    media_type = st.selectbox(
        "Select Media Type",
        ["Movie", "TV Show", "Book", "Music"],
        key="manual_entry_type"
    )
    
    st.markdown("---")
    
    # Form based on media type
    if media_type == "Movie":
        with st.form("manual_movie_form"):
            st.subheader("Movie Details")
            title = st.text_input("Title *", placeholder="Movie title")
            year = st.number_input("Year", min_value=1900, max_value=date.today().year + 1, value=date.today().year)
            status = st.selectbox("Status *", ["currently_watching", "want_to_watch", "watched", "dropped"], index=2, key="manual_movie_status", help="Current watching status")
            watched_date = st.date_input("Watched Date", value=None, key="manual_movie_date", help="Optional: Date when you watched")
            rating = st.slider("Rating (0-10)", 0.0, 10.0, 5.0, 0.5)
            notes = st.text_area("Notes", placeholder="Optional notes")
            
            st.markdown("---")
            st.subheader("Thumbnail (Optional)")
            uploaded_file = st.file_uploader(
                "Upload thumbnail image",
                type=["png", "jpg", "jpeg", "gif", "webp"],
                key="manual_movie_thumbnail"
            )
            
            thumbnail_url = None
            file_bytes = None
            if uploaded_file is not None:
                # Read file bytes once
                file_bytes = uploaded_file.read()
                # Display preview using bytes
                st.image(file_bytes, width=200, caption="Thumbnail Preview")
            
            submit = st.form_submit_button("Add Movie")
            
            if submit:
                if not title:
                    st.error("Title is required!")
                else:
                    # Convert file bytes to base64 data URL if file was uploaded
                    if file_bytes is not None:
                        file_base64 = base64.b64encode(file_bytes).decode('utf-8')
                        file_extension = uploaded_file.name.split('.')[-1].lower()
                        mime_types = {
                            'png': 'image/png',
                            'jpg': 'image/jpeg',
                            'jpeg': 'image/jpeg',
                            'gif': 'image/gif',
                            'webp': 'image/webp'
                        }
                        mime_type = mime_types.get(file_extension, 'image/jpeg')
                        thumbnail_url = f"data:{mime_type};base64,{file_base64}"
                    
                    data = {
                        "title": title,
                        "year": int(year) if year else None,
                        "status": status,
                        "watched_date": str(watched_date) if watched_date else None,
                        "rating": float(rating) if rating else None,
                        "notes": notes if notes else None,
                        "thumbnail_url": thumbnail_url
                    }
                    try:
                        response = make_authenticated_request("POST", "/movies/", json=data)
                        if response.status_code == 201:
                            st.success("Movie added successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to add movie: {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to API. Make sure the backend is running.")
    
    elif media_type == "TV Show":
        # Enhanced TV Show entry with show-level and season-level posters
        st.subheader("TV Show Details")
        st.markdown("*Enter show information first, then add season details below*")
        
        # Step 1: Show-level information
        with st.container():
            st.markdown("### Show Information")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                show_title = st.text_input("Show Title *", placeholder="e.g., Party Down", key="manual_tv_show_title")
                show_year = st.number_input("Show Year", min_value=1900, max_value=date.today().year + 1, value=date.today().year, key="manual_tv_show_year")
                show_genres = st.text_input("Genres (comma-separated)", placeholder="e.g., Comedy, Drama", key="manual_tv_genres")
                show_status = st.selectbox("Show Status *", ["currently_watching", "want_to_watch", "watched", "dropped"], index=2, key="manual_tv_show_status", help="Current watching status for the show")
                show_overall_rating = st.slider("Overall Show Rating (0-10)", 0.0, 10.0, 5.0, 0.5, key="manual_tv_overall_rating")
            
            with col2:
                st.markdown("**Show Poster**")
                show_poster_file = st.file_uploader(
                    "Upload show poster",
                    type=["png", "jpg", "jpeg", "gif", "webp"],
                    key="manual_tv_show_poster",
                    help="Main poster for the entire series"
                )
                
                show_poster_url = None
                show_poster_bytes = None
                if show_poster_file is not None:
                    show_poster_bytes = show_poster_file.read()
                    st.image(show_poster_bytes, width=150, caption="Show Poster Preview")
            
            st.markdown("---")
        
        # Step 2: Season-level information
        with st.form("manual_tv_season_form"):
            st.markdown("### Season Details")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                season_number = st.number_input("Season Number *", min_value=1, value=1, key="manual_tv_season")
                watched_date = st.date_input("Watched Date", value=None, key="manual_tv_watched_date", help="Optional: Date when you watched this season")
                season_rating = st.slider("Season Rating (0-10)", 0.0, 10.0, 5.0, 0.5, key="manual_tv_season_rating")
                season_notes = st.text_area("Season Notes", placeholder="Optional notes about this season", key="manual_tv_season_notes")
            
            with col2:
                st.markdown("**Season Poster**")
                season_poster_file = st.file_uploader(
                    "Upload season poster",
                    type=["png", "jpg", "jpeg", "gif", "webp"],
                    key="manual_tv_season_poster",
                    help="Specific poster for this season"
                )
                
                season_poster_url = None
                season_poster_bytes = None
                if season_poster_file is not None:
                    season_poster_bytes = season_poster_file.read()
                    st.image(season_poster_bytes, width=150, caption="Season Poster Preview")
            
            submit = st.form_submit_button("Add TV Show with Season")
            
            if submit:
                if not show_title:
                    st.error("Show title is required!")
                else:
                    try:
                        # Convert show poster to base64 if uploaded
                        if show_poster_bytes is not None:
                            file_base64 = base64.b64encode(show_poster_bytes).decode('utf-8')
                            file_extension = show_poster_file.name.split('.')[-1].lower()
                            mime_types = {
                                'png': 'image/png',
                                'jpg': 'image/jpeg',
                                'jpeg': 'image/jpeg',
                                'gif': 'image/gif',
                                'webp': 'image/webp'
                            }
                            mime_type = mime_types.get(file_extension, 'image/jpeg')
                            show_poster_url = f"data:{mime_type};base64,{file_base64}"
                        
                        # Convert season poster to base64 if uploaded
                        if season_poster_bytes is not None:
                            file_base64 = base64.b64encode(season_poster_bytes).decode('utf-8')
                            file_extension = season_poster_file.name.split('.')[-1].lower()
                            mime_types = {
                                'png': 'image/png',
                                'jpg': 'image/jpeg',
                                'jpeg': 'image/jpeg',
                                'gif': 'image/gif',
                                'webp': 'image/webp'
                            }
                            mime_type = mime_types.get(file_extension, 'image/jpeg')
                            season_poster_url = f"data:{mime_type};base64,{file_base64}"
                        
                        # First, check if show exists
                        shows_response = make_authenticated_request("GET", "/tv-shows/")
                        show_id = None
                        
                        if shows_response.status_code == 200:
                            shows = shows_response.json()
                            for show in shows:
                                if show['title'].lower() == show_title.lower():
                                    show_id = show['id']
                                    # Update show metadata if needed
                                    update_data = {
                                        "year": int(show_year) if show_year else None,
                                        "genres": show_genres if show_genres else None,
                                        "overall_rating": float(show_overall_rating) if show_overall_rating else None,
                                        "status": show_status,
                                    }
                                    if show_poster_url:
                                        update_data["show_thumbnail_url"] = show_poster_url
                                    make_authenticated_request("PUT", f"/tv-shows/{show_id}", json=update_data)
                                    break
                        
                        # If show doesn't exist, create it
                        if show_id is None:
                            show_data = {
                                "title": show_title,
                                "year": int(show_year) if show_year else None,
                                "genres": show_genres if show_genres else None,
                                "overall_rating": float(show_overall_rating) if show_overall_rating else None,
                                "status": show_status,
                                "show_thumbnail_url": show_poster_url
                            }
                            show_response = make_authenticated_request("POST", "/tv-shows/", json=show_data)
                            if show_response.status_code == 201:
                                show_id = show_response.json()['id']
                            else:
                                st.error(f"Failed to create show: {show_response.text}")
                                st.stop()
                        
                        # Now create the season
                        season_data = {
                            "show_id": show_id,
                            "season_number": int(season_number),
                            "watched_date": str(watched_date) if watched_date else None,
                            "rating": float(season_rating) if season_rating else None,
                            "notes": season_notes if season_notes else None,
                            "season_thumbnail_url": season_poster_url
                        }
                        
                        season_response = make_authenticated_request("POST", "/tv-shows/seasons", json=season_data)
                        if season_response.status_code == 201:
                            st.success(f"TV Show '{show_title}' Season {season_number} added successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to add season: {season_response.text}")
                    
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to API. Make sure the backend is running.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    elif media_type == "Book":
        with st.form("manual_book_form"):
            st.subheader("Book Details")
            title = st.text_input("Title *", placeholder="Book title")
            author = st.text_input("Author", placeholder="Author name")
            pages = st.number_input("Number of Pages", min_value=1, value=None, step=1, key="manual_book_pages", help="Optional: Enter the total number of pages")
            status = st.selectbox("Status *", ["currently_reading", "want_to_read", "finished", "dropped"], index=2, key="manual_book_status", help="Current reading status")
            finished_date = st.date_input("Finished Date", value=None, key="manual_book_date", help="Optional: Date when you finished reading")
            rating = st.slider("Rating (0-10)", 0.0, 10.0, 5.0, 0.5, key="manual_book_rating")
            notes = st.text_area("Notes", placeholder="Optional notes", key="manual_book_notes")
            
            st.markdown("---")
            st.subheader("Thumbnail (Optional)")
            uploaded_file = st.file_uploader(
                "Upload thumbnail image",
                type=["png", "jpg", "jpeg", "gif", "webp"],
                key="manual_book_thumbnail"
            )
            
            thumbnail_url = None
            file_bytes = None
            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                st.image(file_bytes, width=200, caption="Thumbnail Preview")
            
            submit = st.form_submit_button("Add Book")
            
            if submit:
                if not title:
                    st.error("Title is required!")
                else:
                    if file_bytes is not None:
                        file_base64 = base64.b64encode(file_bytes).decode('utf-8')
                        file_extension = uploaded_file.name.split('.')[-1].lower()
                        mime_types = {
                            'png': 'image/png',
                            'jpg': 'image/jpeg',
                            'jpeg': 'image/jpeg',
                            'gif': 'image/gif',
                            'webp': 'image/webp'
                        }
                        mime_type = mime_types.get(file_extension, 'image/jpeg')
                        thumbnail_url = f"data:{mime_type};base64,{file_base64}"
                    
                    data = {
                        "title": title,
                        "author": author if author else None,
                        "pages": int(pages) if pages else None,
                        "status": status,
                        "finished_date": str(finished_date) if finished_date else None,
                        "rating": float(rating) if rating else None,
                        "notes": notes if notes else None,
                        "thumbnail_url": thumbnail_url
                    }
                    try:
                        response = make_authenticated_request("POST", "/books/", json=data)
                        if response.status_code == 201:
                            st.success("Book added successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to add book: {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to API. Make sure the backend is running.")
    
    elif media_type == "Music":
        with st.form("manual_music_form"):
            st.subheader("Music Details")
            title = st.text_input("Title *", placeholder="Song/Album/Band name")
            artist = st.text_input("Artist/Band", placeholder="Artist or band name")
            album = st.text_input("Album", placeholder="Album name (if applicable)")
            status = st.selectbox("Status *", ["currently_listening", "want_to_listen", "listened", "dropped"], index=2, key="manual_music_status", help="Current listening status")
            listened_date = st.date_input("Listened Date", value=None, key="manual_music_date", help="Optional: Date when you listened")
            rating = st.slider("Rating (0-10)", 0.0, 10.0, 5.0, 0.5, key="manual_music_rating")
            notes = st.text_area("Notes", placeholder="Optional notes", key="manual_music_notes")
            
            st.markdown("---")
            st.subheader("Thumbnail (Optional)")
            uploaded_file = st.file_uploader(
                "Upload thumbnail image",
                type=["png", "jpg", "jpeg", "gif", "webp"],
                key="manual_music_thumbnail"
            )
            
            thumbnail_url = None
            file_bytes = None
            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                st.image(file_bytes, width=200, caption="Thumbnail Preview")
            
            submit = st.form_submit_button("Add Music")
            
            if submit:
                if not title:
                    st.error("Title is required!")
                else:
                    if file_bytes is not None:
                        file_base64 = base64.b64encode(file_bytes).decode('utf-8')
                        file_extension = uploaded_file.name.split('.')[-1].lower()
                        mime_types = {
                            'png': 'image/png',
                            'jpg': 'image/jpeg',
                            'jpeg': 'image/jpeg',
                            'gif': 'image/gif',
                            'webp': 'image/webp'
                        }
                        mime_type = mime_types.get(file_extension, 'image/jpeg')
                        thumbnail_url = f"data:{mime_type};base64,{file_base64}"
                    
                    data = {
                        "title": title,
                        "artist": artist if artist else None,
                        "album": album if album else None,
                        "status": status,
                        "listened_date": str(listened_date) if listened_date else None,
                        "rating": float(rating) if rating else None,
                        "notes": notes if notes else None,
                        "thumbnail_url": thumbnail_url
                    }
                    try:
                        response = make_authenticated_request("POST", "/music/", json=data)
                        if response.status_code == 201:
                            st.success("Music entry added successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to add music: {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to API. Make sure the backend is running.")


def display_media_thumbnail(thumbnail_url, placeholder_emoji="📷", width="100%", max_height="350px"):
    """Helper function to display a media thumbnail"""
    image_displayed = False
    if thumbnail_url and thumbnail_url.strip() and thumbnail_url != "N/A":
        if thumbnail_url.startswith("http://") or thumbnail_url.startswith("https://"):
            try:
                st.markdown(
                    f'<img src="{thumbnail_url}" style="width:{width};height:auto;border-radius:8px;display:block;margin-bottom:10px;max-height:{max_height};object-fit:contain;">', 
                    unsafe_allow_html=True
                )
                image_displayed = True
            except:
                pass
            
            if not image_displayed:
                try:
                    st.image(thumbnail_url, use_container_width=True)
                    image_displayed = True
                except:
                    pass
        elif thumbnail_url.startswith("data:"):
            try:
                st.markdown(
                    f'<img src="{thumbnail_url}" style="width:{width};height:auto;border-radius:8px;display:block;margin-bottom:10px;max-height:{max_height};object-fit:contain;">', 
                    unsafe_allow_html=True
                )
                image_displayed = True
            except:
                pass
    
    if not image_displayed:
        st.markdown(
            f'<div style="width:{width};height:250px;background:#f0f0f0;display:flex;align-items:center;justify-content:center;border-radius:8px;font-size:48px;margin-bottom:10px;">{placeholder_emoji}</div>', 
            unsafe_allow_html=True
        )


def analytics_page():
    """Analytics page"""
    st.title("📊 Analytics")
    st.markdown("---")
    
    try:
        # Get available years
        years_response = make_authenticated_request("GET", "/analytics/years")
        if years_response.status_code == 200:
            available_years = years_response.json().get("years", [])
            
            if not available_years:
                st.info("No data available yet. Start tracking your media to see analytics!")
                return
            
            # Sidebar controls
            with st.sidebar:
                st.markdown("### Analytics Filters")
                # Get persisted year from query params
                persisted_year = get_filter_from_query_params("analytics_year", available_years[0] if available_years else None)
                if persisted_year not in available_years:
                    persisted_year = available_years[0] if available_years else None
                default_year_index = available_years.index(persisted_year) if persisted_year and persisted_year in available_years else 0
                
                selected_year = st.selectbox("Select Year", available_years, index=default_year_index, key="analytics_year")
                
                # Update query params when year changes
                if selected_year != persisted_year:
                    update_query_params(analytics_year=selected_year)
                
                # Get persisted media type from query params
                media_type_options = ["Movies", "TV Shows", "Books", "Music"]
                persisted_media_type = get_filter_from_query_params("analytics_media_type", "Movies")
                if persisted_media_type not in media_type_options:
                    persisted_media_type = "Movies"
                default_media_index = media_type_options.index(persisted_media_type) if persisted_media_type in media_type_options else 0
                
                media_type = st.selectbox(
                    "Select Media Type",
                    media_type_options,
                    index=default_media_index,
                    key="analytics_media_type"
                )
                
                # Update query params when media type changes
                if media_type != persisted_media_type:
                    update_query_params(analytics_media_type=media_type)
                st.markdown("---")
                
                # Year Summary in sidebar
                if selected_year:
                    st.markdown("### Year Summary")
                    summary_response = make_authenticated_request("GET", f"/analytics/year/{selected_year}")
                    if summary_response.status_code == 200:
                        summary = summary_response.json()
                        
                        st.metric("Movies", summary["movies_count"])
                        st.metric("TV Shows", summary["tv_shows_count"])
                        st.metric("Books", summary["books_count"])
                        st.metric("Music", summary["music_count"])
                        
                        # Pages statistics for books
                        if summary.get("total_pages_read") is not None:
                            st.metric("Total Pages Read", f"{summary['total_pages_read']:,}")
                        if summary.get("avg_pages_per_book") is not None:
                            st.metric("Avg Pages per Book", f"{summary['avg_pages_per_book']:.1f}")
                        
                        st.markdown("#### Average Ratings")
                        if summary.get("avg_movie_rating"):
                            st.caption(f"Movies: {summary['avg_movie_rating']:.2f}/10")
                        if summary.get("avg_tv_rating"):
                            st.caption(f"TV Shows: {summary['avg_tv_rating']:.2f}/10")
                        if summary.get("avg_book_rating"):
                            st.caption(f"Books: {summary['avg_book_rating']:.2f}/10")
                        if summary.get("avg_music_rating"):
                            st.caption(f"Music: {summary['avg_music_rating']:.2f}/10")
            
            # Main content area - display results
            if selected_year:
                st.subheader(f"{media_type} for {selected_year}")
                # Fetch media items for the selected type and year
                params = {"year": selected_year}
                
                if media_type == "Movies":
                    response = make_authenticated_request("GET", "/movies/", params=params)
                    if response.status_code == 200:
                        items = response.json()
                        if items:
                            st.markdown(f"### {len(items)} Movie{'' if len(items) == 1 else 's'}")
                            cols_per_row = 4
                            for i in range(0, len(items), cols_per_row):
                                cols = st.columns(cols_per_row)
                                for j, item in enumerate(items[i:i+cols_per_row]):
                                    with cols[j]:
                                        display_media_thumbnail(item.get("thumbnail_url"), "🎬")
                                        st.write(f"**{item['title']}**")
                                        if item.get('year'):
                                            st.caption(f"Year: {item['year']}")
                                        st.caption(f"Watched: {item['watched_date']}")
                                        rating = item.get('rating')
                                        if rating:
                                            st.caption(f"Rating: {rating}/10")
                        else:
                            st.info(f"No movies found for {selected_year}")
                
                elif media_type == "TV Shows":
                    response = make_authenticated_request("GET", "/tv-shows/", params=params)
                    if response.status_code == 200:
                        shows = response.json()
                        if shows:
                            st.markdown(f"### {len(shows)} TV Show{'' if len(shows) == 1 else 's'}")
                            cols_per_row = 4
                            for i in range(0, len(shows), cols_per_row):
                                cols = st.columns(cols_per_row)
                                for j, show in enumerate(shows[i:i+cols_per_row]):
                                    with cols[j]:
                                        display_media_thumbnail(show.get("show_thumbnail_url"), "📺")
                                        st.write(f"**{show['title']}**")
                                        if show.get('year'):
                                            st.caption(f"Year: {show['year']}")
                                        if show.get('genres'):
                                            st.caption(f"Genres: {show['genres']}")
                                        season_count = len(show.get('seasons', []))
                                        if season_count:
                                            st.caption(f"{season_count} season{'' if season_count == 1 else 's'}")
                                        overall_rating = show.get('overall_rating')
                                        if overall_rating:
                                            st.caption(f"Rating: {overall_rating}/10")
                        else:
                            st.info(f"No TV shows found for {selected_year}")
                
                elif media_type == "Books":
                    response = make_authenticated_request("GET", "/books/", params=params)
                    if response.status_code == 200:
                        items = response.json()
                        if items:
                            st.markdown(f"### {len(items)} Book{'' if len(items) == 1 else 's'}")
                            cols_per_row = 4
                            for i in range(0, len(items), cols_per_row):
                                cols = st.columns(cols_per_row)
                                for j, item in enumerate(items[i:i+cols_per_row]):
                                    with cols[j]:
                                        display_media_thumbnail(item.get("thumbnail_url"), "📖")
                                        st.write(f"**{item['title']}**")
                                        if item.get('author'):
                                            st.caption(f"by {item['author']}")
                                        if item.get('pages'):
                                            st.caption(f"Pages: {item['pages']}")
                                        st.caption(f"Finished: {item['finished_date']}")
                                        rating = item.get('rating')
                                        if rating:
                                            st.caption(f"Rating: {rating}/10")
                        else:
                            st.info(f"No books found for {selected_year}")
                
                elif media_type == "Music":
                    response = make_authenticated_request("GET", "/music/", params=params)
                    if response.status_code == 200:
                        items = response.json()
                        if items:
                            st.markdown(f"### {len(items)} Music Entry{'' if len(items) == 1 else 'ies'}")
                            cols_per_row = 4
                            for i in range(0, len(items), cols_per_row):
                                cols = st.columns(cols_per_row)
                                for j, item in enumerate(items[i:i+cols_per_row]):
                                    with cols[j]:
                                        display_media_thumbnail(item.get("thumbnail_url"), "🎵")
                                        st.write(f"**{item['title']}**")
                                        if item.get('artist'):
                                            st.caption(f"by {item['artist']}")
                                        if item.get('album'):
                                            st.caption(f"Album: {item['album']}")
                                        st.caption(f"Listened: {item['listened_date']}")
                                        rating = item.get('rating')
                                        if rating:
                                            st.caption(f"Rating: {rating}/10")
                        else:
                            st.info(f"No music entries found for {selected_year}")
        else:
            st.error("Failed to load analytics data")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure the backend is running.")


def habit_tracker_page():
    """Habit Tracker page with Log Habits and Calendar tabs"""
    st.title("📅 Daily Habit Tracker")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["Log Habits", "Calendar"])
    
    with tab1:
        log_habits_tab()
    
    with tab2:
        calendar_tab()


def log_habits_tab():
    """Tab for logging daily habits"""
    st.title("📝 Log Daily Habits")
    st.markdown("---")
    
    # Date picker
    selected_date = st.date_input("Date:", value=date.today(), key="habit_date")
    
    # Load existing habits for this date (for form)
    existing_habits = {}
    try:
        response = make_authenticated_request("GET", f"/habits/date/{selected_date}")
        if response.status_code == 200:
            data = response.json()
            existing_habits = data.get("habits", {})
    except:
        pass
    
    # Load detailed habits for deletion
    existing_habits_detailed = []
    try:
        response = make_authenticated_request("GET", f"/habits/date/{selected_date}/detailed")
        if response.status_code == 200:
            existing_habits_detailed = response.json()
    except:
        pass
    
    # Show existing habits with delete options
    if existing_habits_detailed:
        st.markdown("---")
        st.markdown("### 📋 Currently Saved Habits")
        
        # Group by habit type for display
        habits_by_type = {}
        for log in existing_habits_detailed:
            habit_type = log.get("habit_type", "")
            if habit_type not in habits_by_type:
                habits_by_type[habit_type] = []
            habits_by_type[habit_type].append(log)
        
        for habit_type, logs in habits_by_type.items():
            # Clean up habit type name
            parts = habit_type.split('_')
            display_name = ' '.join(word.capitalize() for word in parts[1:]) if len(parts) > 1 else habit_type
            
            with st.expander(f"**{display_name}** ({len(logs)} metric{'s' if len(logs) > 1 else ''})"):
                for log in logs:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        metric_name = log.get("metric_name", "").capitalize()
                        value = log.get("value", 0)
                        unit = log.get("unit", "")
                        st.write(f"{metric_name}: {value} {unit}")
                    with col2:
                        log_id = log.get("id")
                        if st.button("🗑️ Delete", key=f"delete_habit_{log_id}", help="Delete this habit entry"):
                            try:
                                delete_response = make_authenticated_request("DELETE", f"/habits/{log_id}")
                                if delete_response.status_code == 204:
                                    st.success(f"Deleted {metric_name} entry!")
                                    # Clear form state to reload
                                    if f"habit_form_{selected_date}" in st.session_state:
                                        del st.session_state[f"habit_form_{selected_date}"]
                                    st.rerun()
                                else:
                                    st.error(f"Failed to delete: {delete_response.text}")
                            except Exception as e:
                                st.error(f"Error deleting habit: {str(e)}")
                    with col3:
                        st.write("")  # Spacer
        
        # Delete all button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🗑️ Delete All Habits for This Day", key="delete_all_habits", type="secondary"):
                try:
                    delete_response = make_authenticated_request("DELETE", f"/habits/date/{selected_date}")
                    if delete_response.status_code == 204:
                        st.success("All habits for this day deleted successfully!")
                        # Clear form state to reload
                        if f"habit_form_{selected_date}" in st.session_state:
                            del st.session_state[f"habit_form_{selected_date}"]
                        st.rerun()
                    else:
                        st.error(f"Failed to delete: {delete_response.text}")
                except Exception as e:
                    st.error(f"Error deleting habits: {str(e)}")
        
        st.markdown("---")
    
    # Initialize session state for form values
    if f"habit_form_{selected_date}" not in st.session_state:
        st.session_state[f"habit_form_{selected_date}"] = {
            "exercise_workout": {"checked": False, "minutes": ""},
            "exercise_yoga": {"checked": False, "minutes": ""},
            "exercise_running": {"checked": False, "distance": "", "elevation": ""},
            "exercise_biking": {"checked": False, "distance": "", "elevation": ""},
            "mindfulness_meditation": {"checked": False, "minutes": ""},
            "music_guitar": {"checked": False, "minutes": ""},
            "music_drums": {"checked": False, "minutes": ""},
        }
        
        # Load existing data
        if existing_habits:
            for habit_type, metrics in existing_habits.items():
                if habit_type in st.session_state[f"habit_form_{selected_date}"]:
                    st.session_state[f"habit_form_{selected_date}"][habit_type]["checked"] = True
                    for metric in metrics:
                        metric_name = metric["metric_name"].lower()
                        if metric_name == "minutes":
                            st.session_state[f"habit_form_{selected_date}"][habit_type]["minutes"] = str(metric["value"])
                        elif metric_name == "distance":
                            st.session_state[f"habit_form_{selected_date}"][habit_type]["distance"] = str(metric["value"])
                        elif metric_name == "elevation":
                            st.session_state[f"habit_form_{selected_date}"][habit_type]["elevation"] = str(metric["value"])
    
    form_state = st.session_state[f"habit_form_{selected_date}"]
    
    # Exercise Section
    st.markdown("---")
    st.markdown("### 🏋️ Exercise")
    
    # Workout
    workout_checked = st.checkbox("Workout", value=form_state["exercise_workout"]["checked"], key="workout_check")
    if workout_checked:
        workout_minutes = st.number_input("Minutes", min_value=0.0, value=float(form_state["exercise_workout"]["minutes"]) if form_state["exercise_workout"]["minutes"] else 0.0, step=1.0, key="workout_min")
        form_state["exercise_workout"] = {"checked": True, "minutes": str(workout_minutes)}
    else:
        form_state["exercise_workout"] = {"checked": False, "minutes": ""}
    
    # Yoga
    yoga_checked = st.checkbox("Yoga", value=form_state["exercise_yoga"]["checked"], key="yoga_check")
    if yoga_checked:
        yoga_minutes = st.number_input("Minutes", min_value=0.0, value=float(form_state["exercise_yoga"]["minutes"]) if form_state["exercise_yoga"]["minutes"] else 0.0, step=1.0, key="yoga_min")
        form_state["exercise_yoga"] = {"checked": True, "minutes": str(yoga_minutes)}
    else:
        form_state["exercise_yoga"] = {"checked": False, "minutes": ""}
    
    # Running
    running_checked = st.checkbox("Running", value=form_state["exercise_running"]["checked"], key="running_check")
    if running_checked:
        col1, col2 = st.columns(2)
        with col1:
            running_distance = st.number_input("Distance", min_value=0.0, value=float(form_state["exercise_running"]["distance"]) if form_state["exercise_running"]["distance"] else 0.0, step=0.1, key="running_dist")
            st.caption("mi")
        with col2:
            running_elevation = st.number_input("Elevation", min_value=0.0, value=float(form_state["exercise_running"]["elevation"]) if form_state["exercise_running"]["elevation"] else 0.0, step=1.0, key="running_elev")
            st.caption("ft")
        form_state["exercise_running"] = {"checked": True, "distance": str(running_distance), "elevation": str(running_elevation)}
    else:
        form_state["exercise_running"] = {"checked": False, "distance": "", "elevation": ""}
    
    # Biking
    biking_checked = st.checkbox("Biking", value=form_state["exercise_biking"]["checked"], key="biking_check")
    if biking_checked:
        col1, col2 = st.columns(2)
        with col1:
            biking_distance = st.number_input("Distance", min_value=0.0, value=float(form_state["exercise_biking"]["distance"]) if form_state["exercise_biking"]["distance"] else 0.0, step=0.1, key="biking_dist")
            st.caption("mi")
        with col2:
            biking_elevation = st.number_input("Elevation", min_value=0.0, value=float(form_state["exercise_biking"]["elevation"]) if form_state["exercise_biking"]["elevation"] else 0.0, step=1.0, key="biking_elev")
            st.caption("ft")
        form_state["exercise_biking"] = {"checked": True, "distance": str(biking_distance), "elevation": str(biking_elevation)}
    else:
        form_state["exercise_biking"] = {"checked": False, "distance": "", "elevation": ""}
    
    # Mindfulness Section
    st.markdown("---")
    st.markdown("### 🧠 Mindfulness")
    
    meditation_checked = st.checkbox("Meditation", value=form_state["mindfulness_meditation"]["checked"], key="meditation_check")
    if meditation_checked:
        meditation_minutes = st.number_input("Minutes", min_value=0.0, value=float(form_state["mindfulness_meditation"]["minutes"]) if form_state["mindfulness_meditation"]["minutes"] else 0.0, step=1.0, key="meditation_min")
        form_state["mindfulness_meditation"] = {"checked": True, "minutes": str(meditation_minutes)}
    else:
        form_state["mindfulness_meditation"] = {"checked": False, "minutes": ""}
    
    # Music Practice Section
    st.markdown("---")
    st.markdown("### 🎵 Music Practice")
    
    guitar_checked = st.checkbox("Guitar", value=form_state["music_guitar"]["checked"], key="guitar_check")
    if guitar_checked:
        guitar_minutes = st.number_input("Minutes", min_value=0.0, value=float(form_state["music_guitar"]["minutes"]) if form_state["music_guitar"]["minutes"] else 0.0, step=1.0, key="guitar_min")
        form_state["music_guitar"] = {"checked": True, "minutes": str(guitar_minutes)}
    else:
        form_state["music_guitar"] = {"checked": False, "minutes": ""}
    
    drums_checked = st.checkbox("Drums", value=form_state["music_drums"]["checked"], key="drums_check")
    if drums_checked:
        drums_minutes = st.number_input("Minutes", min_value=0.0, value=float(form_state["music_drums"]["minutes"]) if form_state["music_drums"]["minutes"] else 0.0, step=1.0, key="drums_min")
        form_state["music_drums"] = {"checked": True, "minutes": str(drums_minutes)}
    else:
        form_state["music_drums"] = {"checked": False, "minutes": ""}
    
    # Action buttons
    st.markdown("---")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("Clear All", key="clear_habits"):
            st.session_state[f"habit_form_{selected_date}"] = {
                "exercise_workout": {"checked": False, "minutes": ""},
                "exercise_yoga": {"checked": False, "minutes": ""},
                "exercise_running": {"checked": False, "distance": "", "elevation": ""},
                "exercise_biking": {"checked": False, "distance": "", "elevation": ""},
                "mindfulness_meditation": {"checked": False, "minutes": ""},
                "music_guitar": {"checked": False, "minutes": ""},
                "music_drums": {"checked": False, "minutes": ""},
            }
            st.rerun()
    
    with col2:
        if st.button("Save", key="save_habits", type="primary"):
            # Build the logs array
            logs = []
            
            # Exercise
            if form_state["exercise_workout"]["checked"] and form_state["exercise_workout"]["minutes"]:
                logs.append({
                    "habit_type": "exercise_workout",
                    "metric_name": "minutes",
                    "value": float(form_state["exercise_workout"]["minutes"]),
                    "unit": "min"
                })
            
            if form_state["exercise_yoga"]["checked"] and form_state["exercise_yoga"]["minutes"]:
                logs.append({
                    "habit_type": "exercise_yoga",
                    "metric_name": "minutes",
                    "value": float(form_state["exercise_yoga"]["minutes"]),
                    "unit": "min"
                })
            
            if form_state["exercise_running"]["checked"]:
                if form_state["exercise_running"]["distance"]:
                    logs.append({
                        "habit_type": "exercise_running",
                        "metric_name": "distance",
                        "value": float(form_state["exercise_running"]["distance"]),
                        "unit": "mi"
                    })
                if form_state["exercise_running"]["elevation"]:
                    logs.append({
                        "habit_type": "exercise_running",
                        "metric_name": "elevation",
                        "value": float(form_state["exercise_running"]["elevation"]),
                        "unit": "ft"
                    })
            
            if form_state["exercise_biking"]["checked"]:
                if form_state["exercise_biking"]["distance"]:
                    logs.append({
                        "habit_type": "exercise_biking",
                        "metric_name": "distance",
                        "value": float(form_state["exercise_biking"]["distance"]),
                        "unit": "mi"
                    })
                if form_state["exercise_biking"]["elevation"]:
                    logs.append({
                        "habit_type": "exercise_biking",
                        "metric_name": "elevation",
                        "value": float(form_state["exercise_biking"]["elevation"]),
                        "unit": "ft"
                    })
            
            # Mindfulness
            if form_state["mindfulness_meditation"]["checked"] and form_state["mindfulness_meditation"]["minutes"]:
                logs.append({
                    "habit_type": "mindfulness_meditation",
                    "metric_name": "minutes",
                    "value": float(form_state["mindfulness_meditation"]["minutes"]),
                    "unit": "min"
                })
            
            # Music
            if form_state["music_guitar"]["checked"] and form_state["music_guitar"]["minutes"]:
                logs.append({
                    "habit_type": "music_guitar",
                    "metric_name": "minutes",
                    "value": float(form_state["music_guitar"]["minutes"]),
                    "unit": "min"
                })
            
            if form_state["music_drums"]["checked"] and form_state["music_drums"]["minutes"]:
                logs.append({
                    "habit_type": "music_drums",
                    "metric_name": "minutes",
                    "value": float(form_state["music_drums"]["minutes"]),
                    "unit": "min"
                })
            
            # Send to API
            data = {
                "date": str(selected_date),
                "logs": logs
            }
            
            try:
                response = make_authenticated_request("POST", "/habits/", json=data)
                if response.status_code == 201:
                    saved_logs = response.json()
                    habit_count = len(saved_logs)
                    habit_summary = []
                    
                    # Group by habit type for summary
                    habit_types = {}
                    for log in saved_logs:
                        habit_type = log.get("habit_type", "")
                        metric_name = log.get("metric_name", "")
                        value = log.get("value", 0)
                        unit = log.get("unit", "")
                        
                        # Clean up habit type name
                        parts = habit_type.split('_')
                        display_name = ' '.join(word.capitalize() for word in parts[1:]) if len(parts) > 1 else habit_type
                        
                        if habit_type not in habit_types:
                            habit_types[habit_type] = []
                        habit_types[habit_type].append(f"{metric_name.capitalize()}: {value} {unit}")
                    
                    # Build summary message
                    summary_parts = []
                    for habit_type, metrics in habit_types.items():
                        parts = habit_type.split('_')
                        display_name = ' '.join(word.capitalize() for word in parts[1:]) if len(parts) > 1 else habit_type
                        summary_parts.append(f"{display_name} ({', '.join(metrics)})")
                    
                    success_msg = f"✅ **Successfully saved {habit_count} habit{'s' if habit_count != 1 else ''} to database!**\n\n"
                    success_msg += "**Saved habits:**\n"
                    for summary in summary_parts:
                        success_msg += f"• {summary}\n"
                    
                    st.success(success_msg)
                    # Clear form state to reload from DB
                    if f"habit_form_{selected_date}" in st.session_state:
                        del st.session_state[f"habit_form_{selected_date}"]
                    st.rerun()
                else:
                    st.error(f"Failed to save habits: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API. Make sure the backend is running.")
            except Exception as e:
                st.error(f"Error: {str(e)}")


def calendar_tab():
    """Calendar view showing habit completion by date"""
    st.title("📅 Calendar View")
    st.markdown("---")
    
    # View type selector - get persisted value from query params
    view_options = ["Monthly", "Quarterly", "Yearly"]
    persisted_view = get_filter_from_query_params("calendar_view", "Monthly")
    if persisted_view not in view_options:
        persisted_view = "Monthly"
    default_index = view_options.index(persisted_view) if persisted_view in view_options else 0
    
    view_type = st.radio("View", view_options, index=default_index, horizontal=True, key="calendar_view")
    
    # Update query params when view changes
    if view_type != persisted_view:
        update_query_params(calendar_view=view_type)
    
    # Get current date
    today = date.today()
    
    # Navigation and date selection
    if view_type == "Monthly":
        # Month navigation
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("← Previous", key="prev_month"):
                if "calendar_month" not in st.session_state:
                    st.session_state["calendar_month"] = today
                current_month = st.session_state["calendar_month"]
                if current_month.month == 1:
                    st.session_state["calendar_month"] = date(current_month.year - 1, 12, 1)
                else:
                    st.session_state["calendar_month"] = date(current_month.year, current_month.month - 1, 1)
                st.rerun()
        
        with col2:
            if "calendar_month" not in st.session_state:
                st.session_state["calendar_month"] = today
            current_month = st.session_state["calendar_month"]
            st.markdown(f"### {current_month.strftime('%B %Y')}")
        
        with col3:
            if st.button("Next →", key="next_month"):
                current_month = st.session_state["calendar_month"]
                if current_month.month == 12:
                    st.session_state["calendar_month"] = date(current_month.year + 1, 1, 1)
                else:
                    st.session_state["calendar_month"] = date(current_month.year, current_month.month + 1, 1)
                st.rerun()
        
        # Display monthly calendar
        display_monthly_calendar(current_month)
    
    elif view_type == "Quarterly":
        # Quarter navigation
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("← Previous", key="prev_quarter"):
                if "calendar_quarter" not in st.session_state:
                    st.session_state["calendar_quarter"] = today
                current_date = st.session_state["calendar_quarter"]
                quarter = (current_date.month - 1) // 3 + 1
                year = current_date.year
                if quarter == 1:
                    st.session_state["calendar_quarter"] = date(year - 1, 10, 1)
                else:
                    st.session_state["calendar_quarter"] = date(year, (quarter - 2) * 3 + 1, 1)
                st.rerun()
        
        with col2:
            if "calendar_quarter" not in st.session_state:
                st.session_state["calendar_quarter"] = today
            current_date = st.session_state["calendar_quarter"]
            quarter = (current_date.month - 1) // 3 + 1
            quarter_names = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}
            st.markdown(f"### {quarter_names[quarter]} {current_date.year}")
        
        with col3:
            if st.button("Next →", key="next_quarter"):
                current_date = st.session_state["calendar_quarter"]
                quarter = (current_date.month - 1) // 3 + 1
                year = current_date.year
                if quarter == 4:
                    st.session_state["calendar_quarter"] = date(year + 1, 1, 1)
                else:
                    st.session_state["calendar_quarter"] = date(year, quarter * 3 + 1, 1)
                st.rerun()
        
        # Display quarterly calendar
        display_quarterly_calendar(st.session_state["calendar_quarter"])
    
    elif view_type == "Yearly":
        # Year navigation
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("← Previous", key="prev_year"):
                if "calendar_year" not in st.session_state:
                    st.session_state["calendar_year"] = today.year
                st.session_state["calendar_year"] -= 1
                st.rerun()
        
        with col2:
            if "calendar_year" not in st.session_state:
                st.session_state["calendar_year"] = today.year
            st.markdown(f"### {st.session_state['calendar_year']}")
        
        with col3:
            if st.button("Next →", key="next_year"):
                if "calendar_year" not in st.session_state:
                    st.session_state["calendar_year"] = today.year
                st.session_state["calendar_year"] += 1
                st.rerun()
        
        # Display yearly calendar
        display_yearly_calendar(st.session_state["calendar_year"])


def display_monthly_calendar(month_date):
    """Display a monthly calendar grid"""
    import calendar
    
    # Get calendar data
    cal = calendar.monthcalendar(month_date.year, month_date.month)
    
    # Get habit data for the month
    start_date = date(month_date.year, month_date.month, 1)
    if month_date.month == 12:
        end_date = date(month_date.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(month_date.year, month_date.month + 1, 1) - timedelta(days=1)
    
    habit_data = {}
    try:
        response = make_authenticated_request("GET", "/habits/calendar", params={
            "start_date": str(start_date),
            "end_date": str(end_date)
        })
        if response.status_code == 200:
            entries = response.json()
            for entry in entries:
                entry_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
                habit_data[entry_date] = entry["habit_types"]
    except:
        pass
    
    # Day names
    day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    
    # Create calendar grid
    st.markdown("---")
    
    # Header row
    cols = st.columns(7)
    for i, day_name in enumerate(day_names):
        with cols[i]:
            st.markdown(f"**{day_name}**")
    
    # Calendar rows
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.write("")
                else:
                    day_date = date(month_date.year, month_date.month, day)
                    is_today = day_date == date.today()
                    is_current_month = True
                    
                    # Check if date is in current month
                    if day_date.month != month_date.month:
                        is_current_month = False
                    
                    # Get habits for this day
                    habits = habit_data.get(day_date, [])
                    
                    # Display date
                    if is_today:
                        st.markdown(f"**{day}**")
                    elif is_current_month:
                        st.write(f"{day}")
                    else:
                        st.caption(f"{day}")
                    
                    # Display habit icons - one icon per habit
                    if habits:
                        icons = []
                        for habit_type in habits:
                            if "exercise" in habit_type:
                                icons.append("🤸")
                            elif "mindfulness" in habit_type:
                                icons.append("🧘")
                            elif "music" in habit_type:
                                icons.append("🎵")
                            else:
                                icons.append("✓")
                        
                        if icons:
                            st.write(" ".join(icons))


def display_quarterly_calendar(quarter_date):
    """Display a quarterly calendar (3 months)"""
    quarter = (quarter_date.month - 1) // 3 + 1
    start_month = (quarter - 1) * 3 + 1
    year = quarter_date.year
    
    # Get habit data for the quarter
    start_date = date(year, start_month, 1)
    if quarter == 4:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, start_month + 3, 1) - timedelta(days=1)
    
    habit_data = {}
    try:
        response = make_authenticated_request("GET", "/habits/calendar", params={
            "start_date": str(start_date),
            "end_date": str(end_date)
        })
        if response.status_code == 200:
            entries = response.json()
            for entry in entries:
                entry_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
                habit_data[entry_date] = entry["habit_types"]
    except:
        pass
    
    # Display 3 months side by side
    months = []
    for i in range(3):
        month_num = start_month + i
        if month_num > 12:
            month_num -= 12
            month_year = year + 1
        else:
            month_year = year
        months.append((month_year, month_num))
    
    cols = st.columns(3)
    for idx, (month_year, month_num) in enumerate(months):
        with cols[idx]:
            import calendar
            month_name = calendar.month_name[month_num]
            st.markdown(f"### {month_name} {month_year}")
            
            # Get calendar for this month
            cal = calendar.monthcalendar(month_year, month_num)
            day_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
            
            # Header
            header_cols = st.columns(7)
            for i, day_name in enumerate(day_names):
                with header_cols[i]:
                    st.caption(day_name)
            
            # Calendar days
            for week in cal:
                week_cols = st.columns(7)
                for i, day in enumerate(week):
                    with week_cols[i]:
                        if day == 0:
                            st.write("")
                        else:
                            day_date = date(month_year, month_num, day)
                            st.write(f"{day}")
                            
                            # Display habit icons - one icon per habit
                            habits = habit_data.get(day_date, [])
                            if habits:
                                icons = []
                                for habit_type in habits:
                                    if "exercise" in habit_type:
                                        icons.append("🤸")
                                    elif "mindfulness" in habit_type:
                                        icons.append("🧘")
                                    elif "music" in habit_type:
                                        icons.append("🎵")
                                    else:
                                        icons.append("✓")
                                
                                if icons:
                                    st.caption(" ".join(icons))


def display_yearly_calendar(year):
    """Display a yearly calendar (all 12 months)"""
    # Get habit data for the year
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    habit_data = {}
    try:
        response = make_authenticated_request("GET", "/habits/calendar", params={
            "start_date": str(start_date),
            "end_date": str(end_date)
        })
        if response.status_code == 200:
            entries = response.json()
            for entry in entries:
                entry_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
                habit_data[entry_date] = entry["habit_types"]
    except:
        pass
    
    # Display months in a grid (3x4)
    import calendar
    months_per_row = 3
    
    for row in range(0, 12, months_per_row):
        month_cols = st.columns(months_per_row)
        for col_idx in range(months_per_row):
            if row + col_idx < 12:
                month_num = row + col_idx + 1
                with month_cols[col_idx]:
                    month_name = calendar.month_name[month_num]
                    st.markdown(f"#### {month_name}")
                    
                    # Get calendar for this month
                    cal = calendar.monthcalendar(year, month_num)
                    day_names = ["S", "M", "T", "W", "T", "F", "S"]
                    
                    # Header
                    header_cols = st.columns(7)
                    for i, day_name in enumerate(day_names):
                        with header_cols[i]:
                            st.caption(day_name)
                    
                    # Calendar days (compact)
                    for week in cal:
                        week_cols = st.columns(7)
                        for i, day in enumerate(week):
                            with week_cols[i]:
                                if day == 0:
                                    st.write("")
                                else:
                                    day_date = date(year, month_num, day)
                                    # Show date with icon if habits exist
                                    habits = habit_data.get(day_date, [])
                                    if habits:
                                        icons = []
                                        for habit_type in habits:
                                            if "exercise" in habit_type:
                                                icons.append("🤸")
                                            elif "mindfulness" in habit_type:
                                                icons.append("🧘")
                                            elif "music" in habit_type:
                                                icons.append("🎵")
                                            else:
                                                icons.append("✓")
                                        
                                        if icons:
                                            st.caption(f"{day} {' '.join(icons)}")
                                        else:
                                            st.caption(f"{day}")
                                    else:
                                        st.caption(f"{day}")


def habit_analytics_tab():
    """Analytics page for habit tracking with charts and visualizations"""
    st.title("📊 Habit Analytics")
    st.markdown("---")
    
    # Time frame selection
    col1, col2 = st.columns([1, 1])
    
    with col1:
        time_frame = st.selectbox(
            "Time Frame",
            ["This Month", "This Quarter", "This Year", "Last Month", "Last Quarter", "Last Year", "Custom"],
            key="habit_analytics_timeframe"
        )
    
    # Calculate date range based on selection
    today = date.today()
    start_date = None
    end_date = None
    
    if time_frame == "This Month":
        start_date = date(today.year, today.month, 1)
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)
    elif time_frame == "This Quarter":
        quarter = (today.month - 1) // 3 + 1
        start_month = (quarter - 1) * 3 + 1
        start_date = date(today.year, start_month, 1)
        if quarter == 4:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, start_month + 3, 1) - timedelta(days=1)
    elif time_frame == "This Year":
        start_date = date(today.year, 1, 1)
        end_date = date(today.year, 12, 31)
    elif time_frame == "Last Month":
        if today.month == 1:
            start_date = date(today.year - 1, 12, 1)
            end_date = date(today.year - 1, 12, 31)
        else:
            start_date = date(today.year, today.month - 1, 1)
            end_date = date(today.year, today.month, 1) - timedelta(days=1)
    elif time_frame == "Last Quarter":
        quarter = (today.month - 1) // 3 + 1
        if quarter == 1:
            start_month = 10
            year = today.year - 1
        else:
            start_month = (quarter - 2) * 3 + 1
            year = today.year
        start_date = date(year, start_month, 1)
        if start_month == 10:
            end_date = date(year, 12, 31)
        else:
            end_date = date(year, start_month + 3, 1) - timedelta(days=1)
    elif time_frame == "Last Year":
        start_date = date(today.year - 1, 1, 1)
        end_date = date(today.year - 1, 12, 31)
    elif time_frame == "Custom":
        with col2:
            start_date = st.date_input("Start Date", value=today - timedelta(days=30), key="custom_start")
            end_date = st.date_input("End Date", value=today, key="custom_end")
    
    # Fetch analytics data
    try:
        params = {}
        if start_date:
            params["start_date"] = str(start_date)
        if end_date:
            params["end_date"] = str(end_date)
        
        response = make_authenticated_request("GET", "/habits/analytics/summary", params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Display time frame info
            if start_date and end_date:
                st.info(f"📅 Showing data from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
            
            # Key Metrics
            st.markdown("### 📈 Key Metrics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Days with Habits", data.get("total_days_with_habits", 0))
            with col2:
                st.metric("Total Exercise Sessions", data.get("exercise", {}).get("total_sessions", 0))
            with col3:
                st.metric("Total Mindfulness Sessions", data.get("mindfulness", {}).get("total_sessions", 0))
            with col4:
                st.metric("Total Music Sessions", data.get("music", {}).get("total_sessions", 0))
            
            st.markdown("---")
            
            # Exercise Analytics
            st.markdown("### 🏋️ Exercise Analytics")
            exercise_data = data.get("exercise", {})
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Minutes", f"{exercise_data.get('total_minutes', 0):.0f}")
            with col2:
                st.metric("Total Distance", f"{exercise_data.get('total_distance_miles', 0):.2f} mi")
            with col3:
                st.metric("Total Elevation", f"{exercise_data.get('total_elevation_feet', 0):.0f} ft")
            with col4:
                avg_minutes = exercise_data.get('total_minutes', 0) / exercise_data.get('total_sessions', 1) if exercise_data.get('total_sessions', 0) > 0 else 0
                st.metric("Avg Minutes/Session", f"{avg_minutes:.1f}")
            
            # Exercise breakdown by type
            if exercise_data.get('total_sessions', 0) > 0:
                st.markdown("#### Exercise Breakdown")
                exercise_types = {
                    "Workout": exercise_data.get('workout_sessions', 0),
                    "Yoga": exercise_data.get('yoga_sessions', 0),
                    "Running": exercise_data.get('running_sessions', 0),
                    "Biking": exercise_data.get('biking_sessions', 0)
                }
                
                # Filter out zero values
                exercise_types = {k: v for k, v in exercise_types.items() if v > 0}
                
                if exercise_types:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        # Bar chart
                        try:
                            import pandas as pd
                            df_exercise = pd.DataFrame(list(exercise_types.items()), columns=["Type", "Sessions"])
                            st.bar_chart(df_exercise.set_index("Type"))
                        except ImportError:
                            # Fallback if pandas not available
                            st.write("**Exercise Sessions by Type:**")
                            for ex_type, count in exercise_types.items():
                                st.write(f"- {ex_type}: {count}")
                    with col2:
                        # Pie chart using plotly if available, otherwise show data
                        try:
                            import plotly.express as px
                            fig = px.pie(
                                values=list(exercise_types.values()),
                                names=list(exercise_types.keys()),
                                title="Exercise Sessions by Type"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        except:
                            try:
                                import pandas as pd
                                df_exercise = pd.DataFrame(list(exercise_types.items()), columns=["Type", "Sessions"])
                                st.dataframe(df_exercise, use_container_width=True)
                            except:
                                st.write("**Exercise Sessions:**")
                                for ex_type, count in exercise_types.items():
                                    st.write(f"- {ex_type}: {count}")
            
            st.markdown("---")
            
            # Mindfulness Analytics
            st.markdown("### 🧠 Mindfulness Analytics")
            mindfulness_data = data.get("mindfulness", {})
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Minutes", f"{mindfulness_data.get('total_minutes', 0):.0f}")
            with col2:
                avg_minutes = mindfulness_data.get('total_minutes', 0) / mindfulness_data.get('total_sessions', 1) if mindfulness_data.get('total_sessions', 0) > 0 else 0
                st.metric("Avg Minutes/Session", f"{avg_minutes:.1f}")
            
            st.markdown("---")
            
            # Music Analytics
            st.markdown("### 🎵 Music Practice Analytics")
            music_data = data.get("music", {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Minutes", f"{music_data.get('total_minutes', 0):.0f}")
            with col2:
                avg_minutes = music_data.get('total_minutes', 0) / music_data.get('total_sessions', 1) if music_data.get('total_sessions', 0) > 0 else 0
                st.metric("Avg Minutes/Session", f"{avg_minutes:.1f}")
            with col3:
                st.metric("Guitar Sessions", music_data.get('guitar_sessions', 0))
            
            if music_data.get('total_sessions', 0) > 0:
                music_types = {
                    "Guitar": music_data.get('guitar_sessions', 0),
                    "Drums": music_data.get('drums_sessions', 0)
                }
                music_types = {k: v for k, v in music_types.items() if v > 0}
                
                if music_types:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        try:
                            import pandas as pd
                            df_music = pd.DataFrame(list(music_types.items()), columns=["Type", "Sessions"])
                            st.bar_chart(df_music.set_index("Type"))
                        except ImportError:
                            st.write("**Music Practice by Type:**")
                            for music_type, count in music_types.items():
                                st.write(f"- {music_type}: {count}")
                    with col2:
                        try:
                            import plotly.express as px
                            fig = px.pie(
                                values=list(music_types.values()),
                                names=list(music_types.keys()),
                                title="Music Practice by Type"
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        except:
                            try:
                                import pandas as pd
                                df_music = pd.DataFrame(list(music_types.items()), columns=["Type", "Sessions"])
                                st.dataframe(df_music, use_container_width=True)
                            except:
                                st.write("**Music Practice:**")
                                for music_type, count in music_types.items():
                                    st.write(f"- {music_type}: {count}")
            
            st.markdown("---")
            
            # Daily Activity Trends
            st.markdown("### 📊 Daily Activity Trends")
            daily_data = data.get("daily_breakdown", [])
            
            if daily_data:
                try:
                    import pandas as pd
                    df_daily = pd.DataFrame(daily_data)
                    df_daily['date'] = pd.to_datetime(df_daily['date'])
                    df_daily = df_daily.sort_values('date')
                    
                    # Line chart for daily minutes
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("#### Daily Total Minutes")
                        st.line_chart(df_daily.set_index('date')['total_minutes'])
                    
                    with col2:
                        st.markdown("#### Daily Habit Counts")
                        df_counts = df_daily[['date', 'exercise_count', 'mindfulness_count', 'music_count']].set_index('date')
                        st.line_chart(df_counts)
                    
                    # Activity heatmap (simplified as bar chart by day of week)
                    st.markdown("#### Activity by Day of Week")
                    df_daily['day_of_week'] = df_daily['date'].dt.day_name()
                    df_daily['day_of_week_num'] = df_daily['date'].dt.dayofweek
                    
                    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    df_weekly = df_daily.groupby('day_of_week').agg({
                        'exercise_count': 'sum',
                        'mindfulness_count': 'sum',
                        'music_count': 'sum',
                        'total_minutes': 'mean'
                    }).reindex([d for d in day_order if d in df_daily['day_of_week'].values])
                    
                    st.bar_chart(df_weekly[['exercise_count', 'mindfulness_count', 'music_count']])
                except ImportError:
                    st.info("Pandas is required for daily trends visualization. Install with: pip install pandas")
                    st.json(daily_data)
            
            # Habit Type Distribution
            st.markdown("---")
            st.markdown("### 📋 Habit Type Distribution")
            habit_counts = data.get("habit_type_counts", {})
            
            if habit_counts:
                # Clean up habit type names for display
                display_names = {}
                for habit_type, count in habit_counts.items():
                    # Convert "exercise_workout" to "Exercise: Workout"
                    parts = habit_type.split('_')
                    category = parts[0].capitalize()
                    activity = ' '.join(word.capitalize() for word in parts[1:])
                    display_name = f"{category}: {activity}"
                    display_names[display_name] = count
                
                try:
                    import pandas as pd
                    df_habits = pd.DataFrame(list(display_names.items()), columns=["Habit Type", "Count"])
                    df_habits = df_habits.sort_values('Count', ascending=False)
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.bar_chart(df_habits.set_index("Habit Type"))
                    with col2:
                        st.dataframe(df_habits, use_container_width=True)
                except ImportError:
                    st.write("**Habit Type Distribution:**")
                    sorted_habits = sorted(display_names.items(), key=lambda x: x[1], reverse=True)
                    for habit_name, count in sorted_habits:
                        st.write(f"- {habit_name}: {count}")
        else:
            st.error(f"Failed to load analytics: {response.text}")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure the backend is running.")
    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def portfolio_overview_page():
    """Portfolio overview page showing summary and all holdings"""
    st.title("💼 Portfolio Overview")
    st.markdown("---")
    
    try:
        # Get portfolio summary
        response = make_authenticated_request("GET", "/portfolio/summary")
        if response.status_code == 200:
            summary = response.json()
            
            # Display overall metrics
            st.markdown("### 📊 Portfolio Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Invested",
                    f"${summary['total_invested']:,.2f}"
                )
            
            with col2:
                if summary.get('current_value') is not None:
                    st.metric(
                        "Current Value",
                        f"${summary['current_value']:,.2f}"
                    )
                else:
                    st.metric(
                        "Current Value",
                        "N/A",
                        help="Current prices not available"
                    )
            
            with col3:
                if summary.get('total_profit_loss') is not None:
                    st.metric(
                        "Total P/L",
                        f"${summary['total_profit_loss']:,.2f}",
                        delta=f"{summary['total_profit_loss_percentage']:.2f}%"
                    )
                else:
                    st.metric(
                        "Total P/L",
                        "N/A",
                        help="Current prices not available"
                    )
            
            with col4:
                st.metric(
                    "# Holdings",
                    len(summary['holdings'])
                )
            
            st.markdown("---")
            
            # Delete All Section (Danger Zone)
            with st.expander("🗑️ Delete All Transactions (Danger Zone)", expanded=False):
                st.warning("⚠️ **Warning**: This will permanently delete ALL portfolio transactions and remove all holdings from your portfolio. This action cannot be undone.")
                
                # Get transaction count
                try:
                    txn_count_response = make_authenticated_request("GET", "/portfolio/transactions")
                    if txn_count_response.status_code == 200:
                        all_transactions = txn_count_response.json()
                        txn_count = len(all_transactions)
                        st.info(f"📊 There are currently **{txn_count}** transaction(s) that will be deleted.")
                    else:
                        st.info("⚠️ Unable to fetch transaction count.")
                except Exception as e:
                    st.info("⚠️ Unable to fetch transaction count.")
                
                st.markdown("---")
                
                # Confirmation checkbox
                confirm_delete_all = st.checkbox(
                    "I understand this will delete ALL portfolio data permanently",
                    key="confirm_delete_all_transactions"
                )
                
                if confirm_delete_all:
                    if st.button(
                        "🗑️ DELETE ALL TRANSACTIONS",
                        key="delete_all_transactions",
                        type="primary",
                        use_container_width=True
                    ):
                        try:
                            del_response = make_authenticated_request("DELETE", "/portfolio/transactions")
                            if del_response.status_code == 200:
                                result = del_response.json()
                                st.success(f"✅ Successfully deleted {result.get('deleted_count', 0)} transaction(s)!")
                                st.info("Refreshing page...")
                                st.rerun()
                            else:
                                st.error(f"Failed to delete transactions: {del_response.text}")
                        except Exception as e:
                            st.error(f"Error deleting transactions: {str(e)}")
            
            st.markdown("---")
            
            # Display holdings table
            st.markdown("### 📈 Current Holdings")
            
            if summary['holdings']:
                holdings = summary['holdings']
                
                # Create header row
                header_cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1, 1])
                headers = ["Ticker", "Type", "Quantity", "Avg Cost", "Invested", "Current Price", "Current Value", "P/L", "P/L %"]
                for col, header in zip(header_cols, headers):
                    col.markdown(f"**{header}**")
                
                st.markdown("---")
                
                # Display each holding as a row with clickable ticker
                for holding in holdings:
                    cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1, 1])
                    
                    with cols[0]:
                        # Make ticker clickable
                        if st.button(holding['ticker'], key=f"ticker_{holding['ticker']}", help=f"Click to view detailed breakdown"):
                            st.session_state["selected_page"] = "Individual Holdings"
                            st.session_state[f"selected_ticker_{holding['ticker']}"] = True
                            st.experimental_set_query_params(
                                category="Portfolio Tracker",
                                page="Individual Holdings"
                            )
                            st.rerun()
                    with cols[1]:
                        st.write(holding['asset_type'])
                    with cols[2]:
                        st.write(f"{holding['total_quantity']:.2f}")
                    with cols[3]:
                        st.write(f"${holding['average_cost']:.2f}")
                    with cols[4]:
                        st.write(f"${holding['total_invested']:,.2f}")
                    with cols[5]:
                        st.write(f"${holding['current_price']:.2f}" if holding.get('current_price') else "N/A")
                    with cols[6]:
                        st.write(f"${holding['current_value']:,.2f}" if holding.get('current_value') else "N/A")
                    with cols[7]:
                        profit_loss = holding.get('profit_loss')
                        if profit_loss is not None:
                            color = "green" if profit_loss >= 0 else "red"
                            st.markdown(f":{color}[${profit_loss:,.2f}]")
                        else:
                            st.write("N/A")
                    with cols[8]:
                        pl_pct = holding.get('profit_loss_percentage')
                        if pl_pct is not None:
                            color = "green" if pl_pct >= 0 else "red"
                            st.markdown(f":{color}[{pl_pct:.2f}%]")
                        else:
                            st.write("N/A")
                
                # Pie chart of holdings by value
                st.markdown("### 📊 Holdings Distribution")
                
                try:
                    import plotly.graph_objects as go
                    
                    # Create pie chart for invested amounts
                    labels = [h['ticker'] for h in holdings]
                    values = [h['total_invested'] for h in holdings]
                    
                    fig = go.Figure(data=[go.Pie(
                        labels=labels,
                        values=values,
                        hole=0.3
                    )])
                    fig.update_layout(title_text="Portfolio Allocation by Investment")
                    st.plotly_chart(fig, use_container_width=True)
                except ImportError:
                    st.info("Install plotly for visualization: pip install plotly")
            else:
                st.info("No holdings found. Add transactions to see your portfolio.")
        
        else:
            st.error(f"Failed to load portfolio summary: {response.text}")
    
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure the backend is running.")
    except Exception as e:
        st.error(f"Error loading portfolio: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def portfolio_transactions_page():
    """View and manage portfolio transactions"""
    st.title("📝 Transactions")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["View Transactions", "Add Transaction"])
    
    with tab1:
        st.subheader("All Transactions")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            ticker_filter = st.text_input("Filter by Ticker (optional)", "").upper()
        with col2:
            asset_type_filter = st.selectbox(
                "Filter by Asset Type",
                ["All", "STOCK", "ETF", "MUTUAL_FUND"]
            )
        
        try:
            params = {}
            if ticker_filter:
                params["ticker"] = ticker_filter
            if asset_type_filter != "All":
                params["asset_type"] = asset_type_filter
            
            response = make_authenticated_request("GET", "/portfolio/transactions", params=params)
            if response.status_code == 200:
                transactions = response.json()
                
                if transactions:
                    # Display transactions
                    for txn in transactions:
                        with st.expander(
                            f"{txn['ticker']} - {txn['transaction_type']} - {txn['transaction_date']} - ${txn['total_amount']:,.2f}"
                        ):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Ticker:** {txn['ticker']}")
                                st.write(f"**Type:** {txn['transaction_type']}")
                                st.write(f"**Asset Type:** {txn['asset_type']}")
                                st.write(f"**Date:** {txn['transaction_date']}")
                            with col2:
                                st.write(f"**Quantity:** {txn['quantity']:.2f}")
                                st.write(f"**Price/Unit:** ${txn['price_per_unit']:.2f}")
                                st.write(f"**Total:** ${txn['total_amount']:,.2f}")
                                st.write(f"**Fees:** ${txn['fees']:.2f}")
                            
                            if txn.get('notes'):
                                st.write(f"**Notes:** {txn['notes']}")
                            
                            # Delete button
                            if st.button("Delete", key=f"delete_txn_{txn['id']}"):
                                try:
                                    del_response = make_authenticated_request(
                                        "DELETE",
                                        f"/portfolio/transactions/{txn['id']}"
                                    )
                                    if del_response.status_code == 204:
                                        st.success("Transaction deleted!")
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to delete: {del_response.text}")
                                except Exception as e:
                                    st.error(f"Error deleting transaction: {str(e)}")
                else:
                    st.info("No transactions found.")
            else:
                st.error(f"Failed to load transactions: {response.text}")
        
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API. Make sure the backend is running.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with tab2:
        st.subheader("Add New Transaction")
        
        with st.form("add_transaction_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                ticker = st.text_input("Ticker Symbol*", placeholder="e.g., AAPL").upper()
                transaction_type = st.selectbox("Transaction Type*", ["BUY", "SELL"])
                asset_type = st.selectbox("Asset Type*", ["STOCK", "ETF", "MUTUAL_FUND"])
                transaction_date = st.date_input("Transaction Date*", value=date.today())
            
            with col2:
                quantity = st.number_input("Quantity (shares)*", min_value=0.0, step=0.01, format="%.2f")
                price_per_unit = st.number_input("Price per Unit*", min_value=0.0, step=0.01, format="%.2f")
                fees = st.number_input("Fees", min_value=0.0, step=0.01, value=0.0, format="%.2f")
                total_amount = st.number_input(
                    "Total Amount*",
                    min_value=0.0,
                    step=0.01,
                    value=quantity * price_per_unit if quantity and price_per_unit else 0.0,
                    format="%.2f"
                )
            
            notes = st.text_area("Notes (optional)")
            
            submitted = st.form_submit_button("Add Transaction")
            
            if submitted:
                if not ticker or not quantity or not price_per_unit or not total_amount:
                    st.error("Please fill in all required fields (marked with *)")
                else:
                    try:
                        transaction_data = {
                            "ticker": ticker,
                            "transaction_type": transaction_type,
                            "transaction_date": str(transaction_date),
                            "quantity": quantity,
                            "price_per_unit": price_per_unit,
                            "total_amount": total_amount,
                            "fees": fees,
                            "notes": notes,
                            "asset_type": asset_type
                        }
                        
                        response = make_authenticated_request(
                            "POST",
                            "/portfolio/transactions",
                            json=transaction_data
                        )
                        
                        if response.status_code == 201:
                            st.success(f"Transaction added successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to add transaction: {response.text}")
                    
                    except Exception as e:
                        st.error(f"Error adding transaction: {str(e)}")


def portfolio_upload_page():
    """Upload transactions from JSON"""
    st.title("📤 Upload Transaction Data")
    st.markdown("---")
    
    st.markdown("""
    ### Upload Historical Transactions
    
    Upload your transaction history from a JSON file or paste JSON directly. 
    
    **Supported Formats:**
    1. **Schwab Brokerage Format** - Direct export from Schwab (automatically detected)
    2. **Standard Format** - Our simple transaction format
    """)
    
    # Example JSON formats
    with st.expander("📋 Standard Format Example"):
        example_json = {
            "transactions": [
                {
                    "ticker": "AAPL",
                    "transaction_type": "BUY",
                    "transaction_date": "2024-01-15",
                    "quantity": 10.0,
                    "price_per_unit": 185.50,
                    "total_amount": 1855.00,
                    "fees": 0.0,
                    "notes": "Initial purchase",
                    "asset_type": "STOCK"
                },
                {
                    "ticker": "VTI",
                    "transaction_type": "BUY",
                    "transaction_date": "2024-02-01",
                    "quantity": 25.0,
                    "price_per_unit": 235.80,
                    "total_amount": 5895.00,
                    "fees": 0.0,
                    "notes": "ETF purchase",
                    "asset_type": "ETF"
                }
            ]
        }
        st.json(example_json)
    
    with st.expander("📋 Schwab Format Example"):
        schwab_example = {
            "FromDate": "11/06/2025",
            "ToDate": "11/07/2025",
            "BrokerageTransactions": [
                {
                    "Date": "11/07/2025",
                    "Action": "Buy",
                    "Symbol": "SCHE",
                    "Description": "SCHWAB EMERGING MARKETS EQUITY ETF",
                    "Quantity": "14",
                    "Price": "$33.3799",
                    "Fees & Comm": "",
                    "Amount": "-$467.32"
                }
            ]
        }
        st.json(schwab_example)
        st.info("💡 Schwab format is automatically detected and parsed!")
    
    st.markdown("---")
    
    # Upload method tabs
    upload_tab1, upload_tab2 = st.tabs(["📁 Upload File", "📋 Paste JSON"])
    
    with upload_tab1:
        st.subheader("Upload JSON File")
        uploaded_file = st.file_uploader(
            "Choose a JSON file",
            type=['json'],
            help="Upload your Schwab transaction export or standard format JSON file"
        )
        
        if uploaded_file is not None:
            try:
                # Read the file
                file_contents = uploaded_file.read()
                data = json.loads(file_contents)
                
                # Show preview
                with st.expander("📄 Preview Uploaded Data"):
                    st.json(data)
                
                if st.button("Process and Upload", type="primary", key="upload_file_btn"):
                    try:
                        # Upload to API using flexible endpoint
                        response = make_authenticated_request(
                            "POST",
                            "/portfolio/transactions/upload",
                            json=data
                        )
                        
                        if response.status_code == 201:
                            created = response.json()
                            st.success(f"✅ Successfully uploaded {len(created)} transactions!")
                            
                            # Show summary
                            with st.expander("View Uploaded Transactions"):
                                for txn in created:
                                    st.write(f"- {txn['ticker']} ({txn['asset_type']}): {txn['transaction_type']} {txn['quantity']} @ ${txn['price_per_unit']} on {txn['transaction_date']}")
                        else:
                            st.error(f"Failed to upload transactions: {response.text}")
                    
                    except Exception as e:
                        st.error(f"Error uploading transactions: {str(e)}")
            
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON file: {str(e)}")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    with upload_tab2:
        st.subheader("Paste Your JSON Data")
        json_input = st.text_area(
            "Transaction JSON",
            height=300,
            placeholder='{"transactions": [...]} or Schwab format'
        )
        
        if st.button("Process and Upload", type="primary", key="upload_paste_btn"):
            if not json_input.strip():
                st.error("Please paste your JSON data")
            else:
                try:
                    # Parse JSON
                    data = json.loads(json_input)
                    
                    # Upload to API using flexible endpoint
                    response = make_authenticated_request(
                        "POST",
                        "/portfolio/transactions/upload",
                        json=data
                    )
                    
                    if response.status_code == 201:
                        created = response.json()
                        st.success(f"✅ Successfully uploaded {len(created)} transactions!")
                        
                        # Show summary
                        with st.expander("View Uploaded Transactions"):
                            for txn in created:
                                st.write(f"- {txn['ticker']} ({txn['asset_type']}): {txn['transaction_type']} {txn['quantity']} @ ${txn['price_per_unit']} on {txn['transaction_date']}")
                    else:
                        st.error(f"Failed to upload transactions: {response.text}")
                
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON format: {str(e)}")
                except Exception as e:
                    st.error(f"Error uploading transactions: {str(e)}")


def portfolio_individual_holdings_page():
    """View individual ticker holdings with detailed breakdown in tabs"""
    st.title("📊 Individual Holdings Breakdown")
    st.markdown("---")
    
    try:
        # Get all tickers
        response = make_authenticated_request("GET", "/portfolio/tickers")
        if response.status_code == 200:
            tickers = response.json()
            
            if not tickers:
                st.info("No holdings found. Add transactions first.")
                return
            
            # Check if a specific ticker was selected from another page
            selected_ticker_from_link = None
            for ticker in tickers:
                if st.session_state.get(f"selected_ticker_{ticker}", False):
                    selected_ticker_from_link = ticker
                    # Clear the flag
                    st.session_state[f"selected_ticker_{ticker}"] = False
                    break
            
            # Determine default index
            default_index = 0
            if selected_ticker_from_link and selected_ticker_from_link in tickers:
                default_index = tickers.index(selected_ticker_from_link)
            
            # Use selectbox to choose ticker
            selected_ticker = st.selectbox(
                "Select Ticker to View Details:",
                tickers,
                index=default_index,
                key="individual_holdings_ticker_select"
            )
            
            st.markdown("---")
            
            # Display only the selected ticker
            if selected_ticker:
                ticker = selected_ticker
                st.markdown(f"## {ticker}")
                st.markdown("---")
                
                # Get holding details
                holding_response = make_authenticated_request(
                    "GET",
                    f"/portfolio/holdings/{ticker}"
                )
                
                if holding_response.status_code == 200:
                    holding = holding_response.json()
                    
                    # Display metrics in a compact row
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.metric("Asset Type", holding['asset_type'])
                    
                    with col2:
                        st.metric("Quantity", f"{holding['total_quantity']:.2f}")
                    
                    with col3:
                        st.metric("Avg Cost", f"${holding['average_cost']:.2f}")
                    
                    with col4:
                        st.metric("Invested", f"${holding['total_invested']:,.2f}")
                    
                    with col5:
                        if holding.get('current_price'):
                            st.metric(
                                "P/L",
                                f"${holding['profit_loss']:,.2f}",
                                delta=f"{holding['profit_loss_percentage']:.2f}%"
                            )
                        else:
                            st.metric("Current Price", "N/A")
                    
                    st.markdown("---")
                    
                    # Delete Ticker Section (Danger Zone)
                    with st.expander("🗑️ Delete Ticker (Remove All Transactions)", expanded=False):
                        st.warning(f"⚠️ **Warning**: This will permanently delete ALL transactions for **{ticker}** and remove it from your portfolio.")
                        
                        # Show transaction count
                        txn_count_response = make_authenticated_request(
                            "GET",
                            "/portfolio/transactions",
                            params={"ticker": ticker}
                        )
                        
                        if txn_count_response.status_code == 200:
                            txn_count = len(txn_count_response.json())
                            st.info(f"📊 This ticker has **{txn_count}** transaction(s) that will be deleted.")
                        
                        st.markdown("---")
                        
                        # Confirmation checkbox
                        confirm_delete_ticker = st.checkbox(
                            f"I understand this will delete all {ticker} data permanently",
                            key=f"confirm_delete_ticker_{ticker}"
                        )
                        
                        if confirm_delete_ticker:
                            if st.button(
                                f"🗑️ DELETE ALL {ticker} TRANSACTIONS",
                                key=f"delete_all_ticker_{ticker}",
                                type="primary",
                                use_container_width=True
                            ):
                                try:
                                    # Get all transactions for this ticker
                                    response = make_authenticated_request(
                                        "GET",
                                        "/portfolio/transactions",
                                        params={"ticker": ticker}
                                    )
                                    
                                    if response.status_code == 200:
                                        transactions_to_delete = response.json()
                                        deleted_count = 0
                                        failed_count = 0
                                        
                                        # Delete each transaction
                                        for txn in transactions_to_delete:
                                            del_response = make_authenticated_request(
                                                "DELETE",
                                                f"/portfolio/transactions/{txn['id']}"
                                            )
                                            
                                            if del_response.status_code == 204:
                                                deleted_count += 1
                                            else:
                                                failed_count += 1
                                        
                                        if deleted_count > 0:
                                            st.success(f"✅ Successfully deleted {deleted_count} transaction(s) for {ticker}!")
                                            st.info("Refreshing page...")
                                            st.rerun()
                                        else:
                                            st.error("No transactions were deleted.")
                                        
                                        if failed_count > 0:
                                            st.error(f"❌ Failed to delete {failed_count} transaction(s)")
                                    else:
                                        st.error(f"Failed to fetch transactions: {response.text}")
                                
                                except Exception as e:
                                    st.error(f"Error deleting ticker: {str(e)}")
                    
                    st.markdown("---")
                    
                    # Quick Add Transaction Form
                    with st.expander("➕ Quick Add Transaction", expanded=False):
                        with st.form(f"quick_add_transaction_{ticker}"):
                            st.markdown(f"**Add transaction for {ticker}**")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                transaction_type = st.selectbox(
                                    "Transaction Type*", 
                                    ["BUY", "SELL"],
                                    key=f"quick_txn_type_{ticker}"
                                )
                                transaction_date = st.date_input(
                                    "Transaction Date*", 
                                    value=date.today(),
                                    key=f"quick_txn_date_{ticker}"
                                )
                                quantity = st.number_input(
                                    "Quantity (shares)*", 
                                    min_value=0.0, 
                                    step=0.01, 
                                    format="%.2f",
                                    key=f"quick_quantity_{ticker}"
                                )
                            
                            with col2:
                                price_per_unit = st.number_input(
                                    "Price per Unit*", 
                                    min_value=0.0, 
                                    step=0.01, 
                                    format="%.2f",
                                    key=f"quick_price_{ticker}"
                                )
                                fees = st.number_input(
                                    "Fees", 
                                    min_value=0.0, 
                                    step=0.01, 
                                    value=0.0, 
                                    format="%.2f",
                                    key=f"quick_fees_{ticker}"
                                )
                                total_amount = st.number_input(
                                    "Total Amount*",
                                    min_value=0.0,
                                    step=0.01,
                                    value=quantity * price_per_unit if quantity and price_per_unit else 0.0,
                                    format="%.2f",
                                    key=f"quick_total_{ticker}"
                                )
                            
                            notes = st.text_area(
                                "Notes (optional)",
                                key=f"quick_notes_{ticker}"
                            )
                            
                            submitted = st.form_submit_button("Add Transaction", use_container_width=True)
                            
                            if submitted:
                                if not quantity or not price_per_unit or not total_amount:
                                    st.error("Please fill in all required fields (marked with *)")
                                else:
                                    try:
                                        transaction_data = {
                                            "ticker": ticker,
                                            "transaction_type": transaction_type,
                                            "transaction_date": str(transaction_date),
                                            "quantity": quantity,
                                            "price_per_unit": price_per_unit,
                                            "total_amount": total_amount,
                                            "fees": fees,
                                            "notes": notes,
                                            "asset_type": holding['asset_type']  # Use existing asset type
                                        }
                                        
                                        response = make_authenticated_request(
                                            "POST",
                                            "/portfolio/transactions",
                                            json=transaction_data
                                        )
                                        
                                        if response.status_code == 201:
                                            st.success(f"✅ Transaction added successfully for {ticker}!")
                                            st.info("Refreshing page to show updated data...")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to add transaction: {response.text}")
                                    
                                    except Exception as e:
                                        st.error(f"Error adding transaction: {str(e)}")
                    
                    st.markdown("---")
                    
                    # Get all transactions for this ticker
                    txn_response = make_authenticated_request(
                        "GET",
                        "/portfolio/transactions",
                        params={"ticker": ticker}
                    )
                    
                    if txn_response.status_code == 200:
                        transactions = txn_response.json()
                        
                        if transactions:
                            # Get split information for this ticker
                            try:
                                split_response = make_authenticated_request(
                                    "GET",
                                    f"/portfolio/splits/{ticker}"
                                )
                                splits_data = split_response.json() if split_response.status_code == 200 else {}
                                splits = splits_data.get('splits', {})
                                
                                # Show split information if any
                                if splits:
                                    st.info(
                                        f"📊 **Stock Splits Detected:** {len(splits)} split(s) applied to historical data. "
                                        f"All quantities and prices are adjusted for accurate tracking."
                                    )
                                    with st.expander("View Split Details"):
                                        for split_date, split_ratio in splits.items():
                                            st.write(f"**{split_date}**: {split_ratio:.2f}-for-1 split")
                            except:
                                splits = {}
                            
                            # Sort by date
                            transactions_sorted = sorted(transactions, key=lambda x: x['transaction_date'])
                            
                            # Apply split adjustments to historical transactions
                            # This ensures we're comparing post-split prices with post-split current price
                            for txn in transactions_sorted:
                                # Get split ratio for this transaction
                                txn_date_obj = txn['transaction_date']
                                if isinstance(txn_date_obj, str):
                                    from datetime import datetime as dt
                                    txn_date_obj = dt.strptime(txn_date_obj, "%Y-%m-%d").date()
                                
                                # Calculate split adjustment
                                split_ratio = 1.0
                                if splits:
                                    for split_date_str, ratio in splits.items():
                                        try:
                                            from datetime import datetime as dt
                                            split_date = dt.strptime(split_date_str, '%Y-%m-%d').date()
                                            # If split happened AFTER this transaction, adjust the price
                                            if split_date > txn_date_obj:
                                                split_ratio *= ratio
                                        except:
                                            continue
                                
                                # Apply split adjustment to this transaction
                                # Quantity increases, price decreases by split ratio
                                if split_ratio != 1.0:
                                    txn['quantity'] = txn['quantity'] * split_ratio
                                    txn['price_per_unit'] = txn['price_per_unit'] / split_ratio
                                    # total_amount stays the same (quantity × price remains constant)
                            
                            # Calculate cumulative gain/loss over time (matching Excel logic)
                            # Each purchase lot contributes: (lot_quantity × current_price) - lot_cost
                            # Cumulative = Sum of all lot contributions (for remaining lots after FIFO sells)
                            # This shows the total performance across all your investments at different cost bases
                            timeline_data = []
                            
                            # Track purchase lots with their original purchase price for delta calculation
                            purchase_lots = []  # List of {'quantity': float, 'price_per_unit': float, 'total_cost': float, 'date': str}
                            
                            # Get current market price to use for all calculations
                            current_market_price = holding.get('current_price')
                            
                            if not current_market_price:
                                # Fallback: use last transaction price if no current price
                                if transactions_sorted:
                                    current_market_price = transactions_sorted[-1]['price_per_unit']
                            
                            for txn in transactions_sorted:
                                txn_date = txn['transaction_date']
                                txn_type = txn['transaction_type']
                                quantity = txn['quantity']
                                price = txn['price_per_unit']
                                total_cost = txn['total_amount'] + txn.get('fees', 0)
                                
                                if txn_type == 'BUY':
                                    # Add this purchase lot with its original purchase price
                                    purchase_lots.append({
                                        'quantity': quantity,
                                        'price_per_unit': price,
                                        'total_cost': total_cost,
                                        'date': txn_date
                                    })
                                    
                                elif txn_type == 'SELL':
                                    # Remove sold shares using FIFO
                                    remaining_to_sell = quantity
                                    
                                    while remaining_to_sell > 0 and purchase_lots:
                                        lot = purchase_lots[0]
                                        lot_quantity = lot['quantity']
                                        
                                        if lot_quantity <= remaining_to_sell:
                                            # Sell entire lot
                                            remaining_to_sell -= lot_quantity
                                            purchase_lots.pop(0)
                                        else:
                                            # Sell partial lot - reduce quantity proportionally
                                            sold_ratio = remaining_to_sell / lot_quantity
                                            lot['quantity'] -= remaining_to_sell
                                            lot['total_cost'] -= (lot['total_cost'] * sold_ratio)
                                            # price_per_unit stays the same (original purchase price)
                                            remaining_to_sell = 0
                                
                                # Calculate cumulative gain/loss: sum of each lot's contribution
                                # Each lot contributes: (lot_qty × current_price) - lot_cost
                                cumulative_gain_loss = 0.0
                                total_quantity = 0.0
                                total_cost_basis = 0.0
                                
                                if current_market_price:
                                    for lot in purchase_lots:
                                        lot_current_value = lot['quantity'] * current_market_price
                                        lot_gain_loss = lot_current_value - lot['total_cost']
                                        cumulative_gain_loss += lot_gain_loss
                                        total_quantity += lot['quantity']
                                        total_cost_basis += lot['total_cost']
                                else:
                                    total_quantity = sum(lot['quantity'] for lot in purchase_lots)
                                    total_cost_basis = sum(lot['total_cost'] for lot in purchase_lots)
                                
                                avg_cost_basis = total_cost_basis / total_quantity if total_quantity > 0 else 0
                                
                                timeline_data.append({
                                    'date': txn_date,
                                    'quantity': total_quantity,
                                    'avg_cost': avg_cost_basis,
                                    'invested': total_cost_basis,
                                    'cumulative_gain_loss': cumulative_gain_loss,
                                    'transaction_type': txn_type,
                                    'transaction_quantity': quantity,
                                    'transaction_price': price
                                })
                            
                            # Add final data point with current price if available (for most up-to-date view)
                            if current_market_price and timeline_data:
                                last_entry = timeline_data[-1]
                                
                                # Use today's date for the final point
                                from datetime import datetime
                                final_date = datetime.now().date().isoformat()
                                
                                # Recalculate cumulative with current price (sum of all lot contributions)
                                final_cumulative = 0.0
                                for lot in purchase_lots:
                                    lot_current_value = lot['quantity'] * current_market_price
                                    lot_gain_loss = lot_current_value - lot['total_cost']
                                    final_cumulative += lot_gain_loss
                                
                                timeline_data.append({
                                    'date': final_date,
                                    'quantity': last_entry['quantity'],
                                    'avg_cost': last_entry['avg_cost'],
                                    'invested': last_entry['invested'],
                                    'cumulative_gain_loss': final_cumulative,
                                    'transaction_type': 'CURRENT',
                                    'transaction_quantity': 0,
                                    'transaction_price': current_market_price
                                })
                            
                            # Plot cumulative gain/loss timeline
                            st.markdown("### 📈 Cumulative Gain/Loss Over Time")
                            
                            if timeline_data:
                                try:
                                    import plotly.graph_objects as go
                                    import pandas as pd
                                    from datetime import datetime
                                    
                                    df = pd.DataFrame(timeline_data)
                                    
                                    # Convert date strings to datetime objects
                                    df['date'] = pd.to_datetime(df['date'])
                                    
                                    # CRITICAL: Force numeric type and clean any issues
                                    df['cumulative_gain_loss'] = pd.to_numeric(df['cumulative_gain_loss'], errors='coerce')
                                    
                                    # Create figure focused on cumulative gain/loss
                                    fig = go.Figure()
                                    
                                    # Determine line color based on final gain/loss (green for positive, red for negative)
                                    final_gain_loss = float(df['cumulative_gain_loss'].iloc[-1])
                                    line_color = '#00cc88' if final_gain_loss >= 0 else '#ff4444'  # Streamlit-style colors
                                    
                                    # Set fill color based on gain/loss
                                    if final_gain_loss >= 0:
                                        fill_color = 'rgba(0, 204, 136, 0.15)'  # Light green
                                    else:
                                        fill_color = 'rgba(255, 68, 68, 0.15)'  # Light red
                                    
                                    # Convert to lists to avoid any pandas/plotly interaction issues
                                    x_data = df['date'].tolist()
                                    y_data = df['cumulative_gain_loss'].tolist()
                                    
                                    # Add cumulative gain/loss line
                                    fig.add_trace(go.Scatter(
                                        x=x_data,
                                        y=y_data,
                                        mode='lines+markers',
                                        name='Cumulative Gain/Loss',
                                        line=dict(color=line_color, width=3),
                                        marker=dict(size=6, color=line_color),
                                        hovertemplate='<b>%{x}</b><br>Cumulative Gain/Loss: $%{y:,.2f}<extra></extra>',
                                        fill='tozeroy',
                                        fillcolor=fill_color
                                    ))
                                    
                                    # Update layout - match app style
                                    fig.update_layout(
                                        title=dict(
                                            text=f"{ticker} - Cumulative Gain/Loss Over Time",
                                            font=dict(size=18)
                                        ),
                                        xaxis_title="Date",
                                        yaxis_title="Cumulative Gain/Loss ($)",
                                        hovermode='x unified',
                                        showlegend=False,
                                        height=500,
                                        plot_bgcolor='rgba(0,0,0,0)',
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        xaxis=dict(
                                            showgrid=True,
                                            gridcolor='rgba(128, 128, 128, 0.2)',
                                            showline=True,
                                            linecolor='rgba(128, 128, 128, 0.3)'
                                        ),
                                        yaxis=dict(
                                            showgrid=True,
                                            gridcolor='rgba(128, 128, 128, 0.2)',
                                            showline=True,
                                            linecolor='rgba(128, 128, 128, 0.3)',
                                            range=[min(y_data) - abs(min(y_data) * 0.1), max(y_data) + abs(max(y_data) * 0.1)],  # 10% padding
                                            tickprefix='$',  # Add $ to all tick labels
                                            tickformat=',.0f'  # Format with commas, no decimals
                                        )
                                    )
                                    
                                    # Add zero line for reference
                                    fig.add_hline(y=0, line_dash="dash", line_color="rgba(128, 128, 128, 0.5)", opacity=0.7)
                                    
                                    # Use a unique key to force fresh render
                                    chart_key = f"portfolio_chart_{ticker}_{datetime.now().timestamp()}"
                                    st.plotly_chart(fig, use_container_width=True, key=chart_key)
                                    
                                    # Show current position summary
                                    if holding.get('current_price'):
                                        st.success(
                                            f"**Current Position:** {holding['total_quantity']:.2f} shares @ ${holding['current_price']:.2f} = "
                                            f"${holding['current_value']:,.2f} "
                                            f"({'📈 +' if holding['profit_loss'] >= 0 else '📉 '}"
                                            f"${abs(holding['profit_loss']):,.2f} / "
                                            f"{holding['profit_loss_percentage']:.2f}%)"
                                        )
                                    else:
                                        st.info(
                                            f"**Current Position:** {holding['total_quantity']:.2f} shares "
                                            f"(Cost Basis: ${holding['average_cost']:.2f}/share, "
                                            f"Total Invested: ${holding['total_invested']:,.2f})"
                                        )
                                    
                                except ImportError:
                                    st.warning("Install plotly for timeline visualization: pip install plotly")
                                    # Fallback to simple metrics
                                    if timeline_data:
                                        latest = timeline_data[-1]
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.metric("Total Invested", f"${latest['invested']:,.2f}")
                                        with col2:
                                            st.metric("Current Value", f"${latest['current_value']:,.2f}")
                                        with col3:
                                            st.metric("Cumulative Gain/Loss", f"${latest['cumulative_gain_loss']:,.2f}")
                            
                            st.markdown("---")
                            
                            # Transaction history in collapsible expander
                            with st.expander("📋 Transaction History", expanded=False):
                                if transactions_sorted:
                                    st.markdown(f"**{len(transactions_sorted)} transaction(s)**")
                                    
                                    # Initialize session state for selected transactions if not exists
                                    if f'selected_txns_{ticker}' not in st.session_state:
                                        st.session_state[f'selected_txns_{ticker}'] = []
                                    
                                    # Sorting controls
                                    sort_col1, sort_col2, sort_col3 = st.columns([2, 2, 6])
                                    with sort_col1:
                                        sort_by = st.selectbox(
                                            "Sort by",
                                            ["Date", "Type", "Quantity", "Price", "Total", "Fees"],
                                            key=f"sort_by_{ticker}"
                                        )
                                    with sort_col2:
                                        sort_order = st.selectbox(
                                            "Order",
                                            ["Descending", "Ascending"],
                                            key=f"sort_order_{ticker}"
                                        )
                                    
                                    # Apply sorting
                                    sort_key_map = {
                                        "Date": "transaction_date",
                                        "Type": "transaction_type",
                                        "Quantity": "quantity",
                                        "Price": "price_per_unit",
                                        "Total": "total_amount",
                                        "Fees": "fees"
                                    }
                                    sort_key = sort_key_map[sort_by]
                                    reverse_sort = (sort_order == "Descending")
                                    
                                    transactions_sorted = sorted(
                                        transactions_sorted,
                                        key=lambda x: x[sort_key],
                                        reverse=reverse_sort
                                    )
                                    
                                    st.markdown("---")
                                    
                                    # Bulk actions header
                                    col1, col2, col3 = st.columns([1, 1, 4])
                                    with col1:
                                        if st.button("Select All", key=f"select_all_{ticker}"):
                                            st.session_state[f'selected_txns_{ticker}'] = [txn['id'] for txn in transactions_sorted]
                                            st.rerun()
                                    with col2:
                                        if st.button("Deselect All", key=f"deselect_all_{ticker}"):
                                            st.session_state[f'selected_txns_{ticker}'] = []
                                            st.rerun()
                                    with col3:
                                        selected_count = len(st.session_state[f'selected_txns_{ticker}'])
                                        if selected_count > 0:
                                            if st.button(
                                                f"🗑️ Delete {selected_count} Selected",
                                                key=f"bulk_delete_txns_{ticker}",
                                                type="primary"
                                            ):
                                                try:
                                                    deleted_count = 0
                                                    failed_count = 0
                                                    
                                                    for txn_id in st.session_state[f'selected_txns_{ticker}']:
                                                        response = make_authenticated_request(
                                                            "DELETE",
                                                            f"/portfolio/transactions/{txn_id}"
                                                        )
                                                        
                                                        if response.status_code == 204:
                                                            deleted_count += 1
                                                        else:
                                                            failed_count += 1
                                                    
                                                    # Clear selection
                                                    st.session_state[f'selected_txns_{ticker}'] = []
                                                    
                                                    if deleted_count > 0:
                                                        st.success(f"✅ Successfully deleted {deleted_count} transaction(s)!")
                                                    if failed_count > 0:
                                                        st.error(f"❌ Failed to delete {failed_count} transaction(s)")
                                                    
                                                    st.rerun()
                                                
                                                except Exception as e:
                                                    st.error(f"Error deleting transactions: {str(e)}")
                                    
                                    st.markdown("---")
                                    
                                    # Display transactions with individual action buttons
                                    for txn in transactions_sorted:
                                        # Check if this transaction is being edited
                                        edit_key = f'edit_txn_{ticker}_{txn["id"]}'
                                        is_editing = st.session_state.get(edit_key, False)
                                        
                                        if is_editing:
                                            # Show edit form in a container
                                            with st.container():
                                                st.markdown(f"**✏️ Editing Transaction (ID: {txn['id']})**")
                                                
                                                with st.form(f"edit_form_{ticker}_{txn['id']}"):
                                                    col1, col2 = st.columns(2)
                                                    
                                                    with col1:
                                                        edit_type = st.selectbox(
                                                            "Type",
                                                            ["BUY", "SELL"],
                                                            index=0 if txn['transaction_type'] == "BUY" else 1,
                                                            key=f"edit_type_{ticker}_{txn['id']}"
                                                        )
                                                        from datetime import datetime as dt
                                                        txn_date = dt.strptime(txn['transaction_date'], "%Y-%m-%d").date() if isinstance(txn['transaction_date'], str) else txn['transaction_date']
                                                        edit_date = st.date_input(
                                                            "Date",
                                                            value=txn_date,
                                                            key=f"edit_date_{ticker}_{txn['id']}"
                                                        )
                                                        edit_quantity = st.number_input(
                                                            "Quantity",
                                                            min_value=0.0,
                                                            value=float(txn['quantity']),
                                                            step=0.01,
                                                            format="%.2f",
                                                            key=f"edit_qty_{ticker}_{txn['id']}"
                                                        )
                                                    
                                                    with col2:
                                                        edit_price = st.number_input(
                                                            "Price/Unit",
                                                            min_value=0.0,
                                                            value=float(txn['price_per_unit']),
                                                            step=0.01,
                                                            format="%.2f",
                                                            key=f"edit_price_{ticker}_{txn['id']}"
                                                        )
                                                        edit_fees = st.number_input(
                                                            "Fees",
                                                            min_value=0.0,
                                                            value=float(txn['fees']),
                                                            step=0.01,
                                                            format="%.2f",
                                                            key=f"edit_fees_{ticker}_{txn['id']}"
                                                        )
                                                        edit_total = st.number_input(
                                                            "Total",
                                                            min_value=0.0,
                                                            value=float(txn['total_amount']),
                                                            step=0.01,
                                                            format="%.2f",
                                                            key=f"edit_total_{ticker}_{txn['id']}"
                                                        )
                                                    
                                                    edit_notes = st.text_area(
                                                        "Notes",
                                                        value=txn.get('notes', ''),
                                                        key=f"edit_notes_{ticker}_{txn['id']}"
                                                    )
                                                    
                                                    col1, col2 = st.columns(2)
                                                    with col1:
                                                        save_btn = st.form_submit_button("💾 Save Changes", use_container_width=True)
                                                    with col2:
                                                        cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True)
                                                    
                                                    if save_btn:
                                                        try:
                                                            update_data = {
                                                                "transaction_type": edit_type,
                                                                "transaction_date": str(edit_date),
                                                                "quantity": edit_quantity,
                                                                "price_per_unit": edit_price,
                                                                "total_amount": edit_total,
                                                                "fees": edit_fees,
                                                                "notes": edit_notes
                                                            }
                                                            
                                                            response = make_authenticated_request(
                                                                "PUT",
                                                                f"/portfolio/transactions/{txn['id']}",
                                                                json=update_data
                                                            )
                                                            
                                                            if response.status_code == 200:
                                                                st.session_state[edit_key] = False
                                                                st.success("✅ Transaction updated!")
                                                                st.rerun()
                                                            else:
                                                                st.error(f"Failed to update: {response.text}")
                                                        except Exception as e:
                                                            st.error(f"Error: {str(e)}")
                                                    
                                                    if cancel_btn:
                                                        st.session_state[edit_key] = False
                                                        st.rerun()
                                            
                                            st.markdown("---")
                                        else:
                                            # Normal transaction display
                                            col1, col2, col3 = st.columns([0.5, 7.5, 2])
                                            
                                            with col1:
                                                is_selected = txn['id'] in st.session_state[f'selected_txns_{ticker}']
                                                if st.checkbox(
                                                    "",
                                                    value=is_selected,
                                                    key=f"txn_checkbox_{ticker}_{txn['id']}",
                                                    label_visibility="collapsed"
                                                ):
                                                    if txn['id'] not in st.session_state[f'selected_txns_{ticker}']:
                                                        st.session_state[f'selected_txns_{ticker}'].append(txn['id'])
                                                else:
                                                    if txn['id'] in st.session_state[f'selected_txns_{ticker}']:
                                                        st.session_state[f'selected_txns_{ticker}'].remove(txn['id'])
                                            
                                            with col2:
                                                # Transaction display
                                                txn_type_emoji = "🟢" if txn['transaction_type'] == "BUY" else "🔴"
                                                st.markdown(f"**{txn_type_emoji} {txn['transaction_date']}** - {txn['transaction_type']}")
                                                
                                                info_col1, info_col2, info_col3, info_col4 = st.columns(4)
                                                with info_col1:
                                                    st.caption(f"Qty: {txn['quantity']:.2f}")
                                                with info_col2:
                                                    st.caption(f"Price: ${txn['price_per_unit']:.2f}")
                                                with info_col3:
                                                    st.caption(f"Total: ${txn['total_amount']:,.2f}")
                                                with info_col4:
                                                    st.caption(f"Fees: ${txn['fees']:.2f}")
                                                
                                                if txn.get('notes'):
                                                    st.caption(f"📝 {txn['notes']}")
                                            
                                            with col3:
                                                # Action buttons
                                                btn_col1, btn_col2 = st.columns(2)
                                                with btn_col1:
                                                    if st.button("✏️", key=f"edit_btn_{ticker}_{txn['id']}", help="Edit"):
                                                        st.session_state[edit_key] = True
                                                        st.rerun()
                                                with btn_col2:
                                                    if st.button("🗑️", key=f"delete_btn_{ticker}_{txn['id']}", help="Delete"):
                                                        # Set delete confirmation state
                                                        st.session_state[f'confirm_delete_{ticker}_{txn["id"]}'] = True
                                                        st.rerun()
                                            
                                            # Show delete confirmation if needed
                                            if st.session_state.get(f'confirm_delete_{ticker}_{txn["id"]}', False):
                                                st.warning(f"⚠️ Delete this transaction?")
                                                conf_col1, conf_col2 = st.columns(2)
                                                with conf_col1:
                                                    if st.button("✅ Yes, Delete", key=f"confirm_yes_{ticker}_{txn['id']}"):
                                                        try:
                                                            response = make_authenticated_request(
                                                                "DELETE",
                                                                f"/portfolio/transactions/{txn['id']}"
                                                            )
                                                            
                                                            if response.status_code == 204:
                                                                st.session_state[f'confirm_delete_{ticker}_{txn["id"]}'] = False
                                                                st.success("✅ Transaction deleted!")
                                                                st.rerun()
                                                            else:
                                                                st.error(f"Failed to delete: {response.text}")
                                                        except Exception as e:
                                                            st.error(f"Error: {str(e)}")
                                                with conf_col2:
                                                    if st.button("❌ Cancel", key=f"confirm_no_{ticker}_{txn['id']}"):
                                                        st.session_state[f'confirm_delete_{ticker}_{txn["id"]}'] = False
                                                        st.rerun()
                                            
                                            st.markdown("---")
                                else:
                                    st.info("No transactions found.")
                        else:
                            st.info("No transactions found for this ticker.")
                    else:
                        # No current holdings (but ticker exists in transaction list)
                        st.info(f"ℹ️ No current holdings for **{ticker}** (all shares may have been sold)")
                        st.markdown("---")
                        
                        # Still show delete option for tickers with no current holdings
                        with st.expander("🗑️ Delete Ticker (Remove All Transactions)", expanded=True):
                            st.warning(f"⚠️ **Warning**: This will permanently delete ALL transactions for **{ticker}** and remove it from your portfolio.")
                            
                            # Show transaction count
                            txn_count_response = make_authenticated_request(
                                "GET",
                                "/portfolio/transactions",
                                params={"ticker": ticker}
                            )
                            
                            if txn_count_response.status_code == 200:
                                txn_count = len(txn_count_response.json())
                                st.info(f"📊 This ticker has **{txn_count}** transaction(s) that will be deleted.")
                            
                            st.markdown("---")
                            
                            # Confirmation checkbox
                            confirm_delete_ticker = st.checkbox(
                                f"I understand this will delete all {ticker} data permanently",
                                key=f"confirm_delete_ticker_noholdings_{ticker}"
                            )
                            
                            if confirm_delete_ticker:
                                if st.button(
                                    f"🗑️ DELETE ALL {ticker} TRANSACTIONS",
                                    key=f"delete_all_ticker_noholdings_{ticker}",
                                    type="primary",
                                    use_container_width=True
                                ):
                                    try:
                                        # Get all transactions for this ticker
                                        response = make_authenticated_request(
                                            "GET",
                                            "/portfolio/transactions",
                                            params={"ticker": ticker}
                                        )
                                        
                                        if response.status_code == 200:
                                            transactions_to_delete = response.json()
                                            deleted_count = 0
                                            failed_count = 0
                                            
                                            # Delete each transaction
                                            for txn in transactions_to_delete:
                                                del_response = make_authenticated_request(
                                                    "DELETE",
                                                    f"/portfolio/transactions/{txn['id']}"
                                                )
                                                
                                                if del_response.status_code == 204:
                                                    deleted_count += 1
                                                else:
                                                    failed_count += 1
                                            
                                            if deleted_count > 0:
                                                st.success(f"✅ Successfully deleted {deleted_count} transaction(s) for {ticker}!")
                                                st.info("Refreshing page...")
                                                st.rerun()
                                            else:
                                                st.error("No transactions were deleted.")
                                            
                                            if failed_count > 0:
                                                st.error(f"❌ Failed to delete {failed_count} transaction(s)")
                                        else:
                                            st.error(f"Failed to fetch transactions: {response.text}")
                                    
                                    except Exception as e:
                                        st.error(f"Error deleting ticker: {str(e)}")
        else:
            st.error(f"Failed to load tickers: {response.text}")
    
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure the backend is running.")
    except Exception as e:
        st.error(f"Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


def portfolio_allocation_page():
    """Asset allocation summary page with target vs actual comparison"""
    st.title("📊 Asset Allocation")
    st.markdown("---")
    
    try:
        # Get allocation summary
        response = make_authenticated_request("GET", "/portfolio/allocation/summary")
        
        if response.status_code == 200:
            summary = response.json()
            
            # Display total portfolio value
            st.markdown("### 💰 Total Portfolio Value")
            st.metric(
                "Current Value",
                f"${summary['total_portfolio_value']:,.2f}"
            )
            
            st.markdown("---")
            
            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["📊 Allocation Summary", "⚙️ Settings", "🏷️ Ticker Categories"])
            
            with tab1:
                st.markdown("### Asset Allocation Comparison")
                
                categories = summary['categories']
                
                if categories:
                    # Prepare data for chart and table
                    category_names = [c['category'] for c in categories]
                    target_percentages = [c['target_percentage'] for c in categories]
                    actual_percentages = [c['actual_percentage'] for c in categories]
                    differences = [c['difference'] for c in categories]
                    thresholds = [c['threshold'] for c in categories]
                    values = [c['current_value'] for c in categories]
                    needs_rebalancing = [c['needs_rebalancing'] for c in categories]
                    
                    # Horizontal Bar Chart
                    try:
                        import plotly.graph_objects as go
                        
                        fig = go.Figure()
                        
                        # Add target bars
                        fig.add_trace(go.Bar(
                            name='My Target',
                            y=category_names,
                            x=target_percentages,
                            orientation='h',
                            marker=dict(color='rgb(85, 141, 221)'),  # Blue
                            text=[f"{p:.1f}%" for p in target_percentages],
                            textposition='inside',
                            textfont=dict(color='white', size=12)
                        ))
                        
                        # Add actual bars
                        fig.add_trace(go.Bar(
                            name='Actual',
                            y=category_names,
                            x=actual_percentages,
                            orientation='h',
                            marker=dict(color='rgb(123, 196, 120)'),  # Green
                            text=[f"{p:.1f}%" for p in actual_percentages],
                            textposition='inside',
                            textfont=dict(color='white', size=12)
                        ))
                        
                        fig.update_layout(
                            title='Asset Allocation Summary',
                            title_font_size=18,
                            xaxis_title='Percentage',
                            barmode='group',
                            height=400,
                            xaxis=dict(range=[0, 100]),
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            ),
                            margin=dict(l=150, r=50, t=80, b=50)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                    except ImportError:
                        st.warning("Install plotly for visualization: pip install plotly")
                    
                    st.markdown("---")
                    
                    # Comparison Table
                    st.markdown("### Detailed Breakdown")
                    
                    # Create styled dataframe
                    try:
                        import pandas as pd
                        
                        table_data = []
                        for i, category in enumerate(categories):
                            table_data.append({
                                "Category": category['category'],
                                "My Target": f"{category['target_percentage']:.1f}%",
                                "Actual": f"{category['actual_percentage']:.1f}%",
                                "Difference": f"{category['difference']:+.2f}%",
                                "Threshold": f"{category['threshold']:.1f}%",
                                "Value": f"${category['current_value']:,.2f}",
                                "Status": "⚠️ Rebalance" if category['needs_rebalancing'] else "✅ On Track"
                            })
                        
                        df = pd.DataFrame(table_data)
                        
                        # Apply styling with better contrast for dark mode
                        def highlight_rebalancing(row):
                            if "⚠️" in str(row['Status']):
                                # Use darker red background with white text for better contrast
                                return ['background-color: #8B0000; color: #FFFFFF; font-weight: bold'] * len(row)
                            return [''] * len(row)
                        
                        styled_df = df.style.apply(highlight_rebalancing, axis=1)
                        st.dataframe(styled_df, use_container_width=True, hide_index=True)
                        
                        # Show rebalancing recommendations
                        rebalancing_needed = [c for c in categories if c['needs_rebalancing']]
                        if rebalancing_needed:
                            st.markdown("### 🔄 Rebalancing Recommendations")
                            for category in rebalancing_needed:
                                diff = category['difference']
                                value = category['current_value']
                                target_value = summary['total_portfolio_value'] * category['target_percentage'] / 100
                                amount_to_adjust = target_value - value
                                
                                if diff > 0:
                                    st.warning(
                                        f"**{category['category']}**: Over-allocated by {abs(diff):.2f}%. "
                                        f"Consider reducing by ~${abs(amount_to_adjust):,.2f}"
                                    )
                                else:
                                    st.info(
                                        f"**{category['category']}**: Under-allocated by {abs(diff):.2f}%. "
                                        f"Consider adding ~${abs(amount_to_adjust):,.2f}"
                                    )
                        else:
                            st.success("✅ Your portfolio is well-balanced! All categories are within target thresholds.")
                        
                    except ImportError:
                        # Fallback without pandas
                        for category in categories:
                            with st.expander(f"{category['category']} - {'⚠️ Rebalance' if category['needs_rebalancing'] else '✅ On Track'}"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.write(f"**Target:** {category['target_percentage']:.1f}%")
                                    st.write(f"**Actual:** {category['actual_percentage']:.1f}%")
                                with col2:
                                    st.write(f"**Difference:** {category['difference']:+.2f}%")
                                    st.write(f"**Threshold:** {category['threshold']:.1f}%")
                                with col3:
                                    st.write(f"**Value:** ${category['current_value']:,.2f}")
                
                else:
                    st.info("No allocation data available. Make sure you have holdings and targets set up.")
            
            with tab2:
                st.markdown("### ⚙️ Allocation Targets")
                st.write("Set your target allocation percentages and acceptable deviation thresholds.")
                
                # Get current targets
                targets_response = make_authenticated_request("GET", "/portfolio/allocation/targets")
                
                if targets_response.status_code == 200:
                    targets = targets_response.json()
                    
                    st.markdown("---")
                    
                    for target in targets:
                        with st.expander(f"**{target['category']}**", expanded=True):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                new_target = st.number_input(
                                    "Target %",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=float(target['target_percentage']),
                                    step=1.0,
                                    key=f"target_{target['category']}"
                                )
                            
                            with col2:
                                new_threshold = st.number_input(
                                    "Threshold %",
                                    min_value=0.0,
                                    max_value=100.0,
                                    value=float(target['threshold_percentage']),
                                    step=0.5,
                                    key=f"threshold_{target['category']}"
                                )
                            
                            if st.button(f"Update {target['category']}", key=f"update_{target['category']}"):
                                try:
                                    update_data = {
                                        "target_percentage": new_target,
                                        "threshold_percentage": new_threshold
                                    }
                                    
                                    update_response = make_authenticated_request(
                                        "PUT",
                                        f"/portfolio/allocation/targets/{target['category']}",
                                        json=update_data
                                    )
                                    
                                    if update_response.status_code == 200:
                                        st.success(f"✅ Updated {target['category']} targets!")
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to update: {update_response.text}")
                                except Exception as e:
                                    st.error(f"Error updating target: {str(e)}")
                    
                    # Validation check
                    total_target = sum(t['target_percentage'] for t in targets)
                    if abs(total_target - 100.0) > 0.01:
                        st.warning(f"⚠️ **Note:** Your targets currently add up to {total_target:.1f}%. They should total 100%.")
                    else:
                        st.success(f"✅ Your targets add up to {total_target:.1f}%")
                
                else:
                    st.error("Failed to load allocation targets.")
            
            with tab3:
                st.markdown("### 🏷️ Ticker Categorization")
                st.write("View and adjust how your tickers are categorized. Tickers are automatically categorized using market data.")
                
                # Get ticker categories
                categories_response = make_authenticated_request("GET", "/portfolio/allocation/ticker-categories")
                
                if categories_response.status_code == 200:
                    ticker_categories = categories_response.json()
                    
                    if ticker_categories:
                        st.markdown("---")
                        
                        # Sort by category
                        ticker_categories_sorted = sorted(ticker_categories, key=lambda x: (x['category'], x['ticker']))
                        
                        # Group by category
                        from itertools import groupby
                        
                        for category, tickers_in_category in groupby(ticker_categories_sorted, key=lambda x: x['category']):
                            tickers_list = list(tickers_in_category)
                            
                            with st.expander(f"**{category}** ({len(tickers_list)} tickers)", expanded=False):
                                for ticker_cat in tickers_list:
                                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                                    
                                    with col1:
                                        # Display ticker with full name if available
                                        ticker_name = ticker_cat.get('ticker_name')
                                        if ticker_name:
                                            st.write(f"**{ticker_cat['ticker']}**")
                                            st.caption(ticker_name)
                                        else:
                                            st.write(f"**{ticker_cat['ticker']}**")
                                    
                                    with col2:
                                        auto_label = "🤖 Auto" if ticker_cat['is_auto_categorized'] else "✋ Manual"
                                        st.write(auto_label)
                                    
                                    with col3:
                                        new_category = st.selectbox(
                                            "Change to:",
                                            ["US Stocks", "International Stocks", "Bonds", "Cash"],
                                            index=["US Stocks", "International Stocks", "Bonds", "Cash"].index(ticker_cat['category']),
                                            key=f"cat_select_{ticker_cat['ticker']}",
                                            label_visibility="collapsed"
                                        )
                                    
                                    with col4:
                                        if new_category != ticker_cat['category']:
                                            if st.button("Update", key=f"update_cat_{ticker_cat['ticker']}"):
                                                try:
                                                    update_data = {
                                                        "category": new_category,
                                                        "is_auto_categorized": False
                                                    }
                                                    
                                                    update_response = make_authenticated_request(
                                                        "PUT",
                                                        f"/portfolio/allocation/ticker-categories/{ticker_cat['ticker']}",
                                                        json=update_data
                                                    )
                                                    
                                                    if update_response.status_code == 200:
                                                        st.success(f"✅ Updated {ticker_cat['ticker']}!")
                                                        st.rerun()
                                                    else:
                                                        st.error(f"Failed: {update_response.text}")
                                                except Exception as e:
                                                    st.error(f"Error: {str(e)}")
                                        else:
                                            if ticker_cat['is_auto_categorized'] and st.button("Re-scan", key=f"rescan_{ticker_cat['ticker']}"):
                                                try:
                                                    rescan_response = make_authenticated_request(
                                                        "POST",
                                                        f"/portfolio/allocation/ticker-categories/recategorize/{ticker_cat['ticker']}"
                                                    )
                                                    
                                                    if rescan_response.status_code == 200:
                                                        st.success(f"✅ Re-scanned {ticker_cat['ticker']}!")
                                                        st.rerun()
                                                    else:
                                                        st.error(f"Failed: {rescan_response.text}")
                                                except Exception as e:
                                                    st.error(f"Error: {str(e)}")
                    else:
                        st.info("No ticker categories found. Add transactions to see your tickers here.")
                
                else:
                    st.error("Failed to load ticker categories.")
        
        elif response.status_code == 404:
            st.warning("⚠️ Allocation targets not set up yet. Running migration to initialize...")
            st.info("Please run the migration script: `python scripts/migrate_add_asset_allocation.py`")
            
            st.markdown("---")
            st.markdown("### Quick Setup")
            st.write("Default targets will be:")
            st.write("- **US Stocks**: 70% (±5%)")
            st.write("- **International Stocks**: 25% (±5%)")
            st.write("- **Bonds**: 0% (±0%)")
            st.write("- **Cash**: 5% (±1%)")
        
        else:
            st.error(f"Failed to load allocation summary: {response.text}")
    
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure the backend is running.")
    except Exception as e:
        st.error(f"Error loading allocation: {str(e)}")
        import traceback
        st.code(traceback.format_exc())


# ============================================================================
# WORKOUT TRACKER PAGES
# ============================================================================

def log_workout_page():
    """Log a workout session"""
    st.title("💪 Log Workout")
    st.markdown("---")
    
    try:
        # Get workout templates
        templates_response = make_authenticated_request("GET", "/workouts/templates")
        
        if templates_response.status_code == 200:
            templates = templates_response.json()
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Workout selection
                workout_options = ["Custom Workout"] + [t["name"] for t in templates]
                selected_workout = st.selectbox("Select Workout", workout_options)
                
                workout_id = None
                exercises_list = []
                
                if selected_workout != "Custom Workout":
                    # Get workout details
                    workout = next(t for t in templates if t["name"] == selected_workout)
                    workout_id = workout["id"]
                    
                    # Get full workout details with exercises
                    workout_details_response = make_authenticated_request("GET", f"/workouts/templates/{workout_id}")
                    if workout_details_response.status_code == 200:
                        workout_details = workout_details_response.json()
                        exercises_list = workout_details.get("exercises", [])
                        
                        st.info(f"**{selected_workout}** includes {len(exercises_list)} exercises")
                        
                        # Show last workout performance if available
                        try:
                            last_workout_response = make_authenticated_request("GET", f"/workouts/records/{workout_id}/last")
                            if last_workout_response.status_code == 200:
                                last_workout = last_workout_response.json()
                                with st.expander("📊 View Last Workout Performance"):
                                    st.caption(f"Last performed: {datetime.fromisoformat(last_workout['workout_date']).strftime('%B %d, %Y at %I:%M %p')}")
                                    for ex_record in last_workout.get("exercises", []):
                                        st.write(f"**{ex_record['exercise_name']}**: {ex_record.get('sets', '-')} sets × {ex_record.get('reps', '-')} reps @ {ex_record.get('weight', '-')} lbs")
                        except:
                            pass
            
            with col2:
                workout_date = st.date_input("Workout Date", value=date.today())
                workout_time = st.time_input("Workout Time", value=datetime.now().time())
                duration = st.number_input("Duration (minutes)", min_value=0, value=60)
            
            st.markdown("---")
            
            # Exercise logging
            st.subheader("📝 Log Exercises")
            
            # Get all exercises for selection
            all_exercises_response = make_authenticated_request("GET", "/workouts/exercises")
            if all_exercises_response.status_code == 200:
                all_exercises = all_exercises_response.json()
                
                # Initialize session state for exercise records
                if "workout_exercises" not in st.session_state:
                    st.session_state.workout_exercises = []
                
                # Track the currently selected workout to detect changes
                if "current_workout" not in st.session_state:
                    st.session_state.current_workout = None
                
                # Check if workout selection has changed
                if st.session_state.current_workout != selected_workout:
                    st.session_state.current_workout = selected_workout
                    st.session_state.workout_exercises = []
                    
                    # Pre-populate with workout template exercises if any
                    if exercises_list:
                        for ex in exercises_list:
                            st.session_state.workout_exercises.append({
                                "exercise_id": ex["exercise_id"],
                                "exercise_name": ex["exercise_name"],
                                "sets": 3,
                                "reps": 10,
                                "weight": 0.0
                            })
                
                # Display current exercises
                for idx, ex_record in enumerate(st.session_state.workout_exercises):
                    with st.container():
                        col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
                        
                        with col1:
                            st.write(f"**{ex_record['exercise_name']}**")
                        with col2:
                            sets = st.number_input("Sets", min_value=1, value=ex_record.get("sets", 3), key=f"sets_{idx}")
                            st.session_state.workout_exercises[idx]["sets"] = sets
                        with col3:
                            reps = st.number_input("Reps", min_value=1, value=ex_record.get("reps", 10), key=f"reps_{idx}")
                            st.session_state.workout_exercises[idx]["reps"] = reps
                        with col4:
                            weight = st.number_input("Weight (lbs)", min_value=0.0, value=float(ex_record.get("weight", 0)), step=2.5, key=f"weight_{idx}")
                            st.session_state.workout_exercises[idx]["weight"] = weight
                        with col5:
                            st.write("")  # Spacing
                            st.write("")  # Spacing
                            if st.button("❌", key=f"remove_{idx}"):
                                st.session_state.workout_exercises.pop(idx)
                                st.rerun()
                
                # Add exercise button
                st.markdown("---")
                col1, col2 = st.columns([3, 1])
                with col1:
                    exercise_to_add = st.selectbox(
                        "Add Exercise",
                        options=all_exercises,
                        format_func=lambda x: f"{x['name']} ({x.get('primary_muscle', 'N/A')})",
                        key="exercise_select"
                    )
                with col2:
                    st.write("")  # Spacing
                    st.write("")  # Spacing
                    if st.button("➕ Add"):
                        st.session_state.workout_exercises.append({
                            "exercise_id": exercise_to_add["id"],
                            "exercise_name": exercise_to_add["name"],
                            "sets": 3,
                            "reps": 10,
                            "weight": 0.0
                        })
                        st.rerun()
                
                # Submit workout
                st.markdown("---")
                notes = st.text_area("Workout Notes (optional)")
                
                if st.button("💾 Save Workout", type="primary", use_container_width=True):
                    if len(st.session_state.workout_exercises) == 0:
                        st.error("Please add at least one exercise!")
                    else:
                        try:
                            workout_datetime = datetime.combine(workout_date, workout_time)
                            
                            workout_data = {
                                "workout_id": workout_id,
                                "workout_name": selected_workout,
                                "workout_date": workout_datetime.isoformat(),
                                "duration_minutes": duration,
                                "notes": notes if notes else None,
                                "exercises": [
                                    {
                                        "exercise_id": ex["exercise_id"],
                                        "sets": ex["sets"],
                                        "reps": ex["reps"],
                                        "weight": ex["weight"],
                                        "weight_unit": "lbs"
                                    }
                                    for ex in st.session_state.workout_exercises
                                ]
                            }
                            
                            response = make_authenticated_request("POST", "/workouts/records", json=workout_data)
                            
                            if response.status_code == 201:
                                st.success("✅ Workout logged successfully!")
                                # Clear session state to reset the form
                                st.session_state.workout_exercises = []
                                st.session_state.current_workout = None
                                st.balloons()
                                # Small delay before rerun to show success message
                                import time
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Failed to log workout: {response.text}")
                        
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
        else:
            st.error("Failed to load workout templates")
    
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure the backend is running.")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def workout_history_page():
    """View workout history"""
    st.title("📅 Workout History")
    st.markdown("---")
    
    try:
        # Date range filter
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("From", value=date.today() - timedelta(days=90))
        with col2:
            end_date = st.date_input("To", value=date.today())
        with col3:
            st.write("")  # Spacing
            st.write("")  # Spacing
            if st.button("🔄 Refresh"):
                st.rerun()
        
        # Get workout records
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        response = make_authenticated_request("GET", "/workouts/records", params=params)
        
        if response.status_code == 200:
            records = response.json()
            
            if records:
                st.success(f"Found {len(records)} workouts")
                
                for record in records:
                    workout_date = datetime.fromisoformat(record["workout_date"])
                    
                    with st.expander(f"**{record['workout_name']}** - {workout_date.strftime('%B %d, %Y at %I:%M %p')}"):
                        if record.get("duration_minutes"):
                            st.caption(f"Duration: {record['duration_minutes']} minutes")
                        
                        if record.get("notes"):
                            st.info(f"Notes: {record['notes']}")
                        
                        st.markdown("### Exercises")
                        for ex_record in record.get("exercises", []):
                            col1, col2 = st.columns([3, 2])
                            with col1:
                                st.write(f"**{ex_record['exercise_name']}**")
                            with col2:
                                if ex_record.get("sets") and ex_record.get("reps") and ex_record.get("weight"):
                                    st.write(f"{ex_record['sets']} × {ex_record['reps']} @ {ex_record['weight']} lbs")
                                elif ex_record.get("time_seconds"):
                                    st.write(f"{ex_record['time_seconds']//60} min")
                        
                        # Delete button
                        if st.button(f"🗑️ Delete Workout", key=f"delete_{record['id']}"):
                            delete_response = make_authenticated_request("DELETE", f"/workouts/records/{record['id']}")
                            if delete_response.status_code == 204:
                                st.success("Workout deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete workout")
            else:
                st.info("No workouts found in the selected date range.")
        
        else:
            st.error(f"Failed to load workout history: {response.text}")
    
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure the backend is running.")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def exercises_page():
    """Manage exercises"""
    st.title("🏋️ Exercise Library")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["View Exercises", "Add Exercise"])
    
    with tab1:
        st.subheader("Your Exercises")
        
        # Search and filter
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("Search exercises", placeholder="Enter exercise name...")
        with col2:
            muscle_filter = st.selectbox("Filter by muscle", ["All", "Chest", "Back", "Legs", "Shoulders", "Arms", "Core", "Glutes", "Upper Back"])
        
        try:
            params = {}
            if search_term:
                params["search"] = search_term
            if muscle_filter != "All":
                params["muscle"] = muscle_filter
            
            response = make_authenticated_request("GET", "/workouts/exercises", params=params)
            
            if response.status_code == 200:
                exercises = response.json()
                
                if exercises:
                    st.success(f"Found {len(exercises)} exercises")
                    
                    # Display exercises in a grid
                    for exercise in exercises:
                        with st.container():
                            # Use expander to show exercise details
                            with st.expander(f"**{exercise['name']}** ({exercise.get('primary_muscle', 'N/A')})", expanded=False):
                                col1, col2 = st.columns([1, 2])
                                
                                with col1:
                                    # Display exercise GIF/image
                                    if exercise.get("image_url"):
                                        try:
                                            st.image(exercise['image_url'], width=300, caption=exercise['name'])
                                        except:
                                            st.info("🖼️ Image available (click to view)")
                                            st.caption(f"[View Image]({exercise['image_url']})")
                                    else:
                                        st.warning("⚠️ No image available")
                                
                                with col2:
                                    st.markdown("### Details")
                                    
                                    if exercise.get("primary_muscle"):
                                        st.write(f"**Primary Muscle:** {exercise['primary_muscle']}")
                                    
                                    if exercise.get("secondary_muscles"):
                                        st.write(f"**Secondary Muscles:** {exercise['secondary_muscles']}")
                                    
                                    if exercise.get("notes"):
                                        st.markdown("**Notes:**")
                                        st.write(exercise["notes"])
                                    
                                    # Action buttons
                                    col_edit, col_delete = st.columns(2)
                                    
                                    with col_edit:
                                        if st.button("✏️ Edit", key=f"edit_ex_{exercise['id']}", use_container_width=True):
                                            st.session_state[f"editing_exercise_{exercise['id']}"] = True
                                            st.rerun()
                                    
                                    with col_delete:
                                        if st.button("🗑️ Delete", key=f"delete_ex_{exercise['id']}", use_container_width=True):
                                            delete_response = make_authenticated_request("DELETE", f"/workouts/exercises/{exercise['id']}")
                                            if delete_response.status_code == 204:
                                                st.success("Exercise deleted!")
                                                st.rerun()
                                            else:
                                                st.error("Failed to delete")
                                
                                # Edit form (shown inline when edit button is clicked)
                                if st.session_state.get(f"editing_exercise_{exercise['id']}", False):
                                    st.markdown("---")
                                    with st.form(key=f"edit_form_{exercise['id']}"):
                                        st.markdown("### Edit Exercise")
                                        edit_name = st.text_input("Name", value=exercise['name'], key=f"edit_name_{exercise['id']}")
                                        edit_primary = st.selectbox(
                                            "Primary Muscle",
                                            ["", "Chest", "Back", "Legs", "Shoulders", "Arms", "Core", "Glutes", "Upper Back", "Lower Back", "Hamstrings", "Quadriceps", "Calves", "Biceps", "Triceps", "Forearms"],
                                            index=(["", "Chest", "Back", "Legs", "Shoulders", "Arms", "Core", "Glutes", "Upper Back", "Lower Back", "Hamstrings", "Quadriceps", "Calves", "Biceps", "Triceps", "Forearms"].index(exercise.get('primary_muscle', '')) if exercise.get('primary_muscle') in ["", "Chest", "Back", "Legs", "Shoulders", "Arms", "Core", "Glutes", "Upper Back", "Lower Back", "Hamstrings", "Quadriceps", "Calves", "Biceps", "Triceps", "Forearms"] else 0),
                                            key=f"edit_primary_{exercise['id']}"
                                        )
                                        
                                        # Image upload or URL
                                        st.markdown("**Exercise Image/GIF:**")
                                        image_option = st.radio("Choose image source:", ["Keep current", "Upload new image", "Enter URL"], key=f"img_option_{exercise['id']}", horizontal=True)
                                        
                                        uploaded_image = None
                                        edit_image_url = exercise.get('image_url', '')
                                        
                                        if image_option == "Upload new image":
                                            uploaded_image = st.file_uploader("Upload Image/GIF", type=['png', 'jpg', 'jpeg', 'gif', 'webp'], key=f"upload_img_{exercise['id']}")
                                            if uploaded_image:
                                                st.image(uploaded_image, width=200, caption="Preview")
                                        elif image_option == "Enter URL":
                                            edit_image_url = st.text_input("Image URL", value=exercise.get('image_url', ''), placeholder="https://example.com/exercise.gif", key=f"edit_image_{exercise['id']}")
                                        
                                        edit_notes = st.text_area("Notes", value=exercise.get('notes', ''), key=f"edit_notes_{exercise['id']}")
                                        
                                        col_save, col_cancel = st.columns(2)
                                        with col_save:
                                            save_button = st.form_submit_button("💾 Save", type="primary", use_container_width=True)
                                        with col_cancel:
                                            cancel_button = st.form_submit_button("❌ Cancel", use_container_width=True)
                                        
                                        if save_button:
                                            # Handle image upload
                                            final_image_url = edit_image_url
                                            if uploaded_image is not None:
                                                file_bytes = uploaded_image.read()
                                                file_base64 = base64.b64encode(file_bytes).decode('utf-8')
                                                file_extension = uploaded_image.name.split('.')[-1].lower()
                                                mime_types = {
                                                    'png': 'image/png',
                                                    'jpg': 'image/jpeg',
                                                    'jpeg': 'image/jpeg',
                                                    'gif': 'image/gif',
                                                    'webp': 'image/webp'
                                                }
                                                mime_type = mime_types.get(file_extension, 'image/jpeg')
                                                final_image_url = f"data:{mime_type};base64,{file_base64}"
                                            
                                            update_data = {
                                                "name": edit_name,
                                                "primary_muscle": edit_primary if edit_primary else None,
                                                "notes": edit_notes if edit_notes else None,
                                                "image_url": final_image_url if final_image_url else None
                                            }
                                            
                                            update_response = make_authenticated_request("PUT", f"/workouts/exercises/{exercise['id']}", json=update_data)
                                            
                                            if update_response.status_code == 200:
                                                st.success("✅ Exercise updated!")
                                                st.session_state[f"editing_exercise_{exercise['id']}"] = False
                                                st.rerun()
                                            else:
                                                st.error(f"Failed to update: {update_response.text}")
                                        
                                        if cancel_button:
                                            st.session_state[f"editing_exercise_{exercise['id']}"] = False
                                            st.rerun()
                else:
                    st.info("No exercises found. Add some exercises to get started!")
            
            else:
                st.error(f"Failed to load exercises: {response.text}")
        
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API. Make sure the backend is running.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with tab2:
        st.subheader("Add New Exercise")
        
        with st.form("add_exercise_form"):
            name = st.text_input("Exercise Name*", placeholder="e.g., Barbell Squat")
            primary_muscle = st.selectbox("Primary Muscle Group", ["", "Chest", "Back", "Legs", "Shoulders", "Arms", "Core", "Glutes", "Upper Back", "Lower Back", "Hamstrings", "Quadriceps", "Calves", "Biceps", "Triceps", "Forearms"])
            secondary_muscles = st.text_input("Secondary Muscles (comma-separated)", placeholder="e.g., Core, Lower Back")
            notes = st.text_area("Notes / Form Cues", placeholder="Tips for proper form...")
            
            # Image upload
            st.markdown("**Exercise Image/GIF (optional):**")
            uploaded_file = st.file_uploader("Upload an image or GIF", type=['png', 'jpg', 'jpeg', 'gif', 'webp'], key="new_exercise_image")
            if uploaded_file:
                st.image(uploaded_file, width=200, caption="Preview")
            
            submitted = st.form_submit_button("Add Exercise", type="primary", use_container_width=True)
            
            if submitted:
                if not name:
                    st.error("Please enter an exercise name")
                else:
                    try:
                        # Handle image upload
                        image_url = None
                        if uploaded_file is not None:
                            file_bytes = uploaded_file.read()
                            file_base64 = base64.b64encode(file_bytes).decode('utf-8')
                            file_extension = uploaded_file.name.split('.')[-1].lower()
                            mime_types = {
                                'png': 'image/png',
                                'jpg': 'image/jpeg',
                                'jpeg': 'image/jpeg',
                                'gif': 'image/gif',
                                'webp': 'image/webp'
                            }
                            mime_type = mime_types.get(file_extension, 'image/jpeg')
                            image_url = f"data:{mime_type};base64,{file_base64}"
                        
                        exercise_data = {
                            "name": name,
                            "primary_muscle": primary_muscle if primary_muscle else None,
                            "secondary_muscles": secondary_muscles if secondary_muscles else None,
                            "notes": notes if notes else None,
                            "image_url": image_url
                        }
                        
                        response = make_authenticated_request("POST", "/workouts/exercises", json=exercise_data)
                        
                        if response.status_code == 201:
                            st.success(f"✅ Exercise '{name}' added successfully!")
                            st.rerun()
                        elif response.status_code == 400:
                            st.error(f"Exercise already exists: {response.json().get('detail', '')}")
                        else:
                            st.error(f"Failed to add exercise: {response.text}")
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")


def workout_templates_page():
    """Manage workout templates"""
    st.title("📋 Workout Templates")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["View Workouts", "Create Workout"])
    
    with tab1:
        st.subheader("Your Workout Templates")
        
        try:
            response = make_authenticated_request("GET", "/workouts/templates")
            
            if response.status_code == 200:
                workouts = response.json()
                
                if workouts:
                    # Initialize edit mode tracking in session state
                    if "editing_workout_id" not in st.session_state:
                        st.session_state.editing_workout_id = None
                    
                    for workout in workouts:
                        # Get full workout details
                        details_response = make_authenticated_request("GET", f"/workouts/templates/{workout['id']}")
                        if details_response.status_code == 200:
                            workout_details = details_response.json()
                            
                            # Check if this workout is being edited
                            is_editing = st.session_state.editing_workout_id == workout['id']
                            
                            with st.expander(f"**{workout['name']}** ({len(workout_details.get('exercises', []))} exercises)", expanded=is_editing):
                                if not is_editing:
                                    # View mode
                                    if workout.get("description"):
                                        st.info(workout["description"])
                                    
                                    st.markdown("### Exercises")
                                    for ex in workout_details.get("exercises", []):
                                        st.write(f"- {ex['exercise_name']} ({ex.get('primary_muscle', 'N/A')})")
                                    
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button(f"✏️ Edit", key=f"edit_workout_{workout['id']}"):
                                            st.session_state.editing_workout_id = workout['id']
                                            st.rerun()
                                    with col2:
                                        if st.button(f"🗑️ Delete", key=f"delete_workout_{workout['id']}"):
                                            delete_response = make_authenticated_request("DELETE", f"/workouts/templates/{workout['id']}")
                                            if delete_response.status_code == 204:
                                                st.success("Workout template deleted!")
                                                st.rerun()
                                            else:
                                                st.error("Failed to delete")
                                
                                else:
                                    # Edit mode
                                    st.markdown("### Edit Workout")
                                    
                                    # Get all exercises for selection
                                    exercises_response = make_authenticated_request("GET", "/workouts/exercises")
                                    if exercises_response.status_code == 200:
                                        all_exercises = exercises_response.json()
                                        
                                        # Edit form
                                        edit_name = st.text_input(
                                            "Workout Name*",
                                            value=workout['name'],
                                            key=f"edit_name_{workout['id']}"
                                        )
                                        
                                        edit_description = st.text_area(
                                            "Description (optional)",
                                            value=workout.get('description', ''),
                                            key=f"edit_desc_{workout['id']}"
                                        )
                                        
                                        st.markdown("### Edit Exercises")
                                        
                                        # Get currently selected exercise IDs
                                        current_exercise_ids = [ex['exercise_id'] for ex in workout_details.get('exercises', [])]
                                        
                                        # Pre-select current exercises
                                        default_exercises = [ex for ex in all_exercises if ex['id'] in current_exercise_ids]
                                        
                                        selected_exercises = st.multiselect(
                                            "Choose exercises for this workout",
                                            options=all_exercises,
                                            default=default_exercises,
                                            format_func=lambda x: f"{x['name']} ({x.get('primary_muscle', 'N/A')})",
                                            key=f"edit_exercises_{workout['id']}"
                                        )
                                        
                                        # Action buttons
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            if st.button("💾 Save Changes", type="primary", key=f"save_workout_{workout['id']}"):
                                                if not edit_name:
                                                    st.error("Please enter a workout name")
                                                elif len(selected_exercises) == 0:
                                                    st.error("Please select at least one exercise")
                                                else:
                                                    try:
                                                        update_data = {
                                                            "name": edit_name,
                                                            "description": edit_description if edit_description else None,
                                                            "exercise_ids": [ex["id"] for ex in selected_exercises]
                                                        }
                                                        
                                                        update_response = make_authenticated_request(
                                                            "PUT",
                                                            f"/workouts/templates/{workout['id']}",
                                                            json=update_data
                                                        )
                                                        
                                                        if update_response.status_code == 200:
                                                            st.success(f"✅ Workout '{edit_name}' updated successfully!")
                                                            st.session_state.editing_workout_id = None
                                                            st.rerun()
                                                        elif update_response.status_code == 400:
                                                            st.error(f"Error: {update_response.json().get('detail', '')}")
                                                        else:
                                                            st.error(f"Failed to update workout: {update_response.text}")
                                                    
                                                    except Exception as e:
                                                        st.error(f"Error: {str(e)}")
                                        
                                        with col2:
                                            if st.button("❌ Cancel", key=f"cancel_edit_{workout['id']}"):
                                                st.session_state.editing_workout_id = None
                                                st.rerun()
                else:
                    st.info("No workout templates found. Create one to get started!")
            
            else:
                st.error(f"Failed to load workouts: {response.text}")
        
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API. Make sure the backend is running.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with tab2:
        st.subheader("Create New Workout Template")
        
        # Get all exercises
        try:
            exercises_response = make_authenticated_request("GET", "/workouts/exercises")
            
            if exercises_response.status_code == 200:
                all_exercises = exercises_response.json()
                
                name = st.text_input("Workout Name*", placeholder="e.g., Upper Body Push")
                description = st.text_area("Description (optional)", placeholder="Workout notes...")
                
                st.markdown("### Select Exercises")
                selected_exercises = st.multiselect(
                    "Choose exercises for this workout",
                    options=all_exercises,
                    format_func=lambda x: f"{x['name']} ({x.get('primary_muscle', 'N/A')})"
                )
                
                if st.button("Create Workout", type="primary", use_container_width=True):
                    if not name:
                        st.error("Please enter a workout name")
                    elif len(selected_exercises) == 0:
                        st.error("Please select at least one exercise")
                    else:
                        try:
                            workout_data = {
                                "name": name,
                                "description": description if description else None,
                                "exercise_ids": [ex["id"] for ex in selected_exercises]
                            }
                            
                            response = make_authenticated_request("POST", "/workouts/templates", json=workout_data)
                            
                            if response.status_code == 201:
                                st.success(f"✅ Workout '{name}' created successfully!")
                                st.rerun()
                            elif response.status_code == 400:
                                st.error(f"Workout already exists: {response.json().get('detail', '')}")
                            else:
                                st.error(f"Failed to create workout: {response.text}")
                        
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            
            else:
                st.error("Failed to load exercises")
        
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to API. Make sure the backend is running.")
        except Exception as e:
            st.error(f"Error: {str(e)}")


def workout_progress_page():
    """View progress for specific exercises"""
    st.title("📈 Exercise Progress")
    st.markdown("---")
    
    try:
        # Get all exercises
        exercises_response = make_authenticated_request("GET", "/workouts/exercises")
        
        if exercises_response.status_code == 200:
            exercises = exercises_response.json()
            
            if exercises:
                selected_exercise = st.selectbox(
                    "Select Exercise",
                    options=exercises,
                    format_func=lambda x: f"{x['name']} ({x.get('primary_muscle', 'N/A')})"
                )
                
                # Date range
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("From", value=date.today() - timedelta(days=90))
                with col2:
                    end_date = st.date_input("To", value=date.today())
                
                # Get progress data
                params = {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
                
                progress_response = make_authenticated_request(
                    "GET",
                    f"/workouts/exercises/{selected_exercise['id']}/progress",
                    params=params
                )
                
                if progress_response.status_code == 200:
                    progress = progress_response.json()
                    
                    # Display PRs
                    st.markdown("### 🏆 Personal Records")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        pr_weight = progress.get("personal_record_weight")
                        st.metric("Max Weight", f"{pr_weight:.1f} lbs" if pr_weight else "N/A")
                    with col2:
                        pr_reps = progress.get("personal_record_reps")
                        st.metric("Max Reps", f"{pr_reps}" if pr_reps else "N/A")
                    with col3:
                        pr_volume = progress.get("personal_record_volume")
                        st.metric("Max Volume", f"{pr_volume:.0f}" if pr_volume else "N/A")
                    
                    # History table
                    st.markdown("### 📊 History")
                    history = progress.get("history", [])
                    
                    if history:
                        import pandas as pd
                        
                        # Create DataFrame
                        df = pd.DataFrame([
                            {
                                "Date": datetime.fromisoformat(h["date"]).strftime("%Y-%m-%d"),
                                "Sets": h.get("sets", "-"),
                                "Reps": h.get("reps", "-"),
                                "Weight": f"{h.get('weight', '-')} lbs" if h.get("weight") else "-",
                                "Volume": f"{h.get('volume', '-'):.0f}" if h.get("volume") else "-",
                                "Est. 1RM": f"{h.get('one_rep_max', '-'):.1f} lbs" if h.get("one_rep_max") else "-"
                            }
                            for h in history
                        ])
                        
                        st.dataframe(df, use_container_width=True)
                        
                        # Charts with plotly
                        try:
                            import plotly.graph_objects as go
                            
                            dates = [datetime.fromisoformat(h["date"]) for h in history]
                            weights = [h.get("weight") for h in history if h.get("weight")]
                            volumes = [h.get("volume") for h in history if h.get("volume")]
                            
                            if weights and len(weights) > 1:
                                st.markdown("### 📉 Weight Progression")
                                fig = go.Figure()
                                fig.add_trace(go.Scatter(
                                    x=[datetime.fromisoformat(h["date"]) for h in history if h.get("weight")],
                                    y=weights,
                                    mode='lines+markers',
                                    name='Weight'
                                ))
                                fig.update_layout(xaxis_title="Date", yaxis_title="Weight (lbs)")
                                st.plotly_chart(fig, use_container_width=True)
                            
                            if volumes and len(volumes) > 1:
                                st.markdown("### 📉 Volume Progression")
                                fig = go.Figure()
                                fig.add_trace(go.Scatter(
                                    x=[datetime.fromisoformat(h["date"]) for h in history if h.get("volume")],
                                    y=volumes,
                                    mode='lines+markers',
                                    name='Volume',
                                    line=dict(color='green')
                                ))
                                fig.update_layout(xaxis_title="Date", yaxis_title="Volume (sets × reps × weight)")
                                st.plotly_chart(fig, use_container_width=True)
                        
                        except ImportError:
                            st.info("Install plotly for charts: pip install plotly")
                    
                    else:
                        st.info("No history found for this exercise in the selected date range.")
                
                else:
                    st.error(f"Failed to load progress: {progress_response.text}")
            
            else:
                st.info("No exercises found. Add some exercises first!")
        
        else:
            st.error("Failed to load exercises")
    
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure the backend is running.")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def workout_analytics_page():
    """Workout analytics and insights"""
    st.title("📊 Workout Analytics")
    st.markdown("---")
    
    try:
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From", value=date.today() - timedelta(days=90))
        with col2:
            end_date = st.date_input("To", value=date.today())
        
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        # Get analytics summary
        analytics_response = make_authenticated_request("GET", "/workouts/analytics/summary", params=params)
        
        if analytics_response.status_code == 200:
            analytics = analytics_response.json()
            
            # Key metrics
            st.markdown("### 📈 Key Metrics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Workouts", analytics.get("total_workouts", 0))
            with col2:
                st.metric("Exercises Logged", analytics.get("total_exercises_logged", 0))
            with col3:
                st.metric("Unique Exercises", analytics.get("unique_exercises", 0))
            with col4:
                total_volume = analytics.get("total_volume", 0)
                st.metric("Total Volume", f"{total_volume:,.0f} lbs")
            
            st.markdown("---")
            
            # Most frequent exercises
            st.markdown("### 🏆 Most Frequent Exercises")
            most_frequent = analytics.get("most_frequent_exercises", [])
            
            if most_frequent:
                import pandas as pd
                df = pd.DataFrame(most_frequent)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No data available yet.")
            
            # Workout frequency by month
            st.markdown("### 📅 Workout Frequency by Month")
            frequency_data = analytics.get("workout_frequency_by_month", [])
            
            if frequency_data:
                try:
                    import plotly.graph_objects as go
                    
                    months = [d["month"] for d in frequency_data]
                    counts = [d["count"] for d in frequency_data]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Bar(x=months, y=counts, name="Workouts"))
                    fig.update_layout(xaxis_title="Month", yaxis_title="Number of Workouts")
                    st.plotly_chart(fig, use_container_width=True)
                
                except ImportError:
                    st.info("Install plotly for charts")
            else:
                st.info("No data available yet.")
            
            # Muscle group distribution
            st.markdown("### 💪 Muscle Group Distribution")
            muscle_dist = analytics.get("muscle_group_distribution", {})
            
            if muscle_dist:
                try:
                    import plotly.graph_objects as go
                    
                    labels = list(muscle_dist.keys())
                    values = list(muscle_dist.values())
                    
                    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
                    fig.update_layout(title="Exercises by Muscle Group")
                    st.plotly_chart(fig, use_container_width=True)
                
                except ImportError:
                    st.info("Install plotly for charts")
            else:
                st.info("No data available yet.")
            
            # Personal records
            st.markdown("---")
            st.markdown("### 🏅 Personal Records")
            
            prs_response = make_authenticated_request("GET", "/workouts/analytics/personal-records")
            
            if prs_response.status_code == 200:
                prs = prs_response.json()
                
                if prs:
                    import pandas as pd
                    
                    df = pd.DataFrame([
                        {
                            "Exercise": pr["exercise_name"],
                            "Muscle": pr.get("primary_muscle", "N/A"),
                            "Max Weight": f"{pr.get('max_weight', 0):.1f} lbs" if pr.get("max_weight") else "-",
                            "Max Reps": pr.get("max_reps", "-"),
                            "Max Volume": f"{pr.get('max_volume', 0):.0f}" if pr.get("max_volume") else "-"
                        }
                        for pr in prs
                    ])
                    
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No personal records yet. Start logging workouts!")
        
        else:
            st.error(f"Failed to load analytics: {analytics_response.text}")
    
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure the backend is running.")
    except Exception as e:
        st.error(f"Error: {str(e)}")


# Main app logic
main_app()


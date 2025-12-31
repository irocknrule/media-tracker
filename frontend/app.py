import streamlit as st
import requests
from datetime import date, datetime
from typing import Optional
from collections import defaultdict
import json
import base64

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Personal Media Tracker",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# Try to restore session from query params (for page refresh)
# Streamlit's session state persists during the browser session but not across full refreshes
# So we use URL query parameters as a bridge
if not st.session_state.authenticated:
    token = None
    try:
        # Use experimental API (available in Streamlit 1.28.1)
        if hasattr(st, 'experimental_get_query_params'):
            params = st.experimental_get_query_params()
            # Debug: Check what we got
            # st.write(f"Debug - Query params: {params}")
            if params and "token" in params:
                token_list = params["token"]
                if isinstance(token_list, list) and len(token_list) > 0:
                    token = token_list[0]
                elif isinstance(token_list, str):
                    token = token_list
    except Exception as e:
        # Silently fail - user will need to log in
        pass
    
    if token:
        # Validate token by checking if it's still valid
        try:
            response = requests.get(
                f"{API_BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5
            )
            if response.status_code == 200:
                st.session_state.access_token = token
                st.session_state.authenticated = True
                # Keep token in URL for future refreshes - don't clear it here!
                # Only clear it when user explicitly logs out
                # Rerun to update the UI
                st.rerun()
            else:
                # Token invalid - clear it from URL
                try:
                    if hasattr(st, 'experimental_set_query_params'):
                        st.experimental_set_query_params()
                except:
                    pass
        except Exception as e:
            # Token validation failed - clear it from URL
            try:
                if hasattr(st, 'experimental_set_query_params'):
                    st.experimental_set_query_params()
            except:
                pass


def make_authenticated_request(method: str, endpoint: str, **kwargs):
    """Make an authenticated API request"""
    headers = kwargs.get("headers", {})
    if st.session_state.access_token:
        headers["Authorization"] = f"Bearer {st.session_state.access_token}"
    kwargs["headers"] = headers
    
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


def login_page():
    """Login page"""
    st.title("🔐 Login")
    st.markdown("---")
    
    with st.form("login_form"):
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password", value="admin123")
        submit = st.form_submit_button("Login")
        
        if submit:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/auth/login",
                    params={"username": username, "password": password}
                )
                if response.status_code == 200:
                    data = response.json()
                    token = data["access_token"]
                    st.session_state.access_token = token
                    st.session_state.authenticated = True
                    # Store token in URL for persistence across refreshes
                    # Use JavaScript to directly set it in the URL (more reliable)
                    st.markdown(f"""
                    <script>
                    // Add token to URL for persistence across page refreshes
                    const url = new URL(window.location);
                    url.searchParams.set('token', '{token}');
                    window.history.replaceState({{}}, '', url);
                    </script>
                    """, unsafe_allow_html=True)
                    
                    # Also try Streamlit's method as backup
                    try:
                        if hasattr(st, 'experimental_set_query_params'):
                            st.experimental_set_query_params(**{"token": [token]})
                    except:
                        pass
                    
                    st.success("Login successful! Your session will persist across page refreshes.")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API. Make sure the backend is running on http://localhost:8000")


def logout():
    """Logout function"""
    if st.session_state.access_token:
        try:
            make_authenticated_request(
                "POST",
                "/auth/logout",
                params={"token": st.session_state.access_token}
            )
        except:
            pass
    st.session_state.access_token = None
    st.session_state.authenticated = False
    # Clear token from localStorage
    clear_token_script = """
    <script>
    window.localStorage.removeItem('media_tracker_token');
    </script>
    """
    st.markdown(clear_token_script, unsafe_allow_html=True)
    # Clear token from query params if available
    try:
        if hasattr(st, 'experimental_set_query_params'):
            st.experimental_set_query_params()
        elif hasattr(st, 'query_params') and "token" in st.query_params:
            del st.query_params["token"]
    except:
        pass
    st.rerun()


def main_app():
    """Main application"""
    # Sidebar
    with st.sidebar:
        st.title("📚 Media Tracker")
        st.markdown("---")
        
        if st.button("🚪 Logout"):
            logout()
        
        st.markdown("---")
        st.markdown("### Navigation")
        page = st.radio(
            "Go to",
            ["Movies", "TV Shows", "Books", "Music", "Manual Entry", "Analytics"],
            label_visibility="collapsed"
        )
    
    # Main content
    if page == "Movies":
        movies_page()
    elif page == "TV Shows":
        tv_shows_page()
    elif page == "Books":
        books_page()
    elif page == "Music":
        music_page()
    elif page == "Manual Entry":
        manual_entry_page()
    elif page == "Analytics":
        analytics_page()


def movies_page():
    """Movies tracking page"""
    st.title("🎬 Movies")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["View Movies", "Add Movie"])
    
    with tab1:
        st.subheader("Your Movies")
        year_filter = st.selectbox("Filter by Year", ["All"] + list(range(2020, date.today().year + 2)), key="movie_year")
        
        try:
            params = {}
            if year_filter != "All":
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
        
        # Check session state for selected result
        if "movie_selected_result" in st.session_state:
            selected_result = st.session_state["movie_selected_result"]
            default_title = selected_result.get("title", "")
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
            watched_date = st.date_input("Watched Date *", value=date.today())
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
                        "watched_date": str(watched_date),
                        "rating": float(rating) if rating else None,
                        "notes": notes if notes else None
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
    """TV Shows tracking page"""
    st.title("📺 TV Shows")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["View TV Shows", "Add TV Show"])
    
    with tab1:
        st.subheader("Your TV Shows")
        year_filter = st.selectbox("Filter by Year", ["All"] + list(range(2020, date.today().year + 2)), key="tv_year")
        
        try:
            params = {}
            if year_filter != "All":
                params["year"] = year_filter
            
            response = make_authenticated_request("GET", "/tv-shows/", params=params)
            if response.status_code == 200:
                tv_shows = response.json()
                
                if tv_shows:
                    # Group TV shows by title
                    shows_dict = defaultdict(list)
                    for tv_show in tv_shows:
                        shows_dict[tv_show['title']].append(tv_show)
                    
                    # Display grouped TV shows
                    st.markdown("### Your TV Shows")
                    cols_per_row = 4
                    show_titles = sorted(shows_dict.keys())
                    
                    for i in range(0, len(show_titles), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j, show_title in enumerate(show_titles[i:i+cols_per_row]):
                            with cols[j]:
                                seasons_list = shows_dict[show_title]
                                # Get the first season's thumbnail (or fetch one)
                                first_season = seasons_list[0]
                                thumbnail_url = first_season.get("thumbnail_url")
                                
                                # If no thumbnail in DB, try to fetch it from TVMaze and save it
                                if not thumbnail_url or not thumbnail_url.strip() or thumbnail_url == "N/A":
                                    cache_key = f"tv_thumbnail_fetch_{show_title}"
                                    if cache_key not in st.session_state:
                                        try:
                                            fetched_thumbnail = get_tv_show_thumbnail(show_title)
                                            if fetched_thumbnail:
                                                # Update all seasons for this show with the thumbnail
                                                for season in seasons_list:
                                                    try:
                                                        update_data = {"thumbnail_url": fetched_thumbnail}
                                                        make_authenticated_request(
                                                            "PUT", 
                                                            f"/tv-shows/{season.get('id')}", 
                                                            json=update_data
                                                        )
                                                    except:
                                                        pass
                                                thumbnail_url = fetched_thumbnail
                                                st.session_state[cache_key] = fetched_thumbnail
                                            else:
                                                st.session_state[cache_key] = None
                                        except:
                                            st.session_state[cache_key] = None
                                    elif st.session_state[cache_key]:
                                        thumbnail_url = st.session_state[cache_key]
                                
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
                                        f'<div style="width:100%;height:250px;background:#f0f0f0;display:flex;align-items:center;justify-content:center;border-radius:8px;font-size:48px;margin-bottom:10px;">📺</div>', 
                                        unsafe_allow_html=True
                                    )
                                
                                # Show title
                                st.write(f"**{show_title}**")
                                
                                # Count seasons and get date range
                                season_count = len(seasons_list)
                                season_numbers = sorted([s.get('season') for s in seasons_list if s.get('season')])
                                dates = sorted([s.get('watched_date') for s in seasons_list if s.get('watched_date')])
                                
                                # Show season count
                                if season_count == 1:
                                    st.caption(f"1 season watched")
                                else:
                                    st.caption(f"{season_count} seasons watched")
                                
                                # Show season numbers
                                if season_numbers:
                                    season_str = ", ".join([f"S{sn}" for sn in season_numbers])
                                    st.caption(f"Seasons: {season_str}")
                                
                                # Show date range
                                if dates:
                                    if len(dates) == 1:
                                        st.caption(f"Watched: {dates[0]}")
                                    else:
                                        st.caption(f"Dates: {dates[0]} to {dates[-1]}")
                    
                    # Details section below
                    st.markdown("---")
                    st.markdown("### Season Details")
                    
                    for show_title in sorted(shows_dict.keys()):
                        seasons_list = shows_dict[show_title]
                        with st.expander(f"**{show_title}** - {len(seasons_list)} season{'s' if len(seasons_list) != 1 else ''}"):
                            for season in sorted(seasons_list, key=lambda x: x.get('season', 0) or 0):
                                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                                with col1:
                                    season_num = season.get('season', '?')
                                    st.write(f"**Season {season_num}**")
                                with col2:
                                    st.write(f"Watched: {season.get('watched_date', 'N/A')}")
                                with col3:
                                    rating = season.get('rating')
                                    st.write(f"Rating: {rating}/10" if rating else "Rating: N/A")
                                with col4:
                                    if st.button("Delete", key=f"delete_tv_{season['id']}"):
                                        delete_response = make_authenticated_request("DELETE", f"/tv-shows/{season['id']}")
                                        if delete_response.status_code == 204:
                                            st.success("Season deleted!")
                                            st.rerun()
                                
                                if season.get('notes'):
                                    st.caption(f"Notes: {season['notes']}")
                                
                                if season != seasons_list[-1]:
                                    st.markdown("---")
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
                                episode_count = season.get("episode_count", 0)
                                if episode_count > 0:
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
                            watched_date = st.date_input("Watched Date *", value=date.today(), key="tv_date")
                            rating = st.slider("Rating (0-10)", 0.0, 10.0, 5.0, 0.5, key="tv_rating")
                            notes = st.text_area("Notes", placeholder="Optional notes", key="tv_notes")
                            
                            submit = st.form_submit_button("Add TV Show")
                            
                            if submit:
                                if not title:
                                    st.error("Title is required!")
                                else:
                                    data = {
                                        "title": title,
                                        "season": int(season) if season else None,
                                        "watched_date": str(watched_date),
                                        "rating": float(rating) if rating else None,
                                        "notes": notes if notes else None,
                                        "thumbnail_url": selected_season.get("image", "") if selected_season.get("image") else None
                                    }
                                    try:
                                        response = make_authenticated_request("POST", "/tv-shows/", json=data)
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
                                            st.success("TV Show added successfully!")
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
                    watched_date = st.date_input("Watched Date *", value=date.today(), key="tv_date_fallback")
                    rating = st.slider("Rating (0-10)", 0.0, 10.0, 5.0, 0.5, key="tv_rating_fallback")
                    notes = st.text_area("Notes", placeholder="Optional notes", key="tv_notes_fallback")
                    
                    submit = st.form_submit_button("Add TV Show")
                    
                    if submit:
                        if not title:
                            st.error("Title is required!")
                        else:
                            data = {
                                "title": title,
                                "season": int(season) if season else None,
                                "watched_date": str(watched_date),
                                "rating": float(rating) if rating else None,
                                "notes": notes if notes else None
                            }
                            try:
                                response = make_authenticated_request("POST", "/tv-shows/", json=data)
                                if response.status_code == 201:
                                    if "tv_selected_result" in st.session_state:
                                        del st.session_state["tv_selected_result"]
                                    st.success("TV Show added successfully!")
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
                watched_date = st.date_input("Watched Date *", value=date.today(), key="tv_date")
                rating = st.slider("Rating (0-10)", 0.0, 10.0, 5.0, 0.5, key="tv_rating")
                notes = st.text_area("Notes", placeholder="Optional notes", key="tv_notes")
                
                submit = st.form_submit_button("Add TV Show")
                
                if submit:
                    if not title:
                        st.error("Title is required!")
                    else:
                        data = {
                            "title": title,
                            "season": int(season) if season else None,
                            "watched_date": str(watched_date),
                            "rating": float(rating) if rating else None,
                            "notes": notes if notes else None
                        }
                        try:
                            response = make_authenticated_request("POST", "/tv-shows/", json=data)
                            if response.status_code == 201:
                                st.success("TV Show added successfully!")
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
        year_filter = st.selectbox("Filter by Year", ["All"] + list(range(2020, date.today().year + 2)), key="book_year")
        
        try:
            params = {}
            if year_filter != "All":
                params["year"] = year_filter
            
            response = make_authenticated_request("GET", "/books/", params=params)
            if response.status_code == 200:
                books = response.json()
                
                if books:
                    # Display books in grid layout
                    st.markdown("### Your Books")
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
        if "book_selected_result" in st.session_state:
            selected_result = st.session_state["book_selected_result"]
            default_title = selected_result.get("title", "")
            default_author = selected_result.get("author", "")
        
        with st.form("add_book_form"):
            title = st.text_input("Title *", value=default_title, placeholder="Book title")
            author = st.text_input("Author", value=default_author, placeholder="Author name")
            finished_date = st.date_input("Finished Date *", value=date.today(), key="book_date")
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
                        "finished_date": str(finished_date),
                        "rating": float(rating) if rating else None,
                        "notes": notes if notes else None
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
        year_filter = st.selectbox("Filter by Year", ["All"] + list(range(2020, date.today().year + 2)), key="music_year")
        
        try:
            params = {}
            if year_filter != "All":
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
        if "music_selected_result" in st.session_state:
            selected_result = st.session_state["music_selected_result"]
            default_title = selected_result.get("title", "")
            default_artist = selected_result.get("artist", "")
        
        with st.form("add_music_form"):
            title = st.text_input("Title *", value=default_title, placeholder="Song/Album/Band name")
            artist = st.text_input("Artist/Band", value=default_artist, placeholder="Artist or band name")
            album = st.text_input("Album", placeholder="Album name (if applicable)")
            listened_date = st.date_input("Listened Date *", value=date.today(), key="music_date")
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
                        "listened_date": str(listened_date),
                        "rating": float(rating) if rating else None,
                        "notes": notes if notes else None
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
            watched_date = st.date_input("Watched Date *", value=date.today())
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
                        "watched_date": str(watched_date),
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
        with st.form("manual_tv_form"):
            st.subheader("TV Show Details")
            title = st.text_input("Title *", placeholder="TV Show title")
            season = st.number_input("Season", min_value=1, value=1)
            watched_date = st.date_input("Watched Date *", value=date.today(), key="manual_tv_date")
            rating = st.slider("Rating (0-10)", 0.0, 10.0, 5.0, 0.5, key="manual_tv_rating")
            notes = st.text_area("Notes", placeholder="Optional notes", key="manual_tv_notes")
            
            st.markdown("---")
            st.subheader("Thumbnail (Optional)")
            uploaded_file = st.file_uploader(
                "Upload thumbnail image",
                type=["png", "jpg", "jpeg", "gif", "webp"],
                key="manual_tv_thumbnail"
            )
            
            thumbnail_url = None
            file_bytes = None
            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                st.image(file_bytes, width=200, caption="Thumbnail Preview")
            
            submit = st.form_submit_button("Add TV Show")
            
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
                        "season": int(season) if season else None,
                        "watched_date": str(watched_date),
                        "rating": float(rating) if rating else None,
                        "notes": notes if notes else None,
                        "thumbnail_url": thumbnail_url
                    }
                    try:
                        response = make_authenticated_request("POST", "/tv-shows/", json=data)
                        if response.status_code == 201:
                            st.success("TV Show added successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to add TV show: {response.text}")
                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to API. Make sure the backend is running.")
    
    elif media_type == "Book":
        with st.form("manual_book_form"):
            st.subheader("Book Details")
            title = st.text_input("Title *", placeholder="Book title")
            author = st.text_input("Author", placeholder="Author name")
            finished_date = st.date_input("Finished Date *", value=date.today(), key="manual_book_date")
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
                        "finished_date": str(finished_date),
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
            listened_date = st.date_input("Listened Date *", value=date.today(), key="manual_music_date")
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
                        "listened_date": str(listened_date),
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
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Year Summary")
                selected_year = st.selectbox("Select Year", available_years)
                
                if selected_year:
                    summary_response = make_authenticated_request("GET", f"/analytics/year/{selected_year}")
                    if summary_response.status_code == 200:
                        summary = summary_response.json()
                        
                        st.metric("Movies", summary["movies_count"])
                        st.metric("TV Shows", summary["tv_shows_count"])
                        st.metric("Books", summary["books_count"])
                        st.metric("Music", summary["music_count"])
                        
                        st.markdown("### Average Ratings")
                        if summary.get("avg_movie_rating"):
                            st.write(f"**Movies:** {summary['avg_movie_rating']:.2f}/10")
                        if summary.get("avg_tv_rating"):
                            st.write(f"**TV Shows:** {summary['avg_tv_rating']:.2f}/10")
                        if summary.get("avg_book_rating"):
                            st.write(f"**Books:** {summary['avg_book_rating']:.2f}/10")
                        if summary.get("avg_music_rating"):
                            st.write(f"**Music:** {summary['avg_music_rating']:.2f}/10")
            
            with col2:
                st.subheader("Year Comparison")
                if len(available_years) >= 2:
                    year1 = st.selectbox("Year 1", available_years, key="year1")
                    year2 = st.selectbox("Year 2", available_years, key="year2", index=1 if len(available_years) > 1 else 0)
                    
                    if year1 and year2 and year1 != year2:
                        compare_response = make_authenticated_request("GET", f"/analytics/compare/{year1}/{year2}")
                        if compare_response.status_code == 200:
                            comparison = compare_response.json()
                            
                            st.write(f"**{year1} vs {year2}**")
                            st.metric("Movies Change", f"{comparison['movies_change']:.1f}%")
                            st.metric("TV Shows Change", f"{comparison['tv_shows_change']:.1f}%")
                            st.metric("Books Change", f"{comparison['books_change']:.1f}%")
                            st.metric("Music Change", f"{comparison['music_change']:.1f}%")
                else:
                    st.info("Need at least 2 years of data to compare")
        else:
            st.error("Failed to load analytics data")
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure the backend is running.")


# Main app logic
if not st.session_state.authenticated:
    login_page()
else:
    main_app()


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


def main_app():
    """Main application"""
    # Sidebar
    with st.sidebar:
        st.title("📚 Media Tracker")
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
    """TV Shows tracking page - Plex-style with show and season posters"""
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
                    # Display TV shows in grid layout with show posters
                    st.markdown("### Your TV Shows")
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
                            
                            submit = st.form_submit_button("Add TV Show Season")
                            
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
                    watched_date = st.date_input("Watched Date *", value=date.today(), key="tv_date_fallback")
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
                                "watched_date": str(watched_date),
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
                watched_date = st.date_input("Watched Date *", value=date.today(), key="tv_date")
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
                            "watched_date": str(watched_date),
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
        if "book_selected_result" in st.session_state:
            selected_result = st.session_state["book_selected_result"]
            default_title = selected_result.get("title", "")
            default_author = selected_result.get("author", "")
        
        with st.form("add_book_form"):
            title = st.text_input("Title *", value=default_title, placeholder="Book title")
            author = st.text_input("Author", value=default_author, placeholder="Author name")
            pages = st.number_input("Number of Pages", min_value=1, value=None, step=1, key="book_pages", help="Optional: Enter the total number of pages")
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
                        "pages": int(pages) if pages else None,
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
                watched_date = st.date_input("Watched Date *", value=date.today(), key="manual_tv_watched_date")
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
                            "watched_date": str(watched_date),
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
                        "pages": int(pages) if pages else None,
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
                selected_year = st.selectbox("Select Year", available_years, key="analytics_year")
                media_type = st.selectbox(
                    "Select Media Type",
                    ["Movies", "TV Shows", "Books", "Music"],
                    key="analytics_media_type"
                )
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


# Main app logic
main_app()


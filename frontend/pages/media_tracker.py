"""Media tracker pages for Movies, TV Shows, Books, Music, and Manual Entry."""
import streamlit as st
import requests
from datetime import date
from collections import defaultdict
import base64

from utils import make_authenticated_request, search_media, display_search_results, get_tv_show_seasons
from helpers import get_year_filter

def movies_page():
    """Movies tracking page"""
    st.title("🎬 Movies")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["View Movies", "Add Movie"])
    
    with tab1:
        st.subheader("Your Movies")
        # Get year filter using helper function
        year_filter = get_year_filter("movie_year")
        
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
        # Get year filter using helper function
        year_filter = get_year_filter("tv_year")
        
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
        # Get year filter using helper function
        year_filter = get_year_filter("book_year")
        
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
        # Get year filter using helper function
        year_filter = get_year_filter("music_year")
        
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



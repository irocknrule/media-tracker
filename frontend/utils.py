"""Utility functions for the Streamlit frontend application."""
import streamlit as st
import requests
import os

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


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


def display_media_thumbnail(thumbnail_url, placeholder_emoji="📷", width="100%", max_height="350px"):
    """Display a media thumbnail with fallback options"""
    image_displayed = False
    
    if thumbnail_url and thumbnail_url.strip() and thumbnail_url != "N/A":
        # Check if it's a valid HTTP URL
        if thumbnail_url.startswith("http://") or thumbnail_url.startswith("https://"):
            # Method 1: Try HTML img tag (works better with external URLs)
            try:
                st.markdown(
                    f'<img src="{thumbnail_url}" width="{width}" style="max-height: {max_height}; border-radius: 8px; object-fit: cover;">', 
                    unsafe_allow_html=True
                )
                image_displayed = True
            except:
                pass
            
            # Method 2: Fallback to st.image if HTML fails
            if not image_displayed:
                try:
                    st.image(thumbnail_url, use_container_width=True)
                    image_displayed = True
                except:
                    pass
        
        # Method 3: Check if it's base64 encoded
        elif thumbnail_url.startswith("data:image"):
            try:
                st.image(thumbnail_url, use_container_width=True)
                image_displayed = True
            except:
                pass
    
    # If all methods failed or no thumbnail, show placeholder
    if not image_displayed:
        st.markdown(f"<div style='text-align: center; font-size: 4em;'>{placeholder_emoji}</div>", unsafe_allow_html=True)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from backend.database import get_db
from backend.models import User
from backend.routers.auth import get_current_user
import requests
import os
import re
from urllib.parse import quote

router = APIRouter(prefix="/search", tags=["search"])

# API Keys (can be set via environment variables)
OMDB_API_KEY = os.getenv("OMDB_API_KEY", "free")  # Free tier available
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")


class SearchResult:
    """Search result model"""
    def __init__(self, title: str, year: Optional[str] = None, 
                 thumbnail: Optional[str] = None, description: Optional[str] = None,
                 **kwargs):
        self.title = title
        self.year = year
        self.thumbnail = thumbnail
        self.description = description
        self.extra_data = kwargs


@router.get("/movies")
def search_movies(
    query: str,
    current_user: User = Depends(get_current_user)
):
    """Search for movies using OMDB API"""
    try:
        # OMDB API requires a valid API key - if not set, use a fallback
        if OMDB_API_KEY == "free" or not OMDB_API_KEY:
            # Return empty results if no API key
            return {"results": []}
        
        # URL encode the query
        encoded_query = quote(query)
        url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={encoded_query}&type=movie"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("Response") == "False":
            return {"results": []}
        
        results = []
        for item in data.get("Search", [])[:5]:  # Limit to top 5 results
            # Use poster from search result directly (faster)
            poster = item.get("Poster", "")
            if poster and poster != "N/A":
                thumbnail = poster
            else:
                # Try to get detailed info for thumbnail
                try:
                    detail_url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={item.get('imdbID')}"
                    detail_response = requests.get(detail_url, timeout=5)
                    if detail_response.status_code == 200:
                        detail_data = detail_response.json()
                        thumbnail = detail_data.get("Poster", "")
                    else:
                        thumbnail = ""
                except:
                    thumbnail = ""
            
            results.append({
                "title": item.get("Title", ""),
                "year": item.get("Year", ""),
                "thumbnail": thumbnail if thumbnail and thumbnail != "N/A" else "",
                "description": "",
                "imdb_id": item.get("imdbID", ""),
                "type": "movie"
            })
        
        return {"results": results}
    except Exception as e:
        # Fallback: return empty results on error
        return {"results": []}


@router.get("/tv-shows")
def search_tv_shows(
    query: str,
    current_user: User = Depends(get_current_user)
):
    """Search for TV shows using TVMaze API (free, no API key needed)"""
    try:
        encoded_query = quote(query)
        url = f"https://api.tvmaze.com/search/shows?q={encoded_query}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data[:5]:  # Limit to top 5 results
            show = item.get("show", {})
            # Clean HTML from summary
            summary = show.get("summary", "")
            if summary:
                summary = re.sub('<[^<]+?>', '', summary)
                summary = summary[:200]
            
            # Get thumbnail - TVMaze API structure
            thumbnail = ""
            image_data = show.get("image")
            if image_data:
                # image_data is typically a dict with medium/original keys
                if isinstance(image_data, dict):
                    # Prefer medium size (smaller, faster to load)
                    thumbnail = image_data.get("medium", "")
                    # Fallback to original if medium not available
                    if not thumbnail:
                        thumbnail = image_data.get("original", "")
                # Or it might be a string URL directly (unlikely but handle it)
                elif isinstance(image_data, str):
                    thumbnail = image_data
            
            # Debug: Log if no thumbnail found (can be removed later)
            if not thumbnail:
                import logging
                logging.debug(f"No thumbnail for show: {show.get('name', 'Unknown')}")
            
            results.append({
                "title": show.get("name", ""),
                "year": show.get("premiered", "")[:4] if show.get("premiered") else "",
                "thumbnail": thumbnail,
                "description": summary,
                "tvmaze_id": show.get("id", ""),
                "type": "tv_show"
            })
        
        return {"results": results}
    except Exception as e:
        return {"results": []}


@router.get("/tv-shows/thumbnail")
def get_tv_show_thumbnail(
    title: str,
    current_user: User = Depends(get_current_user)
):
    """Get thumbnail URL for a TV show by title"""
    try:
        encoded_query = quote(title)
        url = f"https://api.tvmaze.com/search/shows?q={encoded_query}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data and len(data) > 0:
            # Get the first result (most likely match)
            show = data[0].get("show", {})
            image_data = show.get("image")
            if image_data:
                if isinstance(image_data, dict):
                    thumbnail = image_data.get("medium", "") or image_data.get("original", "")
                elif isinstance(image_data, str):
                    thumbnail = image_data
                else:
                    thumbnail = ""
            else:
                thumbnail = ""
            
            return {"thumbnail_url": thumbnail if thumbnail else None}
        else:
            return {"thumbnail_url": None}
    except Exception as e:
        return {"thumbnail_url": None}


@router.get("/tv-shows/{tvmaze_id}/seasons")
def get_tv_show_seasons(
    tvmaze_id: int,
    current_user: User = Depends(get_current_user)
):
    """Get all seasons for a TV show using TVMaze API"""
    try:
        # First, get the show info to get the show image as fallback
        show_url = f"https://api.tvmaze.com/shows/{tvmaze_id}"
        show_response = requests.get(show_url, timeout=10)
        show_image = ""
        if show_response.status_code == 200:
            show_data = show_response.json()
            show_image_data = show_data.get("image")
            if show_image_data:
                if isinstance(show_image_data, dict):
                    show_image = show_image_data.get("medium", "") or show_image_data.get("original", "")
                elif isinstance(show_image_data, str):
                    show_image = show_image_data
        
        # Get seasons
        url = f"https://api.tvmaze.com/shows/{tvmaze_id}/seasons"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        seasons = []
        for season in data:
            # TVMaze doesn't provide season images, so we'll try to get the first episode's image
            # or fall back to the show image
            image_url = ""
            season_id = season.get("id")
            
            # Try to get first episode image for this season
            if season_id:
                try:
                    episodes_url = f"https://api.tvmaze.com/seasons/{season_id}/episodes"
                    episodes_response = requests.get(episodes_url, timeout=5)
                    if episodes_response.status_code == 200:
                        episodes_data = episodes_response.json()
                        if episodes_data and len(episodes_data) > 0:
                            # Get image from first episode
                            first_episode = episodes_data[0]
                            episode_image_data = first_episode.get("image")
                            if episode_image_data:
                                if isinstance(episode_image_data, dict):
                                    image_url = episode_image_data.get("medium", "") or episode_image_data.get("original", "")
                                elif isinstance(episode_image_data, str):
                                    image_url = episode_image_data
                except:
                    pass  # If episode fetch fails, continue to fallback
            
            # Fallback to show image if no episode image found
            if not image_url and show_image:
                image_url = show_image
            
            seasons.append({
                "number": season.get("number", 0),
                "name": season.get("name", f"Season {season.get('number', 0)}"),
                "episode_count": season.get("episodeOrder", 0),
                "premiere_date": season.get("premiereDate", ""),
                "end_date": season.get("endDate", ""),
                "summary": re.sub('<[^<]+?>', '', season.get("summary", ""))[:200] if season.get("summary") else "",
                "image": image_url
            })
        
        return {"seasons": seasons}
    except Exception as e:
        return {"seasons": []}


@router.get("/books")
def search_books(
    query: str,
    current_user: User = Depends(get_current_user)
):
    """Search for books using Open Library API (free, no API key needed)"""
    try:
        encoded_query = quote(query)
        url = f"https://openlibrary.org/search.json?q={encoded_query}&limit=5"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for item in data.get("docs", [])[:5]:
            # Get cover image
            cover_id = item.get("cover_i")
            thumbnail = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ""
            
            # Get author
            authors = item.get("author_name", [])
            author = authors[0] if authors else ""
            
            results.append({
                "title": item.get("title", ""),
                "author": author,
                "year": str(item.get("first_publish_year", "")) if item.get("first_publish_year") else "",
                "thumbnail": thumbnail,
                "description": "",
                "isbn": item.get("isbn", [""])[0] if item.get("isbn") else "",
                "type": "book"
            })
        
        return {"results": results}
    except Exception as e:
        return {"results": []}


@router.get("/music")
def search_music(
    query: str,
    current_user: User = Depends(get_current_user)
):
    """Search for music using Last.fm API (free, API key recommended but not required for basic search)"""
    try:
        # Last.fm API (free, 5 requests/second)
        api_key = os.getenv("LASTFM_API_KEY", "b25b959554ed76058ac220b7b2e0a026")  # Public demo key
        encoded_query = quote(query)
        url = f"http://ws.audioscrobbler.com/2.0/?method=track.search&track={encoded_query}&api_key={api_key}&format=json&limit=5"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        results = []
        tracks = data.get("results", {}).get("trackmatches", {}).get("track", [])
        
        if not isinstance(tracks, list):
            tracks = [tracks] if tracks else []
        
        for item in tracks[:5]:
            # Get album art
            artist = item.get("artist", "")
            track = item.get("name", "")
            
            # Try to get album art from Last.fm (simplified - skip if too slow)
            thumbnail = ""
            try:
                encoded_artist = quote(artist)
                encoded_track = quote(track)
                album_url = f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={api_key}&artist={encoded_artist}&track={encoded_track}&format=json"
                album_response = requests.get(album_url, timeout=5)
                if album_response.status_code == 200:
                    album_data = album_response.json()
                    album_images = album_data.get("track", {}).get("album", {}).get("image", [])
                    if album_images:
                        # Get medium size image
                        for img in album_images:
                            if img.get("@size") == "medium":
                                thumbnail = img.get("#text", "")
                                break
                        if not thumbnail and album_images:
                            thumbnail = album_images[0].get("#text", "")
            except:
                pass  # Skip thumbnail if it fails
            
            results.append({
                "title": track,
                "artist": artist,
                "thumbnail": thumbnail,
                "description": "",
                "type": "music"
            })
        
        return {"results": results}
    except Exception as e:
        return {"results": []}


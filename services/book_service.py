"""
Book Service for CapyRead - Handles book recommendations using OpenLibrary API
"""

import requests
from typing import List, Dict, Optional
import time
import logging

logger = logging.getLogger(__name__)

class BookService:
    """Service for book recommendations and search using OpenLibrary API"""
    
    def __init__(self):
        self.base_url = "https://openlibrary.org"
        
    def search_books(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for books using OpenLibrary search API."""
        url = f"{self.base_url}/search.json"
        params = {
            "q": query,
            "limit": limit,
            "fields": "title,author_name,first_publish_year,cover_i,key,ratings_average,description"
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            books = []
            for book in data.get("docs", []):
                # Get more details about the book
                book_details = self.get_book_details(book.get("key", ""))
                
                books.append({
                    "title": book.get("title", "Unknown Title"),
                    "author": ", ".join(book.get("author_name", ["Unknown Author"])),
                    "year": book.get("first_publish_year", "N/A"),
                    "rating": book.get("ratings_average", 0) or 4.0,  # Default to 4.0 if no rating
                    "cover_id": book.get("cover_i"),
                    "description": book_details.get("description", "No description available."),
                    "link": f"https://openlibrary.org{book.get('key', '')}"
                })
                
                # Add small delay to avoid rate limiting
                time.sleep(0.1)
                
            logger.info(f"Found {len(books)} books for query: {query}")
            return books
            
        except Exception as e:
            logger.error(f"Error searching books: {str(e)}")
            return []
            
    def get_book_details(self, book_key: str) -> Dict:
        """Get detailed information about a book."""
        if not book_key:
            return {}
            
        url = f"{self.base_url}{book_key}.json"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            # Extract description from different possible fields
            description = data.get("description", "")
            if isinstance(description, dict):
                description = description.get("value", "")
                
            return {
                "description": description[:500] if description else "No description available."
            }
            
        except Exception as e:
            logger.error(f"Error getting book details for {book_key}: {str(e)}")
            return {}
            
    def get_books_by_genre(self, genre: str, min_rating: float = 4.0, limit: int = 5) -> List[Dict]:
        """Get book recommendations based on genre."""
        # Construct a search query that includes the genre
        query = f"subject:{genre}"
        books = self.search_books(query, limit * 2)  # Get more to filter by rating
        
        # Filter by rating if specified
        if min_rating > 0:
            books = [book for book in books if book["rating"] >= min_rating]
            
        return books[:limit]
        
    def get_cover_url(self, cover_id: Optional[int], size: str = "M") -> str:
        """Get the URL for a book cover image."""
        if cover_id:
            return f"https://covers.openlibrary.org/b/id/{cover_id}-{size}.jpg"
        return "https://via.placeholder.com/150x220?text=No+Cover"
    
    def get_trending_books(self, limit: int = 5) -> List[Dict]:
        """Get trending/popular books"""
        # Search for highly rated books in popular genres
        genres = ["fiction", "mystery", "romance", "science fiction", "fantasy"]
        all_books = []
        
        for genre in genres:
            books = self.get_books_by_genre(genre, min_rating=4.2, limit=2)
            all_books.extend(books)
            
        # Sort by rating and return top books
        all_books.sort(key=lambda x: x["rating"], reverse=True)
        return all_books[:limit] 
    
if __name__ == "__main__":
    book_service = BookService()
    print(book_service.get_trending_books())
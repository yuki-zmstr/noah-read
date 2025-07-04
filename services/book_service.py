"""
Book Service for Noah - Handles book recommendations using OpenLibrary API
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
        self.google_books_url = "https://www.googleapis.com/books/v1/volumes"

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
                
                if "ratings_average" in book:
                    rating = str(book.get("ratings_average")) + "/5"
                else:
                    rating = "N/A"
                

                books.append({
                    "title": book.get("title", "Unknown Title"),
                    "author": ", ".join(book.get("author_name", ["Unknown Author"])),
                    "year": book.get("first_publish_year", "N/A"),
                    # Default to 4.0 if no rating
                    "rating": rating,
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
            logger.error(
                f"Error getting book details for {book_key}: {str(e)}")
            return {}

    def search_books_google(self, query: str = "", author: str = "", limit: int = 5) -> List[Dict]:
        """Search for books using Google Books API with keyword and author support."""
        search_terms = []
        
        if query:
            search_terms.append(query.replace(" ", "+"))
        
        if author:
            search_terms.append(f"inauthor:{author}")
        
        if not search_terms:
            return []
        
        search_query = "+".join(search_terms)
        
        params = {
            "q": search_query,
            "maxResults": limit,
            "printType": "books"
        }
        
        try:
            response = requests.get(self.google_books_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            books = []
            for item in data.get("items", []):
                volume_info = item.get("volumeInfo", {})
                
                authors = volume_info.get("authors", ["Unknown Author"])
                author_str = ", ".join(authors)
                
                description = volume_info.get("description", "No description available.")
                if len(description) > 500:
                    description = description[:500] + "..."
                
                if "averageRating" in volume_info:
                    rating = str(volume_info.get("averageRating")) + "/5"
                else:
                    rating = "N/A"
                
                image_links = volume_info.get("imageLinks", {})
                cover_url = image_links.get("thumbnail", "")
                
                books.append({
                    "title": volume_info.get("title", "Unknown Title"),
                    "author": author_str,
                    "year": volume_info.get("publishedDate", "N/A")[:4] if volume_info.get("publishedDate") else "N/A",
                    "rating": rating,
                    "cover_url": cover_url,
                    "description": description,
                    "link": volume_info.get("infoLink", "")
                })
            
            logger.info(f"Found {len(books)} books from Google Books for query: {search_query}")
            return books
            
        except Exception as e:
            logger.error(f"Error searching Google Books: {str(e)}")
            return []

    def get_books_by_genre(self, genre: str, limit: int = 5) -> List[Dict]:
        """Get book recommendations based on genre."""
        # Construct a search query that includes the genre
        query = f"subject:{genre}"
        books = self.search_books(query, limit)

        return books[:limit]
    
    def get_books_by_author(self, author: str, limit: int = 5) -> List[Dict]:
        """Get book recommendations based on author."""
        # Construct a search query that includes the author
        query = f"author:{author}"
        books = self.search_books(query, limit)

        return books[:limit]

    # def search_books_combined(self, query: str = "", author: str = "", limit: int = 5) -> List[Dict]:
    #     """Search for books using both OpenLibrary and Google Books APIs."""
    #     all_books = []
        
    #     # Search OpenLibrary
    #     if query and author:
    #         ol_query = f"{query} author:{author}"
    #     elif query:
    #         ol_query = query
    #     elif author:
    #         ol_query = f"author:{author}"
    #     else:
    #         ol_query = ""
        
    #     if ol_query:
    #         ol_books = self.search_books(ol_query, limit // 2)
    #         for book in ol_books:
    #             book["source"] = "OpenLibrary"
    #         all_books.extend(ol_books)
        
    #     # Search Google Books
    #     google_books = self.search_books_google(query, author, limit // 2)
    #     for book in google_books:
    #         book["source"] = "Google Books"
    #     all_books.extend(google_books)
        
    #     # Remove duplicates based on title and author similarity
    #     unique_books = []
    #     seen_titles = set()
        
    #     for book in all_books:
    #         title_key = book["title"].lower().strip()
    #         if title_key not in seen_titles:
    #             seen_titles.add(title_key)
    #             unique_books.append(book)
        
    #     return unique_books[:limit]


if __name__ == "__main__":
    pass
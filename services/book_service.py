import os
from typing import List, Dict
import requests
from goodreads_api_client import Client
from dotenv import load_dotenv

load_dotenv()

class BookService:
    def __init__(self):
        self.client = Client(api_key=os.getenv('GOODREADS_API_KEY'))
        
    def get_book_recommendations(self, genres: List[str] = None, min_rating: float = 4.0) -> List[Dict]:
        """
        Get book recommendations based on genres and minimum rating.
        
        Args:
            genres: List of genres to filter by
            min_rating: Minimum rating threshold
            
        Returns:
            List of recommended books with their details
        """
        recommendations = []
        
        try:
            # Search for books in specified genres
            for genre in genres or ['fiction']:  # Default to fiction if no genres specified
                search_results = self.client.search.books(q=genre)
                
                for book in search_results:
                    if float(book.average_rating) >= min_rating:
                        recommendations.append({
                            'title': book.title,
                            'author': book.author,
                            'rating': book.average_rating,
                            'description': book.description,
                            'link': f"https://www.goodreads.com/book/show/{book.id}",
                            'genre': genre
                        })
                        
                        if len(recommendations) >= 5:  # Limit to 5 recommendations per genre
                            break
                            
        except Exception as e:
            print(f"Error fetching book recommendations: {str(e)}")
            return []
            
        return recommendations
        
    def get_book_details(self, book_id: str) -> Dict:
        """
        Get detailed information about a specific book.
        
        Args:
            book_id: Goodreads book ID
            
        Returns:
            Dictionary containing book details
        """
        try:
            book = self.client.book.show(book_id)
            return {
                'title': book.title,
                'author': book.author,
                'rating': book.average_rating,
                'description': book.description,
                'publication_year': book.publication_year,
                'num_pages': book.num_pages,
                'link': f"https://www.goodreads.com/book/show/{book_id}"
            }
        except Exception as e:
            print(f"Error fetching book details: {str(e)}")
            return None 
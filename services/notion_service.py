"""
Notion Service for CapyRead - Handles Notion integration for book reviews and notes
"""

import os
from typing import Dict, Optional
import logging
from dotenv import load_dotenv
from notion_client import Client


load_dotenv()
logger = logging.getLogger(__name__)

class NotionService:
    """Service for creating and managing book reviews in Notion"""
    
    def __init__(self):
        self.enabled = False
        try:
            
            self.api_key = os.getenv('NOTION_API_KEY')
            self.database_id = os.getenv('NOTION_DATABASE_ID')
            
            if self.api_key:
                self.client = Client(auth=self.api_key)
                self.enabled = True
                logger.info("Notion service initialized successfully")
            else:
                logger.warning("NOTION_API_KEY not found in environment variables")
                
        except ImportError:
            logger.warning("Notion client not available. Notion features disabled.")
    
    def create_book_review(self, title: str, author: str = "", review: str = "", rating: int = 5) -> Dict:
        """
        Create a book review in Notion.
        
        Args:
            title: Book title
            author: Book author
            review: User's review text
            rating: Rating from 1-5
            
        Returns:
            Dictionary containing success status and page details
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "Notion integration not available. Please install notion-client and set NOTION_API_KEY."
            }
        
        try:
            # Create the properties for the Notion page
            properties = {
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                "Rating": {
                    "number": rating
                },
                "Review": {
                    "rich_text": [
                        {
                            "text": {
                                "content": review
                            }
                        }
                    ]
                },
                "Status": {
                    "status": {
                        "name": "Done"
                    }
                }
            }
            
            # Add author if provided
            if author:
                properties["Author"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": author
                            }
                        }
                    ]
                }
            
            # Create the page content blocks
            children = [
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "My Review"}}]
                    }
                }
            ]
            
            # Add review content if provided
            if review:
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": review}}]
                    }
                })
            else:
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": "Add your thoughts about this book here..."}}]
                    }
                })
            
            # Add sections for notes
            children.extend([
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "Key Quotes"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": "Add memorable quotes here..."}}]
                    }
                },
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": "Reading Notes"}}]
                    }
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": "Add your reading notes and insights here..."}}]
                    }
                }
            ])
            
            new_page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties,
                children=children
            )
            
            return {
                'success': True,
                'page_id': new_page['id'],
                'page_url': new_page['url'],
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error creating Notion page: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to create Notion page: {str(e)}"
            }
    
    def create_book_page(self, book_details: Dict) -> Dict:
        """
        Create a new page in Notion for a book (legacy method for compatibility).
        
        Args:
            book_details: Dictionary containing book information
            
        Returns:
            Dictionary containing the created page information
        """
        return self.create_book_review(
            title=book_details.get('title', 'Unknown Title'),
            author=book_details.get('author', ''),
            review="",
            rating=int(book_details.get('rating', 5)),
            status=book_details.get('status', 'Done')
        )
            
    def update_book_status(self, page_id: str, status: str) -> Dict:
        """
        Update the reading status of a book.
        
        Args:
            page_id: Notion page ID
            status: New status (e.g., 'To Read', 'Reading', 'Done')
            
        Returns:
            Dictionary containing the update status
        """
        if not self.enabled:
            return {"success": False, "error": "Notion service not available"}
        
        try:
            self.client.pages.update(
                page_id=page_id,
                properties={
                    "Status": {
                        "status": {
                            "name": status
                        }
                    }
                }
            )
            
            return {
                'success': True,
                'message': f"Updated book status to {status}"
            }
        except Exception as e:
            logger.error(f"Error updating book status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_books(self, query: str, limit: int = 10) -> Dict:
        """Search for books in the Notion database"""
        if not self.enabled:
            return {"success": False, "error": "Notion service not available"}
        
        try:
            results = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Title",
                    "title": {
                        "contains": query
                    }
                },
                page_size=limit
            )
            
            books = []
            for page in results['results']:
                properties = page['properties']
                books.append({
                    'id': page['id'],
                    'title': properties.get('Title', {}).get('title', [{}])[0].get('text', {}).get('content', ''),
                    'author': properties.get('Author', {}).get('rich_text', [{}])[0].get('text', {}).get('content', ''),
                    'rating': properties.get('Rating', {}).get('number', 0),
                    'status': properties.get('Status', {}).get('select', {}).get('name', ''),
                    'url': page['url']
                })
            
            return {
                'success': True,
                'books': books
            }
            
        except Exception as e:
            logger.error(f"Error searching Notion books: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            } 
        
if __name__ == "__main__":
    notion_service = NotionService()
    print(notion_service.create_book_review("The Little Prince", "Antoine de Saint-Exupéry", "A classic story about a boy and his adventures with a fox.", 5))
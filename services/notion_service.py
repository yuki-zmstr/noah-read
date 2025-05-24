import os
from typing import Dict
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

class NotionService:
    def __init__(self):
        self.client = Client(auth=os.getenv('NOTION_API_KEY'))
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        
    def create_book_page(self, book_details: Dict) -> Dict:
        """
        Create a new page in Notion for a book.
        
        Args:
            book_details: Dictionary containing book information
            
        Returns:
            Dictionary containing the created page information
        """
        try:
            new_page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Title": {
                        "title": [
                            {
                                "text": {
                                    "content": book_details['title']
                                }
                            }
                        ]
                    },
                    "Author": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": book_details['author']
                                }
                            }
                        ]
                    },
                    "Rating": {
                        "number": float(book_details['rating'])
                    },
                    "Status": {
                        "select": {
                            "name": "To Read"
                        }
                    },
                    "Link": {
                        "url": book_details['link']
                    }
                },
                children=[
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"text": {"content": "Description"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": book_details['description']}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [{"text": {"content": "My Notes"}}]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": "Add your reading notes here..."}}]
                        }
                    }
                ]
            )
            
            return {
                'status': 'success',
                'page_id': new_page['id'],
                'url': new_page['url']
            }
            
        except Exception as e:
            print(f"Error creating Notion page: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
            
    def update_book_status(self, page_id: str, status: str) -> Dict:
        """
        Update the reading status of a book.
        
        Args:
            page_id: Notion page ID
            status: New status (e.g., 'Reading', 'Completed')
            
        Returns:
            Dictionary containing the update status
        """
        try:
            self.client.pages.update(
                page_id=page_id,
                properties={
                    "Status": {
                        "select": {
                            "name": status
                        }
                    }
                }
            )
            
            return {
                'status': 'success',
                'message': f"Updated book status to {status}"
            }
        except Exception as e:
            print(f"Error updating book status: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            } 
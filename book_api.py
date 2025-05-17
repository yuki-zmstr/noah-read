import requests

def fetch_book_info(title: str) -> dict:
    url = "https://openlibrary.org/search.json"
    params = {"title": title}
    res = requests.get(url, params=params)
    data = res.json()
    if data["docs"]:
        book = data["docs"][0]
        return {
            "title": book.get("title"),
            "author": ", ".join(book.get("author_name", [])),
            "year": book.get("first_publish_year", "n/a"),
            "cover_id": book.get("cover_i"),
            "description": f"A book titled '{book.get('title')}' by {', '.join(book.get('author_name', []))}."
        }
    return {"title": title, "author": "Unknown", "description": "No data found."}

def get_cover_url(cover_id, size="M") -> str:
    if cover_id:
        return f"https://covers.openlibrary.org/b/id/{cover_id}-{size}.jpg"
    return "https://via.placeholder.com/150x220?text=No+Cover"

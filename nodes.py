from langchain_core.runnables import RunnableLambda
from book_api import fetch_book_info, get_cover_url
from vector_store import store_reflection

# Each of these returns a RunnableLambda

greeting_node = RunnableLambda(lambda state: state)

def choose_mode(state):
    text = state["user_input"].lower()
    if "recommend" in text:
        return "recommend"
    elif "journal" in text:
        return "journal"
    return "chat"

choose_mode = RunnableLambda(choose_mode)

def recommend_fn(state):
    book = "The Little Prince"  # Replace with smarter selection
    info = fetch_book_info(book)
    cover = get_cover_url(info.get("cover_id"))
    state["last_book"] = book
    state["response"] = (
        f"📚 *{info['title']}* by {info['author']} ({info['year']})\n\n"
        f"{info['description']}\n\n![cover]({cover})"
    )
    return state

recommend_node = RunnableLambda(recommend_fn)

coffee_node = RunnableLambda(lambda state: {
    **state,
    "response": state["response"] + "\n☕ Pair it with a hazelnut latte!"
})

chat_node = RunnableLambda(lambda state: {
    **state,
    "response": f"💬 What did you think about {state.get('last_book', 'the book')}?"
})

def memory_fn(state):
    book = state.get("last_book")
    reflection = state.get("user_input")
    if book and reflection:
        store_reflection(book, reflection)
    state["response"] = "🧠 Capybara remembers your thoughts!"
    return state

memory_node = RunnableLambda(memory_fn)

journal_node = RunnableLambda(lambda state: {
    **state,
    "response": "📝 How did the book make you feel?"
})

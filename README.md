---
title: Noah
emoji: 💬
colorFrom: yellow
colorTo: purple
sdk: gradio
sdk_version: 5.29.1
app_file: app.py
pinned: false
short_description: Noah is an AI-powered reading assistant that can recommend books, manage your reading schedule, and track your reading journey.
---

An example chatbot using [Gradio](https://gradio.app), [`huggingface_hub`](https://huggingface.co/docs/huggingface_hub/v0.22.2/en/index), and the [Hugging Face Inference API](https://huggingface.co/docs/api-inference/index).

# 📚 Noah — Your AI Reading Companion

Noah is an AI-powered reading assistant that helps you discover books, manage your reading schedule, and track your reading journey. It integrates with OpenLibrary for book recommendations, Google Calendar for scheduling, and Notion for note-taking.

## ✨ Features

1. 📖 Book Recommendations

   - Get personalized book recommendations based on genres
   - Filter by minimum rating
   - View detailed book information from OpenLibrary

2. 📅 Reading Schedule

   - Schedule reading sessions in your Google Calendar
   - Customize reading duration
   - Automatic scheduling for optimal reading times

3. 📝 Reading Notes
   - Create organized Notion pages for each book
   - Track reading progress
   - Store your thoughts and highlights

## 🚀 Getting Started

1. Clone the repo:

   ```bash
   git clone https://huggingface.co/spaces/yuki-zmstr/noah-read
   cd noah-read
   ```

2. Ensure you have python 3.10 or above installed (3.10 is recommended):

   ```bash
   python3 --version
   ```

3. Create a virtual environment to isolate dependencies:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

4. Install requirements:

   ```bash
   pip3 install -r requirements.txt
   ```

5. Set up your environment variables:
   Copy `.env.example` to `.env` and fill in your API keys:

   ```bash
   cp .env.example .env
   ```

6. Run the app:

   ```bash
   python3 app.py
   ```

   Or for development mode with auto-reload:

   ```bash
   gradio app.py
   ```

## 🔑 API Setup

1. **OpenAI API**:

   - Go to [OpenAI API](https://platform.openai.com/api-keys)
   - Create an account or log in
   - Generate a new API key
   - Add to `.env`: `OPENAI_API_KEY=your_key_here`

2. **Google Calendar API**:

   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project
   - Enable the Google Calendar API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download and rename to `google_credentials.json`
   - Add to `.env`: `GOOGLE_CALENDAR_CREDENTIALS_FILE=google_credentials.json`

3. **Notion API**:
   - Go to [Notion Developers](https://www.notion.so/my-integrations)
   - Create new integration
   - Copy the Integration Token
   - Create a database and share with integration
   - Add to `.env`:
     ```
     NOTION_API_KEY=your_integration_token
     NOTION_DATABASE_ID=your_database_id
     ```

## 💬 Usage Examples

Try these commands in the chat:

```
"Recommend me some science fiction books"
"Schedule 30 minutes to read tomorrow"
"Create a journal entry for my thoughts"
```

## Notion Database Structure

The Notion database will be automatically set up with these fields:

- Title (title): Book title
- Author (rich text): Author name(s)
- Rating (number): Book rating
- Status (select): Reading status (To Read, Reading, Completed)
- Link (url): Link to the book on OpenLibrary
- Description (rich text): Book description
- My Notes (rich text): Your reading notes and thoughts

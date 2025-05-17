---
title: Capyread
emoji: 💬
colorFrom: yellow
colorTo: purple
sdk: gradio
sdk_version: 5.29.1
app_file: app.py
pinned: false
short_description: CapyRead is an AI-powered chatbot that recommends books
---

An example chatbot using [Gradio](https://gradio.app), [`huggingface_hub`](https://huggingface.co/docs/huggingface_hub/v0.22.2/en/index), and the [Hugging Face Inference API](https://huggingface.co/docs/api-inference/index).

# 📚 CapyRead — Your Cozy Capybara Reading Companion

CapyRead is an AI-powered chatbot that recommends books, remembers your reflections, and pairs every title with a delicious coffee. Built with Python, LangGraph, LangSmith, and Gradio.

## ✨ Features

- 📖 Book recommendations via OpenLibrary
- 🧠 Reflection memory using ChromaDB
- ☕ Coffee pairings based on mood
- 🐾 Capybara-themed personality with LangGraph orchestration

## 🚀 Getting Started

1. Clone the repo:

   ```bash
   git clone https://huggingface.co/spaces/yuki-zmstr/capyread
   cd capyread

   ```

2. Create a virtual envionment to isolate dependencies:

   ```
   python3 -m venv capyread
   source capyread/bin/activate
   ```

3. Install requirements

   ```
   pip3 install -r requirements.txt
   ```

4. Run the app in local dev mode with hot reload

   ```
   gradio app.py --demo-name=demo
   ```
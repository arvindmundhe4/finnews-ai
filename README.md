# FinNews

A beautiful and modern financial news assistant built with FastAPI, Marked.js, TailwindCSS, and DaisyUI. This application provides up-to-date financial news, market analysis, and sentiment analysis using the OpenAI API.


## Features

- 🔍 Get the latest financial news on stocks, cryptocurrencies, and economic trends
- 📊 Visual sentiment analysis with color-coded tables for better insights
- 🔗 Highlighted citations with source links for easy reference
- 📱 Share conversations via unique shareable URLs
- 🌓 Light and dark mode support
- 📱 Fully responsive design for all devices
- ⚡ Beautiful markdown rendering with proper formatting

## Technology Stack

- **Backend**: FastAPI
- **Frontend**: TailwindCSS + DaisyUI
- **Markdown**: Marked.js with DOMPurify for secure content rendering
- **Database**: SQLite with Tortoise ORM
- **API**: OpenAI API for news retrieval and sentiment analysis

## Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/finnews.git
   cd finnews
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on the provided `.env.example`:
   ```
   cp .env.example .env
   ```

5. Edit the `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   OPENAI_SEARCH_MODEL=gpt-4o-search-preview
   OPENAI_SENTIMENT_MODEL=gpt-4o-mini
   APP_BASE_URL=http://localhost:8000
   ```

### Running the Application

Start the application with:

```
python app.py
```

Or with uvicorn directly:

```
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at `http://localhost:8000`.

## Usage

1. Enter your financial question or topic in the input box
2. Click "Send" or press Enter to get the latest financial news
3. View the financial news with highlighted citations and sentiment analysis
4. Share your conversation by clicking the "Share Chat" button

## Enhanced Features

### Citation Highlighting

Citations in the news content are now highlighted with a green background and are clickable links that take you directly to the source. This makes it easier to verify information and explore sources in depth.

### Visual Sentiment Analysis

Sentiment analysis results are presented in a visually appealing table with color-coded scores:
- 🟢 Positive sentiment (green)
- 🔴 Negative sentiment (red)
- ⚪ Neutral sentiment (gray)

This makes it easy to quickly understand the sentiment around different entities mentioned in the news.

### Markdown Rendering

All content is rendered using Marked.js with proper markdown formatting, ensuring beautiful presentation of:
- Headers and subheaders
- Lists and bullet points
- Tables and structured data
- Code blocks with syntax highlighting
- Links and references

### Sharing Conversations

The application allows you to share your conversations via a unique URL. To share a conversation:

1. Have at least one exchange with the assistant
2. Click the "Share Chat" button in the top right corner
3. Copy the URL from the dialog
4. Share the URL with others

Anyone with the URL can view the shared conversation with all formatting preserved.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/)
- [TailwindCSS](https://tailwindcss.com/) and [DaisyUI](https://daisyui.com/)
- [Marked.js](https://marked.js.org/) for markdown rendering
- [DOMPurify](https://github.com/cure53/DOMPurify) for security
- [OpenAI API](https://openai.com/api/) for news retrieval and analysis

import os
import re
import asyncio
import json
import openai
import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Dict, Any, List, Optional

# Load environment variables from .env file
load_dotenv()

# Create router
router = APIRouter()

# Configure rate limiter
limiter = Limiter(key_func=get_remote_address)

# Get model names from environment variables
SEARCH_MODEL = os.getenv("OPENAI_SEARCH_MODEL", "gpt-4o-mini-search-preview")
SENTIMENT_MODEL = os.getenv("OPENAI_SENTIMENT_MODEL", "gpt-4o-mini")
API_KEY = os.getenv("OPENAI_API_KEY")

@router.post("/api/get_news")
@limiter.limit("10 per minute")
async def get_news(request: Request, data: Dict[str, Any]):
    """Get financial news based on query."""
    query = data.get('query', '')
    search_depth = data.get('search_depth', 'medium')
    
    # Check if query is provided
    if not query:
        return JSONResponse(
            status_code=400,
            content={"error": "Query is required"}
        )
    
    try:
        # Step 1: Call OpenAI API to get financial news
        system_message = (
            "You are FinNews AI, a sophisticated financial news analyst specializing in providing accurate, "
            "up-to-date information about global markets, stocks, cryptocurrencies, and economic trends. "
            "\n\n"
            "GUIDELINES:\n"
            "1. Always prioritize recent, factual information from reputable financial sources.\n"
            "2. Provide balanced perspectives, acknowledging both bullish and bearish viewpoints when relevant.\n"
            "3. Avoid speculation and clearly distinguish between facts and expert opinions.\n"
            "4. Use precise financial terminology appropriate for the user's query.\n"
            "5. Include relevant quantitative data (e.g., price movements, percentages, market cap changes).\n"
            "6. Structure your response with clear sections and bullet points for readability.\n"
            "7. For technical queries, explain concepts in accessible language.\n"
            "\n\n"
            "SOURCES:\n"
            "- Always cite your sources using the format [Source: Title (URL)] immediately after the information.\n"
            "- Include publication dates when available to establish recency.\n"
            "\n\n"
            "Remember that users rely on this information for financial awareness, so accuracy and clarity are paramount."
        )
        
        # Adjust the prompt based on search depth
        detail_level = {
            "low": "Provide a brief overview with 3 key points.",
            "medium": "Provide a balanced analysis with 5 key points.",
            "high": "Provide a comprehensive analysis with 10 key points and detailed information."
        }.get(search_depth, "Provide a balanced analysis with 4-6 key points.")
        
        user_message = f"Please provide financial news about: {query}. {detail_level}"
        
        # Call the API with a simpler parameter set and explicit API key
        # Create a client without specifying proxies
        http_client = httpx.Client()
        client = openai.OpenAI(api_key=API_KEY, http_client=http_client)
        response = client.chat.completions.create(
            model=SEARCH_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
        )
        
        # Extract content
        content = response.choices[0].message.content
        
        # Process sources/citations from content
        citation_pattern = r'\[Source: (.*?) \((https?://[^\s\)]+)\)\]'
        citations_found = re.findall(citation_pattern, content)
        
        citations = [{"title": title, "url": url} for title, url in citations_found]
        
        # Step 2: Perform sentiment analysis
        sentiment_result = await perform_sentiment_analysis(content, query)
        
        # Format the response with the news and sentiment analysis
        response_text = format_response(query, content, citations, sentiment_result)
        
        return {"response": response_text}
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Error getting news: {str(e)}"}
        )


async def perform_sentiment_analysis(content: str, query: str):
    """
    Process the content to extract sentiment analysis.
    Returns a table of sentiment scores ranging from -10 (extremely negative) to +10 (extremely positive).
    """
    try:
        # Create prompt for sentiment analysis
        system_prompt = """
        You are FinNews AI's sentiment analysis engine, a sophisticated financial analyst specializing in market sentiment evaluation.
        
        TASK:
        Analyze the provided financial news and generate a comprehensive sentiment analysis table with precision and nuance.
        
        SCORING SYSTEM:
        - Use a scale from -10 (extremely negative) to +10 (extremely positive)
        - -10 to -7: Severe negative impact (e.g., bankruptcy, major crisis)
        - -6 to -3: Moderate negative outlook (e.g., missed earnings, market correction)
        - -2 to +2: Neutral or mixed signals (e.g., mixed performance, uncertain outlook)
        - +3 to +6: Moderate positive outlook (e.g., growth potential, positive earnings)
        - +7 to +10: Strongly positive outlook (e.g., breakthrough, major acquisition, exceptional growth)
        
        ANALYSIS CATEGORIES:
        1. Overall Market Sentiment - Assess the general market mood related to the query
        2. Specific Companies/Assets - Analyze individual stocks, cryptocurrencies, or other assets mentioned
        3. Sector/Industry Trends - Evaluate industry-wide patterns and movements
        4. Economic Indicators - Assess relevant economic data points (inflation, employment, GDP, etc.)
        5. Risk Assessment - Evaluate potential downside risks mentioned in the news
        
        FORMAT:
        - Create a clean, well-formatted markdown table with headers: Entity | Score | Explanation
        - For each entity, provide a concise but insightful 1-2 sentence explanation that justifies the score
        - Focus on the most relevant entities to the user's query (4-8 total items)
        - Sort results from most positive to most negative sentiment
        
        QUALITY STANDARDS:
        - Be objective and evidence-based in your scoring
        - Avoid political bias or emotional language
        - Identify nuanced sentiment that might not be explicitly stated
        - Consider both short and long-term implications when scoring
        """
        
        user_prompt = f"""
        FINANCIAL NEWS TO ANALYZE:
        {content}
        
        USER QUERY:
        {query}
        
        Provide a sentiment analysis table for this financial news, focusing on aspects relevant to the user's query.
        """
        
        # Call OpenAI API for sentiment analysis
        http_client = httpx.Client()
        client = openai.OpenAI(api_key=API_KEY, http_client=http_client)
        completion = client.chat.completions.create(
            model=SENTIMENT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=1200
        )
        
        # Extract response
        response_text = completion.choices[0].message.content
        
        # Return the sentiment analysis
        return response_text
    
    except Exception as e:
        print(f"Error performing sentiment analysis: {str(e)}")
        return "Error performing sentiment analysis. Please try again later."


def format_response(query: str, content: str, citations: List[Dict[str, str]], sentiment_analysis: Optional[str] = None) -> str:
    """Format the response with news results and sentiment analysis."""
    if not content:
        return f"I couldn't find any recent financial news related to '{query}'. Please try a different query or check back later."
    
    # Format news results with proper markdown instead of HTML tags
    response = f"## **Financial News for: {query}**\n\n"
    
    # Highlight citations in the content
    citation_pattern = r'\[Source: (.*?) \((https?://[^\s\)]+)\)\]'
    
    # Replace citations with highlighted spans
    citation_replaced_content = re.sub(
        citation_pattern,
        r'<a href="\2" class="citation" target="_blank">[Source: \1]</a>',
        content
    )
    
    # Add the main content with highlighted citations
    response += citation_replaced_content
    
    # Add sentiment analysis if available
    if sentiment_analysis:
        sentiment_content = "\n\n### Sentiment Analysis\n\n"
        response += sentiment_content
        
        # Check if it's already in HTML format
        if "<table" not in sentiment_analysis:
            # Parse the sentiment analysis text to extract structured data
            # This is a simple implementation and might need adjustment based on actual format
            lines = sentiment_analysis.strip().split('\n')
            
            # Start the HTML table
            table_html = '<table class="sentiment-table">\n<thead>\n<tr>'
            table_html += '<th>Entity</th><th>Score</th><th>Explanation</th>'
            table_html += '</tr>\n</thead>\n<tbody>\n'
            
            # Check if the sentiment analysis is already in a table format
            in_table = False
            for line in lines:
                if "Entity" in line and "Score" in line and "Explanation" in line:
                    in_table = True
                    continue
                
                if in_table and "|" in line and "---" not in line:
                    cols = line.split("|")
                    if len(cols) >= 4:  # Account for empty first column in markdown tables
                        entity = cols[1].strip()
                        score = cols[2].strip()
                        explanation = cols[3].strip()
                        
                        # Apply color classes based on score value
                        score_class = "score-neutral"
                        if score.startswith("+"):
                            score_class = "score-positive"
                        elif score.startswith("-"):
                            score_class = "score-negative"
                        
                        table_html += f'<tr>\n  <td>{entity}</td>\n  <td class="{score_class}">{score}</td>\n  <td>{explanation}</td>\n</tr>\n'
            
            # Close the table
            table_html += '</tbody>\n</table>'
            
            # Add the HTML table to the response
            sentiment_analysis = table_html
        
        response += sentiment_analysis
    
    # Add disclaimer
    response += "\n\n---\n*Note: This information is based on recent financial news and may not reflect the most current market conditions.*"
    
    return response


@router.post("/api/stream_news")
@router.get("/api/stream_news")
@limiter.limit("10 per minute")
async def stream_news(request: Request, query: str = None, search_depth: str = "medium"):
    """Stream financial news based on query using Server-Sent Events."""
    # For POST requests, data comes from the request body
    if request.method == "POST":
        data = await request.json()
        query = data.get('query', '')
        search_depth = data.get('search_depth', 'medium')
    # For GET requests, data comes from query parameters (already captured in function parameters)
    
    # Check if query is provided
    if not query:
        return JSONResponse(
            status_code=400,
            content={"error": "Query is required"}
        )
    
    async def event_generator():
        try:
            # Step 1: Prepare system message for the financial news
            system_message = """
            You are FinNews AI, a sophisticated financial news analyst specializing in global market trends and insights.
            
            TASK:
            Generate comprehensive, high-quality financial news and analysis on the given topic.
            
            FORMAT:
            - DO NOT include any title or heading at the beginning of your response
            - Start with a brief introduction summarizing key points
            - Organize information into clearly numbered sections with descriptive headings
            - Include relevant data points, trends, and expert opinions
            - Include links to reputable financial sources in parentheses (e.g., reuters.com, bloomberg.com)
            - Maintain a professional, objective tone
            - Your analysis should be data-driven, balanced, and insightful
            """
            
            # Adjust the prompt based on search depth
            detail_level = {
                "low": "Provide a brief overview with 3-5 key points.",
                "medium": "Provide a standard analysis with 5-7 key insights.",
                "high": "Provide a comprehensive analysis with 7-10 key insights, including technical details where relevant."
            }.get(search_depth, "Provide a standard analysis with 5-7 key insights.")
            
            user_message = f"Please provide financial news about: {query}. {detail_level}"
            
            # Send initial message to indicate the start of streaming
            yield f"data: {json.dumps({'type': 'start', 'content': f'## **Financial News for: {query}**\n\n'})}\n\n"
            
            # Stream the OpenAI response
            # Use AsyncOpenAI client
            title_sent = False
            collected_text = ""
            
            async with httpx.AsyncClient() as http_client:
                client = openai.AsyncOpenAI(api_key=API_KEY, http_client=http_client)
                
                response_stream = await client.chat.completions.create(
                    model=SEARCH_MODEL,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    stream=True
                )
                
                full_content = ""
                async for chunk in response_stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        content_delta = chunk.choices[0].delta.content
                        if content_delta:
                            full_content += content_delta
                            
                            # Skip any duplicated headline that might appear in the model output
                            if not title_sent:
                                if "Financial News for:" in content_delta:
                                    # Skip this as we've already sent the title
                                    continue
                            
                            yield f"data: {json.dumps({'type': 'content', 'content': content_delta})}\n\n"
                
                # Process sources/citations from content
                citation_pattern = r'\[Source: (.*?) \((https?://[^\s\)]+)\)\]'
                citations_found = re.findall(citation_pattern, full_content)
                
                citations = [{"title": title, "url": url} for title, url in citations_found]
                
                # Format citations in the content
                citation_replaced_content = re.sub(
                    citation_pattern,
                    r'<a href="\2" class="citation" target="_blank">[Source: \1]</a>',
                    full_content
                )
                
                # Send a message indicating we're performing sentiment analysis
                yield f"data: {json.dumps({'type': 'loading_sentiment', 'content': '\n\n### Sentiment Analysis (calculating...)\n\n'})}\n\n"
                
                # Perform sentiment analysis
                # Create prompt for sentiment analysis
                system_prompt = """
                You are FinNews AI's sentiment analysis engine, a sophisticated financial analyst specializing in market sentiment evaluation.
                
                TASK:
                Analyze the provided financial news and generate a comprehensive sentiment analysis table with precision and nuance.
                
                FORMAT:
                Present your results in a clean, well-formatted table with these columns:
                | Date | News | Score |
                
                The Score column should use a scale from -10 (extremely negative) to +10 (extremely positive).
                
                Add an "Overall Sentiment Score" after the table summarizing the collective sentiment.
                """
                
                user_prompt = f"""
                FINANCIAL NEWS TO ANALYZE:
                {full_content}
                
                USER QUERY:
                {query}
                
                Provide a sentiment analysis table for this financial news, focusing on aspects relevant to the user's query.
                """
                
                # Call OpenAI API for sentiment analysis
                async with httpx.AsyncClient() as http_client:
                    client = openai.AsyncOpenAI(api_key=API_KEY, http_client=http_client)
                    sentiment_response = await client.chat.completions.create(
                        model=SENTIMENT_MODEL,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.3,
                        max_tokens=1200
                    )
                    
                    # Extract sentiment analysis
                    sentiment_analysis = sentiment_response.choices[0].message.content
                    
                    # Send the sentiment analysis in one chunk
                    yield f"data: {json.dumps({'type': 'sentiment', 'content': '\n\n### Sentiment Analysis\n\n' + sentiment_analysis})}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'content': '[DONE]'})}\n\n"
                    
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

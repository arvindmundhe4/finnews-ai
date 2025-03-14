from typing import Dict, Any, List, Optional
import re
import os
import openai
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

# Create router
router = APIRouter()

# Configure rate limiter
limiter = Limiter(key_func=get_remote_address)

# Get model names from environment variables
SEARCH_MODEL = os.getenv("OPENAI_SEARCH_MODEL", "gpt-4o-mini-search-preview")
SENTIMENT_MODEL = os.getenv("OPENAI_SENTIMENT_MODEL", "gpt-4o-mini")


@router.post("/api/get_news")
@limiter.limit("10 per minute")
async def get_news(request: Request, data: Dict[str, Any]):
    """Get financial news based on query."""
    query = data.get('query', '')
    search_depth = data.get('search_depth', 'high')
    
    # Check if query is provided
    if not query:
        return JSONResponse(
            status_code=400,
            content={"error": "Query is required"}
        )
    
    try:
        # Step 1: Call OpenAI API to get financial news
        system_message = (
            "You are a financial news agent that provides up-to-date information about "
            "markets, stocks, cryptocurrency, and economic trends. "
            "Always cite your sources in your response using [Source: Title (URL)] format at the end of relevant statements."
        )
        
        # Adjust the prompt based on search depth
        detail_level = {
            "low": "Provide a brief overview with 1-2 key points.",
            "medium": "Provide a balanced analysis with 3-4 key points.",
            "high": "Provide a comprehensive analysis with 5+ key points and detailed information."
        }.get(search_depth, "Provide a balanced analysis with 3-4 key points.")
        
        user_message = f"Please provide financial news about: {query}. {detail_level}"
        
        # Call the API with a simpler parameter set
        client = openai.OpenAI()
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
        You are a financial analyst specializing in sentiment analysis. 
        Analyze the provided financial news and generate a table of sentiment scores.
        
        Score each relevant entity mentioned in the news on a scale from -10 (extremely negative) to +10 (extremely positive).
        Focus on the following categories:
        1. Overall Market Sentiment
        2. Specific Companies or Stocks mentioned
        3. Economic Indicators
        4. Sector/Industry sentiment
        
        For each item, provide:
        - Entity name/description
        - Sentiment score (-10 to +10)
        - Brief 1-2 sentence explanation of the score
        
        Format your response as a markdown table with headers: Entity | Score | Explanation
        """
        
        user_prompt = f"""
        FINANCIAL NEWS TO ANALYZE:
        {content}
        
        USER QUERY:
        {query}
        
        Provide a sentiment analysis table for this financial news, focusing on aspects relevant to the user's query.
        """
        
        # Call OpenAI API for sentiment analysis
        client = openai.OpenAI()
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
    response = f"## Financial News for: {query}\n\n"
    
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
        response += "\n\n## Sentiment Analysis\n\n"
        response += "Here is the sentiment analysis table based on the provided financial news:\n\n"
        
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

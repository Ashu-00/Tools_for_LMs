import sys
import time
import os
import requests
import re
from urllib.parse import urljoin, urlparse
from googlesearch import search
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID, STORED
from whoosh.qparser import QueryParser

# Define the schema with explicit STORED field for content
schema = Schema(
    title=TEXT(stored=True),
    content=TEXT(stored=True),  # Ensure content is stored
    url=ID(stored=True)
)

# Create or open the index directory
index_dir = "index"
if not os.path.exists(index_dir):
    os.mkdir(index_dir)
    ix = create_in(index_dir, schema)
else:
    # Force rebuild the index to ensure schema is correct
    import shutil
    shutil.rmtree(index_dir)
    os.mkdir(index_dir)
    ix = create_in(index_dir, schema)

# Function to clean HTML text without BeautifulSoup
def extract_text_from_html(html_content):
    """Extract text from HTML without using BeautifulSoup"""
    # Remove script and style elements
    html_content = re.sub(r'<script[^>]*>.*?</script>', ' ', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<style[^>]*>.*?</style>', ' ', html_content, flags=re.DOTALL)

    # Extract title separately
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.DOTALL | re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else "No title"

    # Get text by removing HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)

    # Clean extracted text
    text = re.sub(r'&nbsp;|&gt;|&lt;|&amp;|&quot;|&apos;', ' ', text)  # Remove common HTML entities
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace

    return title, text

# Extract links from HTML using regex instead of BeautifulSoup
def extract_links(html_content, base_url):
    """Extract links from HTML using regex"""
    links = []
    # Find all href attributes in anchor tags
    for match in re.finditer(r'<a\s+[^>]*href=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</a>', html_content, re.DOTALL | re.IGNORECASE):
        href = match.group(1)
        link_text = match.group(2)

        # Clean link text by removing tags
        link_text = re.sub(r'<[^>]+>', ' ', link_text)
        link_text = re.sub(r'\s+', ' ', link_text).strip()

        # Create absolute URL
        full_url = urljoin(base_url, href)

        links.append((full_url, link_text))

    return links

# Function to index a crawled page
def index_page(url, title, content):
    try:
        # Truncate content if it's too large
        if len(content) > 50000:  # Limit to 50K characters
            content = content[:50000] + "... (content truncated)"

        # Truncate title if needed
        if len(title) > 1000:
            title = title[:1000] + "... (title truncated)"

        # Verify we have actual content
        if len(content.strip()) < 100:
            print(f"Content too short to index for {url}")
            return False

        writer = ix.writer()
        writer.add_document(title=title, content=content, url=url)
        writer.commit()
        print(f"Successfully indexed document with {len(content)} characters")
        return True
    except Exception as e:
        print(f"Error indexing {url}: {e}")
        return False

# Function to validate URL
def is_valid_url(url):
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme) and parsed.scheme in ['http', 'https']
    except:
        return False

# Crawler function
def crawl(query, max_pages=20, max_depth=1):
    query_words = query.lower().split()  # Split query into keywords
    try:
        initial_urls = list(search(query, num=5, stop=5))
    except Exception as e:
        print(f"Error with Google search: {e}")
        initial_urls = []

    # Store tuples of (url, current_depth)
    to_visit = [(url, 0) for url in initial_urls if is_valid_url(url)]
    visited = set()
    pages_crawled = 0

    print(f"Found {len(initial_urls)} initial URLs")

    while to_visit and pages_crawled < max_pages:
        url, depth = to_visit.pop(0)
        if url in visited:
            continue

        print(f"Visiting: {url} (depth: {depth})")
        visited.add(url)

        try:
            # Set a user agent
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

            # Get the HTML content with a timeout and size limit
            response = requests.get(url, timeout=10, headers=headers, stream=True)

            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                print(f"Skipping non-HTML content: {content_type}")
                continue

            # Read content in chunks to limit memory usage
            html_content = ""
            content_size = 0
            max_size = 5 * 1024 * 1024  # 5MB limit

            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    try:
                        decoded_chunk = chunk.decode('utf-8', errors='ignore')
                        html_content += decoded_chunk
                        content_size += len(chunk)

                        if content_size > max_size:
                            print(f"Content too large, truncating at {max_size} bytes")
                            break
                    except Exception as e:
                        print(f"Error decoding chunk: {e}")
                        break

            # Check if we actually got content
            if len(html_content.strip()) < 500:  # Require at least 500 chars of HTML
                print(f"HTML content too small: {len(html_content)} bytes")
                continue

            # Extract text using regex instead of BeautifulSoup
            title, content = extract_text_from_html(html_content)

            print(f"Extracted title: '{title}'")
            print(f"Extracted content length: {len(content)} characters")

            # Only index if we have meaningful content
            if len(content) > 100:
                if index_page(url, title, content):
                    pages_crawled += 1
                    print(f"Crawled and indexed ({pages_crawled}/{max_pages}): {url}")
            else:
                print(f"Skipping page with insufficient content: {url}")

            # Only follow links if we haven't reached the max depth
            if depth < max_depth:
                links_added = 0

                # Extract links using regex
                extracted_links = extract_links(html_content, url)

                print(f"Found {len(extracted_links)} links on page")

                for next_url, link_text in extracted_links:
                    # Skip if not valid URL or already visited
                    if not is_valid_url(next_url) or next_url in visited or any(next_url == u for u, _ in to_visit):
                        continue

                    # Check if link text or URL contains any query words
                    link_text_lower = link_text.lower()
                    url_lower = next_url.lower()

                    if any(word in link_text_lower for word in query_words) or any(word in url_lower for word in query_words):
                        to_visit.append((next_url, depth + 1))
                        links_added += 1
                        print(f"Adding link: {next_url}")

                        # Limit links per page
                        if links_added >= 5:
                            break

                print(f"Added {links_added} new links to visit")

        except Exception as e:
            print(f"Error crawling {url}: {e}")

        # Delay to avoid overloading servers
        time.sleep(1)

    print(f"Crawling complete. Visited {len(visited)} URLs, indexed {pages_crawled} pages.")

# Function to search the indexed data
def search_index(query_str):
    try:
        with ix.searcher() as searcher:
            query_obj = QueryParser("content", ix.schema).parse(query_str)
            results = searcher.search(query_obj, limit=10)

            if len(results) == 0:
                print("No results found.")
                return

            print(f"Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(f"Title: {result['title']}")
                print(f"URL: {result['url']}")

                # Debug field names
                print(f"Available fields: {', '.join(result.fields())}")

                # Print a snippet of content
                if 'content' in result:
                    content = result['content']
                    print(f"Content length: {len(content)} characters")
                    snippet = content[:200] + "..." if len(content) > 200 else content
                    print(f"Snippet: {snippet}")
                else:
                    print("No content field available")
                print("---")
            return results
    except Exception as e:
        print(f"Error searching index: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    query = "Harry Potter"  # Your search query
    print(f"Starting crawl for query: '{query}'")
    crawl(query, max_pages=10, max_depth=2)  # Reduced depth and pages for testing

    print("\nCrawling complete. Searching the index for 'Elon Musk':")
    search_index("Hermione Granger")

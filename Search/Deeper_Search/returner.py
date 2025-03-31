# Function to take the crawled sites and return chunked, ready to add to vector db form
from Tools_for_LMs.Search.Deeper_Search.crawler import crawl, search_index

def returner(query, vectordb, max_pages=10, max_depth=2):
    """
    Crawls the web for the given query, indexes the content, and adds it to the provided VectorDB.

    Args:
        query (str): The search query.
        vectordb (VectorDB): An instance of the VectorDB class.
        max_pages (int, optional): Maximum number of pages to crawl. Defaults to 10.
        max_depth (int, optional): Maximum depth for crawling. Defaults to 2.

    Returns:
        list: A list of indexed URLs.
    """
    indexed_urls = []

    def crawl_and_index(query, max_pages, max_depth):
        """
        Crawls and indexes content for the given query.
        """
        try:
            # Perform crawling
            if not query.strip():
                print("Empty query provided. Proceeding with crawl.")
            print(f"Starting crawl for query: '{query}'")
            crawl(query, max_pages=max_pages, max_depth=max_depth)

            # Search the index for the query
            print(f"\nSearching the index for '{query}':")
            results = search_index(query)

            # Extract content from results and add to VectorDB
            if results:
                chunks = []
                for result in results:
                    if 'content' in result:
                        content = result['content']
                        chunks.append(content)
                        indexed_urls.append(result['url'])

                # Add content to the vector database
                if chunks:
                    print(f"Adding {len(chunks)} chunks to the vector database...")
                    vectordb.add_texts_to_vector_db(chunks)
                    print("Content added to the vector database.")
            else:
                print("No results found to add to the vector database.")

        except Exception as e:
            print(f"Error during crawling and indexing: {e}")
            import traceback
            traceback.print_exc()

    # Execute the crawl and index process
    crawl_and_index(query, max_pages, max_depth)

    return indexed_urls

if __name__ == "__main__":
    from Tools_for_LMs.core.vector_db.db import VectorDB

    # Initialize the VectorDB
    vector_db = VectorDB(vector_dim=384, index_type="flat")  # Adjust vector_dim as per your embedding model

    # Query to search and add to the vector database
    query = "Artificial Intelligence"

    # Call the returner function
    indexed_urls = returner(query, vector_db, max_pages=5, max_depth=1)

    print("\nIndexed URLs:")
    for url in indexed_urls:
        print(url)
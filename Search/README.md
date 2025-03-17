# Search the Web

## Basic Idea
2 different searching tools.
1. Simple search for things like time or common information
2. Deeper search for efficiency

## Simple search implementation Idea
- [ ] A *api based search tool* that calls google/duckduckgo search and returns the first responses. 

## Deeper Search implementation Idea
- [x] A *base web crawler* that crawls webpages one by one and index them based on query
- [x] A *index search tool* that searches the index of web pages and retrieves useful, limited pages. This should also delete the old index after retrieval for stroage reasons.
- [ ] A *chunk and save tool* to index the pages in a common vector database.

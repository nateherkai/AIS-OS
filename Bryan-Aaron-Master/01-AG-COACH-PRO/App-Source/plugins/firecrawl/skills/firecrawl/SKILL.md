---
name: firecrawl
description: Use Firecrawl to scrape URLs, search the web with scraped content, map site URLs, or start website crawls.
---

# Firecrawl

Use this skill when the user asks for high-fidelity web scraping, page-to-Markdown conversion, website URL discovery, web search with scraped page content, or recursive site crawling.

## Tools

- `firecrawl_scrape`: scrape one absolute `http(s)` URL.
- `firecrawl_search`: search the web and optionally include scraped Markdown.
- `firecrawl_map`: discover URLs on a domain.
- `firecrawl_crawl`: start a recursive crawl.

## Requirements

The MCP server reads `FIRECRAWL_API_KEY` from the environment. In this repo it is configured through `FIRECRAWL_ENV_PATH=/Volumes/Samsung PSSD T7/ag-coach-app/.env`.

Never print the API key or commit it into plugin files.

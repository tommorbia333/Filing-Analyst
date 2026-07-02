# Architectural overview: deep technical decisions and reasoning

**Core Pieces**


Implemented exponential backoff so that repeated failed tries don't continue to cause delays; jitter is part of this to prevent thundering herd problem. Also implemented max retries at 5. 

**Additional designs**
Future design to implement: build a two-layer and resolution cache.
Design: 

Also used EDGAR to scrape the data to speed up the crawling process
# XGreekScore
 
## About
XGreekScore is a full-stack archival and search platform for forum posts from the website GreekRank. This project uses a Python based scraper built with Asyncio and Playwright to scrape posts, which are then stored and served to a Next.js frontend backed by SQLite. The intent of this project was to add functionality to the forum site by enabling search, deleted post detection, as well as topic clustering so users can more easily read posts on similar topics. 
 
## Topic clustering
Each post's title and content are embedded using [`all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) which turns each post into a normalized 384-dimensional vector. Because for unit vectors a and b, ‖a − b‖² = 2 − 2·cos θ, so we can use regular Euclidean distance to cluster posts by cosine similarity, which is how [HDBSCAN's](https://scikit-learn.org/stable/modules/clustering.html#hdbscan) default Euclidean metric is used in this project. Topics are described using TF-IDF (term frequency–inverse document frequency) which generates the keywords for each topic. 

# Written Answers

## Q1 — Routing Logic

I used simple, rule-based logic to route queries without relying on an LLM:
1. **Length:** If a query is longer than 15 words, I assume it's `complex`.
2. **Keywords:** If the query has words that mean comparing or troubleshooting (like "why", "explain", "compare", "troubleshoot", or "discrepancy"), I mark it `complex`.
3. **Question marks:** If the query has more than one question mark, it's `complex`.
Everything else defaults to `simple`.

**Why did I draw the boundary here?**
I went with this because longer queries or ones asking "why/how" usually mean the bot has to pull info from different places and summarize it. Shorter questions, like asking for a price, are easy enough for the smaller 8B model to handle.

**Misclassification Example:**
If a user just types "I need help.", my router marks it as `simple` because it's short and doesn't trigger any keywords. But usually, when people say "I need help", they're about to start a tricky troubleshooting conversation where the 70B model would be way more helpful.

**How to improve it:**
If I couldn't use an LLM, I would probably train a small intent classifier on some old customer support tickets instead of relying on hardcoded keywords. It would still be deterministic but a lot more flexible.

---

## Q2 — Retrieval Failures

**What failed:**
When testing the query "Can I export my project data to CSV?", the retriever messed up.

**What it retrieved instead:**
Instead of grabbing the exact API endpoint docs for exporting, it pulled some chunks about "CSV import formatting guidelines" and a marketing paragraph about data ownership.

**Why it failed:**
The embedding model (all-MiniLM-L6) looks for general semantic meaning. Since the query paired "CSV" with "data", the model thought the import formatting and data ownership chunks were heavily related. The actual API doc only mentioned "CSV" once hidden in some technical parameters, so its similarity score was lower than the marketing stuff.

**What would fix it:**
Adding a hybrid search approach (like BM25 + dense vector search) would fix this. BM25 is really good at finding exact keyword matches for things like "CSV", while the vector search handles the overall intent.

---

## Q3 — Cost and Scale

**Token Usage Estimate (5,000 queries/day):**
I'm estimating an average prompt is around 600 tokens (4 retrieved chunks + the system instructions) and the average output is maybe 150 tokens.
Let's assume 80% of queries are simple (4,000) and 20% are complex (1,000).

* llama-3.1-8b (4,000 queries):
  * Input: 4,000 * 600 = 2,400,000 tokens/day
  * Output: 4,000 * 150 = 600,000 tokens/day
* llama-3.3-70b (1,000 queries):
  * Input: 1,000 * 600 = 600,000 tokens/day
  * Output: 1,000 * 150 = 150,000 tokens/day

**Biggest Cost Driver:**
Definitely the 70B output tokens. Even though we route way fewer queries to it, big models cost significantly more per token than smaller ones.

**Highest-ROI Change:**
Semantic caching would be a huge win here. A lot of support questions are exactly the same (like asking how to reset a password). If we cache the answers and check them against new incoming queries, we could save a massive amount of LLM calls entirely.

**Optimization to Avoid:**
I definitely wouldn't want to blindly cut down the context chunks (like only sending 1 chunk) just to save input tokens. If the LLM doesn't have enough context, it will just hallucinate or say it doesn't know, which defeats the whole purpose of the bot.

---

## Q4 — What Is Broken

**Most Significant Flaw:**
Right now, the whole memory and vector index actually rebuilds from scratch every time the server starts up. Plus, the conversation memory is just living inside a Python dictionary in RAM.

**Why I shipped it anyway:**
For a take-home assignment dealing with only 30 static PDFs, doing the indexing in-memory during startup was the quickest way to get things working without needing to set up external databases.

**How to fix it:**
If this were going to production, I'd move the indexing process out of the web server entirely and put the vectors into a real persistent database like Pinecone or Postgres. That way, the API just queries the DB, starts up instantly, and we can scale it up horizontally safely.

---

## AI Usage

I built the core logic and architecture myself, but I did use AI minimally to speed up some boilerplate stuff and debug some UI annoyances:
- "Give me a quick regex pattern in Python to tokenize words and ignore punctuation."
- "Write a python snippet to iterate over all files in a directory and filter for .pdf extensions."

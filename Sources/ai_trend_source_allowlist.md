# AI Trend Source Allowlist

This file controls where Codex automation may look when it needs fresh AI engineering, LLM, agent, model, paper, or tooling signals.

## Network Safety

For scheduled daily/weekly research automation, keep internet access read-only.

Allowed HTTP methods:

```text
GET
HEAD
OPTIONS
```

Do not allow `POST`, `PUT`, `PATCH`, or `DELETE` for trend research jobs unless a future task explicitly needs to mutate a remote service.

## Daily Source Policy

.

## Weekly Source Policy



## Core Sources

```text
github.com
api.github.com
raw.githubusercontent.com
huggingface.co
cdn-lfs.huggingface.co
pypi.org
files.pythonhosted.org
npmjs.com
registry.npmjs.org
crates.io
hub.docker.com
```

## Papers And Research

```text
arxiv.org
export.arxiv.org
paperswithcode.com
semanticscholar.org
api.semanticscholar.org
openreview.net
aclweb.org
aclanthology.org
proceedings.mlr.press
neurips.cc
icml.cc
iclr.cc
scholar.google.com
```

Use `scholar.google.com` as a manual fallback or citation-chasing source only. Scheduled automation should prefer arXiv, OpenReview, Papers with Code, and Semantic Scholar.

## Discovery And Community

```text
news.ycombinator.com
hn.algolia.com
reddit.com
old.reddit.com
x.com
twitter.com
```

## AI Labs And Company Sources

```text
openai.com
platform.openai.com
anthropic.com
docs.anthropic.com
deepmind.google
ai.googleblog.com
ai.meta.com
mistral.ai
docs.mistral.ai
cohere.com
docs.cohere.com
nvidia.com
blogs.nvidia.com
microsoft.com
research.microsoft.com
microsoft.github.io
```

## Agent And AI Engineering Tooling

```text
langchain.com
blog.langchain.com
docs.langchain.com
langchain-ai.github.io
langgraph.dev
llamaindex.ai
docs.llamaindex.ai
modelcontextprotocol.io
docs.cursor.com
docs.together.ai
docs.fireworks.ai
docs.perplexity.ai
```

## News And Analysis

```text
the-decoder.com
venturebeat.com
techcrunch.com
simonwillison.net
latent.space
lilianweng.github.io
sebastianraschka.com
newsletter.pragmaticengineer.com
```

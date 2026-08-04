---
name: andrej-karpathy
type: person
tags: [ai-researcher, openai, tesla, stanford, llm-wiki, karpathy]
source_files: [nate-herk-karpathy-walkthrough]
domains: [06-AI-WORKFLOW]
created: 2026-05-16
updated: 2026-05-16
---

# Andrej Karpathy

AI researcher and educator. Former Director of AI at Tesla, co-founder of OpenAI, Stanford PhD. Known for karpathy.ai, nanoGPT, and popular AI education content.

## LLM Wiki Contribution

Posted a short tweet on X about using LLMs to build personal knowledge bases from raw source documents. The post went viral in April 2026. He followed up with a GitHub Gist formalizing the idea — intentionally leaving the prompt vague to encourage customization per project context.

**Core idea from Karpathy:** Give Claude Code raw data (PDFs, articles, transcripts). It auto-maintains an index, writes brief summaries, and builds a crosslinked wiki. At small scale (~100 articles, ~500k words), LLMs navigate this better than fancy RAG because they read indexes and follow links rather than similarity-searching chunks.

Quote: "I thought that I had to reach for fancy RAG, but the LLM has been pretty good about auto-maintaining index files and brief summaries of all documents."

He also noted that LLM health checks (linting) over the wiki can find inconsistent data, impute missing data via web searches, and flag interesting connections for new article candidates.

## Related

- [[../sources/nate-herk-karpathy-walkthrough|Nate Herk Walkthrough]]
- [[../concepts/llm-wiki-pattern|LLM Wiki Pattern]]
- [[../comparisons/wiki-vs-rag|Wiki vs RAG]]
- [[../analysis/why-wiki-compounds|Why Wiki Compounds]]

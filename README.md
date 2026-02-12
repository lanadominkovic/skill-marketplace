# Dataset Generator Marketplace

A Claude Code plugin marketplace for AI evaluation and benchmarking tools.

## Plugins

### dataset-generator

Generate high-quality evaluation datasets with adjustable difficulty levels from PDF documents for RAG system testing and benchmarking.

**Features:**
- Extract content from PDF documents
- Generate questions across 5 types: fact retrieval, multi-hop reasoning, comparative analysis, contextual summarization, and creative generation
- Adjustable difficulty levels: easy, medium, hard, or mixed
- Standard benchmark JSON output format
- Compatible with RAGAs and other evaluation frameworks

## Installation

### Add the marketplace

**From GitHub (recommended):**
```bash
/plugin marketplace add lanadominkovic/skill-marketplace
```

**From local directory (for testing):**
```bash
/plugin marketplace add ~/skill-marketplace
```

### Install the plugin

```bash
/plugin install dataset-generator-plugin@skill-marketplace
```

## Usage

After installation, use the `/dataset-generator` skill:

```bash
# Generate 20 mixed-difficulty questions
/dataset-generator ./pdfs

# Generate 30 hard questions
/dataset-generator ./pdfs hard_benchmark.json 30 hard

# Generate 15 easy questions for testing retrieval
/dataset-generator ./pdfs easy_test.json 15 easy
```

## Requirements

- Python 3.8+
- pypdf library (auto-installed if missing)
- Anthropic API key in environment
- PDF files in specified directory

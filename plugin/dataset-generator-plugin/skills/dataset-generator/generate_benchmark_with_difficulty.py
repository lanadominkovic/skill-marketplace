#!/usr/bin/env python3
"""
Generate benchmark evaluation datasets with adjustable difficulty levels from PDF documents.
Compatible with RAGAs and other evaluation frameworks.
"""

import os
import sys
import json
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any
import re


def install_pypdf():
    """Install pypdf if not available."""
    try:
        import pypdf
    except ImportError:
        print("⚠️  pypdf not found, installing...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'pypdf', '-q'])
        import pypdf


def load_pdfs(docs_path: str, chunk_size: int = 1000) -> tuple[List[str], Dict[str, int]]:
    """
    Load PDFs and chunk them based on difficulty requirements.

    Args:
        docs_path: Directory containing PDF files
        chunk_size: Target chunk size in characters

    Returns:
        tuple: (list of text chunks, stats dict)
    """
    import pypdf

    print(f"\n📂 Loading documents from {docs_path}...")
    print(f"   Chunk size: {chunk_size} chars")

    docs = []
    docs_dir = Path(docs_path)
    pdf_files = list(docs_dir.glob('*.pdf'))

    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {docs_path}")

    stats = {'files': len(pdf_files), 'chunks': 0, 'total_chars': 0}

    for file_path in pdf_files:
        print(f"   Processing {file_path.name}...")

        try:
            with open(file_path, 'rb') as f:
                pdf_reader = pypdf.PdfReader(f)
                full_text = ""
                for page in pdf_reader.pages:
                    full_text += page.extract_text() + "\n"

            # Clean text
            full_text = re.sub(r'\s+', ' ', full_text).strip()
            stats['total_chars'] += len(full_text)

            # Split into sentences
            sentences = re.split(r'([.!?]+\s+)', full_text)
            clean_sentences = []
            for i in range(0, len(sentences)-1, 2):
                sent = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
                if sent.strip():
                    clean_sentences.append(sent.strip())

            # Create chunks with 25% overlap
            overlap_size = chunk_size // 4
            chunks = []
            current_chunk = ""
            sentence_buffer = []

            for sent in clean_sentences:
                if len(current_chunk) + len(sent) + 1 < chunk_size:
                    current_chunk += sent + " "
                    sentence_buffer.append(sent)
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())

                        # Create overlap
                        overlap_chunk = ""
                        overlap_sentences = []
                        for s in reversed(sentence_buffer):
                            test_overlap = s + " " + overlap_chunk
                            if len(test_overlap) < overlap_size:
                                overlap_chunk = test_overlap
                                overlap_sentences.insert(0, s)
                            else:
                                break

                        current_chunk = overlap_chunk + sent + " "
                        sentence_buffer = overlap_sentences + [sent]
                    else:
                        current_chunk = sent + " "
                        sentence_buffer = [sent]

            if current_chunk:
                chunks.append(current_chunk.strip())

            print(f"   ✅ Extracted {len(chunks)} chunks")
            docs.extend(chunks)
            stats['chunks'] += len(chunks)

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n✅ Loaded {stats['chunks']} chunks from {stats['files']} PDFs ({stats['total_chars']:,} chars)")
    return docs, stats


def generate_dataset(pdf_dir: str, output_file: str, num_questions: int, difficulty: str):
    """
    Generate evaluation dataset with specified difficulty level.

    Args:
        pdf_dir: Directory containing PDF files
        output_file: Output JSON file path
        num_questions: Number of questions to generate
        difficulty: Difficulty level (easy, medium, hard, mixed)
    """
    install_pypdf()

    # Configure based on difficulty
    if difficulty == "easy":
        chunk_size = 400
        question_types = ["Fact Retrieval"]
        distribution = {"Fact Retrieval": 1.0}
    elif difficulty == "medium":
        chunk_size = 900
        question_types = ["Fact Retrieval", "Multi-hop Reasoning"]
        distribution = {"Fact Retrieval": 0.5, "Multi-hop Reasoning": 0.5}
    elif difficulty == "hard":
        chunk_size = 1300
        question_types = ["Multi-hop Reasoning", "Comparative Analysis", "Contextual Summarization"]
        distribution = {"Multi-hop Reasoning": 0.4, "Comparative Analysis": 0.3, "Contextual Summarization": 0.3}
    else:  # mixed
        chunk_size = 1000
        question_types = ["Fact Retrieval", "Multi-hop Reasoning", "Comparative Analysis",
                          "Contextual Summarization", "Creative Generation"]
        distribution = {
            "Fact Retrieval": 0.25,
            "Multi-hop Reasoning": 0.25,
            "Comparative Analysis": 0.20,
            "Contextual Summarization": 0.15,
            "Creative Generation": 0.15
        }

    print(f"\n🔨 DATASET GENERATOR")
    print(f"{'='*60}")
    print(f"   PDF Directory: {pdf_dir}")
    print(f"   Output File: {output_file}")
    print(f"   Questions: {num_questions}")
    print(f"   Difficulty: {difficulty}")
    print(f"   Chunk Size: {chunk_size} chars")
    print(f"{'='*60}\n")

    # Load documents
    start_time = time.time()
    docs, stats = load_pdfs(pdf_dir, chunk_size)

    if not docs:
        print("❌ No documents loaded. Exiting.")
        return

    # Save extracted content for analysis
    content_file = output_file.replace('.json', '_content.json')
    with open(content_file, 'w') as f:
        json.dump({'chunks': docs, 'stats': stats}, f, indent=2)
    print(f"💾 Saved extracted content to {content_file}")

    # Generate questions using Claude
    print(f"\n🤖 Generating {num_questions} questions...")
    print(f"   Question types: {', '.join(question_types)}")
    print(f"\n⚠️  This requires manual Claude interaction")
    print(f"\nNext steps:")
    print(f"1. Review extracted content in: {content_file}")
    print(f"2. Use Claude to analyze the content and generate questions")
    print(f"3. Follow the difficulty guidelines:")
    print(f"   - Easy: Single-passage, direct facts")
    print(f"   - Medium: 2-3 hop reasoning")
    print(f"   - Hard: Cross-document synthesis")
    print(f"4. Save questions to: {output_file}")

    elapsed = time.time() - start_time
    print(f"\n✅ Preparation completed in {elapsed:.2f}s")
    print(f"\nTemplate for {output_file}:")
    print(json.dumps([{
        "id": "doc-" + hashlib.md5(b"example").hexdigest()[:10],
        "question": "What is the main topic?",
        "answer": "The main topic is...",
        "question_type": question_types[0],
        "difficulty": difficulty,
        "evidence": ["Evidence passage 1", "Evidence passage 2"],
        "evidence_relations": "Evidence 1 provides X, Evidence 2 provides Y"
    }], indent=2))


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_benchmark_with_difficulty.py <pdf_dir> [output_file] [num_questions] [difficulty]")
        print("\nDifficulty levels: easy, medium, hard, mixed (default: mixed)")
        sys.exit(1)

    pdf_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "benchmark_dataset.json"
    num_questions = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    difficulty = sys.argv[4] if len(sys.argv) > 4 else "mixed"

    if difficulty not in ["easy", "medium", "hard", "mixed"]:
        print(f"❌ Invalid difficulty: {difficulty}")
        print("   Valid options: easy, medium, hard, mixed")
        sys.exit(1)

    generate_dataset(pdf_dir, output_file, num_questions, difficulty)


if __name__ == "__main__":
    main()

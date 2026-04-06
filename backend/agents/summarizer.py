import httpx
import json
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional, Union

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

PURPOSE_STYLES = {
    "general": {"tone": "balanced overview", "detail": "medium", "structure": "mixed"},
    "academic": {"tone": "formal academic", "detail": "high", "structure": "hierarchical"},
    "writing": {"tone": "clear engaging prose", "detail": "medium", "structure": "narrative"},
    "quick": {"tone": "concise", "detail": "low", "structure": "bulleted"},
    "presentation": {"tone": "highlights", "detail": "medium", "structure": "bulleted"},
    "comparative": {"tone": "analytical", "detail": "high", "structure": "contrasting"},
}


def _validate_input(paper: Dict, is_batch: bool = False) -> tuple[bool, str]:
    if not paper:
        return False, "Empty input received"
    
    if is_batch:
        if not isinstance(paper, list):
            return False, "Expected list of documents"
        if len(paper) == 0:
            return False, "Empty document list"
        return True, ""
    
    if isinstance(paper, dict):
        abstract = paper.get("abstract", "").strip()
        title = paper.get("title", "").strip()
        if not abstract and not title:
            return False, "No meaningful content (missing abstract and title)"
    
    return True, ""


def _calculate_confidence(paper: Dict, is_comparative: bool = False, docs: List[Dict] = None) -> float:
    score = 0.0
    max_score = 5.0 if not is_comparative else 6.0
    
    if not is_comparative:
        if paper.get("abstract", "").strip():
            score += 1.0
        if paper.get("title", "").strip():
            score += 0.5
        if paper.get("authors"):
            score += 0.5
        if paper.get("year"):
            score += 0.5
        if paper.get("methodology"):
            score += 0.5
        if paper.get("full_text") or paper.get("content"):
            score += 1.0
        if paper.get("keywords"):
            score += 0.5
    else:
        if docs:
            valid_docs = sum(1 for d in docs if d.get("abstract", "").strip() or d.get("title", "").strip())
            score += min(valid_docs / len(docs), 1.0) * 2.0
            
            titles = set(d.get("title", "") for d in docs if d.get("title"))
            score += 1.0 if len(titles) > 1 else 0.0
            
            years = set(str(d.get("year", "")) for d in docs if d.get("year"))
            score += 1.0 if len(years) > 1 else 0.0
            
            all_keywords = []
            for d in docs:
                all_keywords.extend(d.get("keywords", []))
            score += 1.0 if all_keywords else 0.0
            
            consistency = _check_consistency(docs)
            score += consistency * 1.0
    
    return round(score / max_score, 2)


def _check_consistency(docs: List[Dict]) -> float:
    if len(docs) < 2:
        return 0.5
    
    titles = [d.get("title", "").lower() for d in docs if d.get("title")]
    years = [str(d.get("year", "")) for d in docs if d.get("year")]
    
    title_dups = len(titles) - len(set(titles))
    year_dups = len(years) - len(set(years))
    
    if title_dups > len(docs) * 0.5:
        return 0.3
    return 0.8


def _handle_incomplete_input(paper: Dict, is_long: bool = False) -> Dict:
    title = paper.get("title", "Untitled Document")
    abstract = paper.get("abstract", "")
    
    if is_long:
        return {
            "derived_content": {
                "abstract_compression": f"Document titled '{title}' - extensive content provided.",
                "key_points": ["Document contains substantial content - summary focused on high-impact information"]
            },
            "inferred_content": {
                "explanation_approach": "Methodology inferred from content structure",
                "strengths": "Comprehensive content available for analysis",
                "limitations": "Content truncated for processing",
                "novelty_level": "Analysis based on provided excerpt"
            },
            "key_takeaway": f"'{title}' contains significant research content",
            "confidence_score": 0.6
        }
    
    if not abstract:
        return {
            "derived_content": {
                "abstract_compression": f"Document titled '{title}' - content not available for analysis.",
                "key_points": ["Insufficient information for detailed analysis"]
            },
            "inferred_content": {
                "explanation_approach": "Cannot be determined - insufficient input data",
                "strengths": "Unable to assess - incomplete input",
                "limitations": "Unable to assess - incomplete input",
                "novelty_level": "Unknown - insufficient information"
            },
            "key_takeaway": f"Document '{title}' exists but content analysis not possible",
            "confidence_score": 0.2
        }
    
    return None


def _detect_conflicts(docs: List[Dict]) -> List[str]:
    conflicts = []
    
    years = {}
    for d in docs:
        title = d.get("title", "")
        year = d.get("year")
        if year:
            if year in years:
                conflicts.append(f"Potential duplicate: '{title}' and existing document share year {year}")
            years[year] = title
    
    return conflicts


def _truncate_for_processing(text: str, max_length: int = 2000) -> str:
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "... [content truncated]"


async def summarize_paper(paper: Dict, purpose: str = "general") -> Dict:
    is_valid, error_msg = _validate_input(paper)
    if not is_valid:
        return _error_response(error_msg)
    
    title = paper.get("title", "Unknown Title")
    abstract = paper.get("abstract", "")
    authors = paper.get("authors", [])
    year = paper.get("year", "")
    keywords = paper.get("keywords", [])
    full_text = paper.get("full_text", "") or paper.get("content", "")
    
    is_long_doc = len(full_text) > 5000
    
    incomplete_result = _handle_incomplete_input(paper, is_long_doc)
    if incomplete_result:
        return incomplete_result
    
    keywords_str = ", ".join(keywords) if keywords else "Not provided"
    authors_str = ", ".join(authors[:3]) if authors else "Unknown"
    if authors and len(authors) > 3:
        authors_str += " et al."
    
    style = PURPOSE_STYLES.get(purpose, PURPOSE_STYLES["general"])
    
    if purpose == "quick":
        abstract_limit = 150
        key_points_limit = 3
    elif purpose == "presentation":
        abstract_limit = 200
        key_points_limit = 5
    else:
        abstract_limit = 300
        key_points_limit = 5
    
    truncated_abstract = _truncate_for_processing(abstract, 1500)
    
    prompt = f"""You are an advanced document summarizer optimized for {style['tone']} output.
Purpose: {purpose}
Detail level: {style['detail']}

Document:
- Title: {title}
- Authors: {authors_str}
- Year: {year}
- Keywords: {keywords_str}
- Abstract: {truncated_abstract}

Generate a JSON with exactly these fields:
1. "derived_content": Object with directly extracted information:
   - "abstract_compression": 2-3 sentence summary (max {abstract_limit} chars)
   - "key_points": List of {key_points_limit}-5 points ranked by importance (derived from document)
2. "inferred_content": Object with inferred analysis:
   - "explanation_approach": Method/approach used (1-2 sentences)
   - "strengths": Notable strengths (1-2 sentences)
   - "limitations": Known/inferred limitations (1-2 sentences)
   - "novelty_level": Rating (Novel/Incremental/Building on existing/Standard) with justification
3. "key_takeaway": One clear takeaway (1-2 sentences)
4. "confidence_score": Float 0.0-1.0 based on input completeness

Distinguish clearly between DERIVED (directly from text) and INFERRED (your analysis) content.
If insufficient info for a field, use "Information not available".
Do not include any text outside the JSON."""

    if not abstract or len(abstract.strip()) < 20:
        return {
            "derived_content": {
                "abstract_compression": f"Document: {title} - abstract too brief for detailed analysis.",
                "key_points": ["Abstract content insufficient for detailed extraction"]
            },
            "inferred_content": {
                "explanation_approach": "Cannot be determined from provided input",
                "strengths": "Insufficient information to assess",
                "limitations": "Insufficient information to assess",
                "novelty_level": "Unknown - minimal input"
            },
            "key_takeaway": f"Document '{title}' requires more content for analysis",
            "confidence_score": 0.3
        }

    if not GEMINI_API_KEY:
        return {
            "derived_content": {
                "abstract_compression": f"Summary of: {title}. {abstract[:200]}...",
                "key_points": ["API key not configured - using basic extraction"]
            },
            "inferred_content": {
                "explanation_approach": "Cannot determine - API not configured",
                "strengths": "Cannot assess - API not configured",
                "limitations": "Cannot assess - API not configured",
                "novelty_level": "Unknown - API not configured"
            },
            "key_takeaway": f"Configure API key for full analysis of '{title}'",
            "confidence_score": _calculate_confidence(paper)
        }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048},
                },
            )
            response.raise_for_status()
            data = response.json()

            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            text = _clean_json_response(text)
            summary = json.loads(text)
            
            confidence = summary.get("confidence_score")
            if confidence is None:
                confidence = _calculate_confidence(paper)
            
            return {
                "derived_content": {
                    "abstract_compression": summary.get("derived_content", {}).get("abstract_compression", "Unable to generate summary"),
                    "key_points": summary.get("derived_content", {}).get("key_points", [])
                },
                "inferred_content": {
                    "explanation_approach": summary.get("inferred_content", {}).get("explanation_approach", "Information not available"),
                    "strengths": summary.get("inferred_content", {}).get("strengths", "Information not available"),
                    "limitations": summary.get("inferred_content", {}).get("limitations", "Information not available"),
                    "novelty_level": summary.get("inferred_content", {}).get("novelty_level", "Unknown")
                },
                "key_takeaway": summary.get("key_takeaway", "Unable to extract"),
                "confidence_score": round(confidence, 2)
            }
    except json.JSONDecodeError as e:
        print(f"JSON parsing error for paper summary {title}: {e}")
        return _error_response("JSON parsing error", title)
    except Exception as e:
        print(f"Summary generation error for paper {title}: {e}")
        return _error_response(str(e), title)


def _error_response(error_msg: str, title: str = "Document") -> Dict:
    return {
        "derived_content": {
            "abstract_compression": f"Error: {error_msg}",
            "key_points": [error_msg]
        },
        "inferred_content": {
            "explanation_approach": "N/A",
            "strengths": "N/A",
            "limitations": "N/A",
            "novelty_level": "Unknown"
        },
        "key_takeaway": "Unable to process input",
        "confidence_score": 0.0
    }


def _clean_json_response(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


async def summarize_documents(documents: List[Dict], purpose: str = "general") -> Dict:
    is_valid, error_msg = _validate_input(documents, is_batch=True)
    if not is_valid:
        return {
            "derived_content": {
                "common_themes": [],
                "key_combined_insights": []
            },
            "inferred_content": {
                "differences": [error_msg],
                "gaps": ["Input validation failed"]
            },
            "unified_summary": f"Error: {error_msg}",
            "confidence_score": 0.0
        }
    
    if len(documents) == 1:
        single_result = await summarize_paper(documents[0], purpose)
        return {
            "derived_content": {
                "common_themes": single_result.get("derived_content", {}).get("key_points", []),
                "key_combined_insights": []
            },
            "inferred_content": {
                "differences": [],
                "gaps": ["Only one document - comparative analysis not applicable"]
            },
            "unified_summary": single_result.get("derived_content", {}).get("abstract_compression", ""),
            "confidence_score": single_result.get("confidence_score", 0.5)
        }
    
    unique_docs = _deduplicate_documents(documents)
    
    if len(unique_docs) < 2:
        return {
            "derived_content": {
                "common_themes": [],
                "key_combined_insights": []
            },
            "inferred_content": {
                "differences": ["Insufficient unique documents for comparison"],
                "gaps": ["Need at least 2 unique documents"]
            },
            "unified_summary": "Duplicate or insufficient documents provided",
            "confidence_score": 0.2
        }
    
    doc_summaries = _prepare_doc_summaries(unique_docs)
    
    style = PURPOSE_STYLES.get(purpose, PURPOSE_STYLES["general"])
    style_instruction = f"Use {style['tone']} tone. Detail level: {style['detail']}. Structure: {style['structure']}."
    
    docs_text = "\n\n".join([
        f"Doc {s['index']}: \"{s['title']}\" by {s['authors']} ({s['year']}). Abstract: {s['abstract']}"
        for s in doc_summaries
    ])
    
    conflicts = _detect_conflicts(unique_docs)
    conflict_note = f"\nNote: Potential conflicts detected: {conflicts}" if conflicts else ""

    prompt = f"""You are an advanced comparative document analyzer.
{style_instruction}

Purpose: {purpose}

Documents:
{docs_text}{conflict_note}

Return ONLY valid JSON with these fields:
1. "derived_content": Object with directly extracted info:
   - "common_themes": 3-6 themes ranked by frequency
   - "key_combined_insights": Key insights across all documents
2. "inferred_content": Object with analysis:
   - "differences": Contradictions or conflicting viewpoints
   - "gaps": Topics NOT covered by any document
3. "unified_summary": Coherent synthesis (3-5 sentences)
4. "confidence_score": Float 0.0-1.0 based on consistency and coverage

Clearly identify contradictions when present.
Use "Information not available" when data is insufficient."""

    if not GEMINI_API_KEY:
        return _fallback_comparative_summary(unique_docs)

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.5, "maxOutputTokens": 3072},
                },
            )
            response.raise_for_status()
            data = response.json()

            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            text = _clean_json_response(text)
            result = json.loads(text)
            
            confidence = result.get("confidence_score")
            if confidence is None:
                confidence = _calculate_confidence({}, is_comparative=True, docs=unique_docs)
            
            return {
                "derived_content": {
                    "common_themes": result.get("derived_content", {}).get("common_themes", []),
                    "key_combined_insights": result.get("derived_content", {}).get("key_combined_insights", [])
                },
                "inferred_content": {
                    "differences": result.get("inferred_content", {}).get("differences", []),
                    "gaps": result.get("inferred_content", {}).get("gaps", [])
                },
                "unified_summary": result.get("unified_summary", "Unable to generate unified summary"),
                "confidence_score": round(confidence, 2)
            }
    except json.JSONDecodeError as e:
        print(f"JSON parsing error in comparative summary: {e}")
        return _fallback_comparative_summary(unique_docs, error=True)
    except Exception as e:
        print(f"Comparative summary error: {e}")
        return _fallback_comparative_summary(unique_docs, error=True)


def _deduplicate_documents(documents: List[Dict]) -> List[Dict]:
    seen_titles = set()
    unique_docs = []
    
    for doc in documents:
        title = doc.get("title", "").strip().lower()
        if not title:
            unique_docs.append(doc)
            continue
        if title not in seen_titles:
            seen_titles.add(title)
            unique_docs.append(doc)
    
    return unique_docs


def _prepare_doc_summaries(docs: List[Dict]) -> List[Dict]:
    doc_summaries = []
    for i, doc in enumerate(docs):
        title = doc.get("title", f"Document {i+1}")
        abstract = doc.get("abstract", "")
        year = doc.get("year", "Unknown")
        authors = doc.get("authors", ["Unknown"])
        
        authors_str = ", ".join(authors[:3]) if authors else "Unknown"
        if authors and len(authors) > 3:
            authors_str += " et al."
        
        doc_summaries.append({
            "index": len(doc_summaries) + 1,
            "title": title,
            "authors": authors_str,
            "year": year,
            "abstract": _truncate_for_processing(abstract, 800) if abstract else "No abstract"
        })
    
    return doc_summaries


def _fallback_comparative_summary(docs: List[Dict], error: bool = False) -> Dict:
    common = []
    titles = []
    keywords_set = set()
    
    for doc in docs:
        if doc.get("title"):
            titles.append(doc["title"])
        if doc.get("keywords"):
            keywords_set.update(doc.get("keywords", [])[:3])
    
    common = list(keywords_set)[:5] if keywords_set else titles[:3]
    
    status = "Analysis failed" if error else "API key not configured"
    
    return {
        "derived_content": {
            "common_themes": common,
            "key_combined_insights": ["Basic keyword extraction only - configure API for full analysis"]
        },
        "inferred_content": {
            "differences": [f"{status} - cannot perform full comparative analysis"],
            "gaps": ["API key required for gap analysis"]
        },
        "unified_summary": f"Analysis of {len(docs)} documents. {status}.",
        "confidence_score": _calculate_confidence({}, is_comparative=True, docs=docs)
    }


async def synthesize_papers(papers: List[Dict], purpose: str = "academic") -> str:
    if not papers:
        return "No papers selected for synthesis."
    
    result = await summarize_documents(papers, purpose=purpose)
    return result.get("unified_summary", "Error generating synthesis.")

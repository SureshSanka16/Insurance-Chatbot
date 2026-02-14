"""
Simple RAG Service - Efficient JSON-based knowledge retrieval for Vantage Insurance.

This service provides fast, accurate policy information retrieval using:
1. Structured JSON knowledge base with 99 pre-chunked policy entries
2. Keyword and tag-based search for instant results
3. Policy type filtering for context-aware responses
"""

import json
import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("simple_rag")

# Constants
CHUNK_SIZE = 99  # Max results per query batch
KNOWLEDGE_BASE_PATH = Path(__file__).parent / "policy_knowledge_base.json"

# Policy type mapping (frontend tab -> JSON policy_type)
TAB_TO_POLICY_TYPE = {
    "Vehicle": "vehicle_insurance",
    "Health": "health_insurance",
    "Life": "life_insurance",
    "Home": "home_insurance",
    "Property": "home_insurance",
}

# Cache for knowledge base
_knowledge_base: List[Dict[str, Any]] = []


def load_knowledge_base() -> List[Dict[str, Any]]:
    """Load and cache the knowledge base from JSON file."""
    global _knowledge_base
    
    if _knowledge_base:
        return _knowledge_base
    
    try:
        if KNOWLEDGE_BASE_PATH.exists():
            with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
                _knowledge_base = json.load(f)
            logger.info(f"Loaded {len(_knowledge_base)} knowledge base entries")
        else:
            logger.warning(f"Knowledge base not found at {KNOWLEDGE_BASE_PATH}")
            _knowledge_base = []
    except Exception as e:
        logger.error(f"Failed to load knowledge base: {e}")
        _knowledge_base = []
    
    return _knowledge_base


def normalize_query(query: str) -> str:
    """Normalize query for better matching."""
    # Convert to lowercase and remove extra whitespace
    query = query.lower().strip()
    query = re.sub(r'\s+', ' ', query)
    return query


def extract_keywords(query: str) -> List[str]:
    """Extract significant keywords from query."""
    # Remove common stop words
    stop_words = {
        'what', 'is', 'are', 'the', 'a', 'an', 'my', 'your', 'does', 'do',
        'how', 'can', 'i', 'me', 'we', 'you', 'this', 'that', 'these', 'those',
        'in', 'on', 'at', 'to', 'for', 'of', 'with', 'about', 'tell', 'please',
        'would', 'could', 'should', 'will', 'be', 'have', 'has', 'had', 'get',
        'know', 'want', 'need', 'like', 'give', 'show', 'explain'
    }
    
    # Tokenize and filter
    words = re.findall(r'\b\w+\b', query.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    return keywords


def calculate_relevance_score(entry: Dict[str, Any], keywords: List[str], query: str) -> float:
    """Calculate relevance score for a knowledge base entry."""
    score = 0.0
    
    text_lower = entry.get("text", "").lower()
    topic_lower = entry.get("topic", "").lower()
    section_lower = entry.get("section", "").lower()
    tags = [t.lower() for t in entry.get("tags", [])]
    
    # Keyword matches in text (highest weight)
    for keyword in keywords:
        if keyword in text_lower:
            score += 3.0
        if keyword in topic_lower:
            score += 5.0  # Topic match is very relevant
        if keyword in section_lower:
            score += 2.0
        if keyword in tags:
            score += 4.0  # Tag match is highly relevant
    
    # Exact phrase matches (bonus points)
    if len(keywords) >= 2:
        phrase = ' '.join(keywords[:3])
        if phrase in text_lower:
            score += 10.0
    
    # Section-specific boosts based on query intent
    query_lower = query.lower()
    
    if any(w in query_lower for w in ['cover', 'covered', 'coverage', 'include', 'protect']):
        if section_lower == 'coverage':
            score += 5.0
    
    if any(w in query_lower for w in ['limit', 'maximum', 'cap', 'amount', 'how much']):
        if section_lower == 'limits':
            score += 5.0
    
    if any(w in query_lower for w in ['exclude', 'exclusion', 'not cover', 'exception']):
        if section_lower == 'exclusions':
            score += 5.0
    
    if any(w in query_lower for w in ['claim', 'file', 'submit', 'process', 'procedure']):
        if section_lower == 'claims':
            score += 5.0
    
    if any(w in query_lower for w in ['wait', 'waiting', 'period', 'before']):
        if section_lower in ['waiting_periods', 'exclusions']:
            score += 4.0
    
    if any(w in query_lower for w in ['define', 'definition', 'mean', 'what is']):
        if section_lower == 'definitions':
            score += 4.0
    
    if any(w in query_lower for w in ['contact', 'help', 'support', 'complaint', 'grievance']):
        if section_lower == 'grievance':
            score += 5.0
    
    if any(w in query_lower for w in ['cancel', 'refund', 'terminate']):
        if section_lower == 'general_terms':
            score += 4.0
    
    if any(w in query_lower for w in ['hospital', 'network', 'cashless']):
        if section_lower in ['network_hospitals', 'claims']:
            score += 4.0
    
    return score


def search_knowledge_base(
    query: str,
    policy_type: Optional[str] = None,
    max_results: int = CHUNK_SIZE
) -> List[Dict[str, Any]]:
    """
    Search the knowledge base for relevant entries.
    
    Args:
        query: User's question or search query
        policy_type: Optional filter by policy type (Vehicle, Health, Life, Home)
        max_results: Maximum number of results to return
    
    Returns:
        List of relevant knowledge base entries with scores
    """
    kb = load_knowledge_base()
    
    if not kb:
        return []
    
    query_normalized = normalize_query(query)
    keywords = extract_keywords(query_normalized)
    
    logger.info(f"Searching KB with keywords: {keywords}, policy_type: {policy_type}")
    
    # Filter by policy type if specified
    filtered_kb = kb
    if policy_type:
        policy_type_key = TAB_TO_POLICY_TYPE.get(policy_type, policy_type.lower() + "_insurance")
        filtered_kb = [e for e in kb if e.get("policy_type") == policy_type_key]
        logger.info(f"Filtered to {len(filtered_kb)} entries for {policy_type_key}")
    
    # Score all entries
    scored_results = []
    for entry in filtered_kb:
        score = calculate_relevance_score(entry, keywords, query_normalized)
        if score > 0:
            scored_results.append({
                **entry,
                "_score": score
            })
    
    # Sort by score descending and limit results
    scored_results.sort(key=lambda x: x["_score"], reverse=True)
    top_results = scored_results[:max_results]
    
    logger.info(f"Found {len(scored_results)} matches, returning top {len(top_results)}")
    
    return top_results


def get_all_by_section(
    section: str,
    policy_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get all entries for a specific section."""
    kb = load_knowledge_base()
    
    results = [e for e in kb if e.get("section") == section]
    
    if policy_type:
        policy_type_key = TAB_TO_POLICY_TYPE.get(policy_type, policy_type.lower() + "_insurance")
        results = [e for e in results if e.get("policy_type") == policy_type_key]
    
    return results


def get_policy_summary(policy_type: str) -> str:
    """Get a brief summary of a policy type's key information."""
    kb = load_knowledge_base()
    policy_type_key = TAB_TO_POLICY_TYPE.get(policy_type, policy_type.lower() + "_insurance")
    
    entries = [e for e in kb if e.get("policy_type") == policy_type_key]
    
    if not entries:
        return f"No information available for {policy_type} insurance."
    
    # Get key sections
    coverage = [e for e in entries if e.get("section") == "coverage"]
    limits = [e for e in entries if e.get("section") == "limits"]
    exclusions = [e for e in entries if e.get("section") == "exclusions"]
    
    summary_parts = []
    
    # Product name
    product = entries[0].get("product", f"{policy_type} Insurance")
    summary_parts.append(f"**{product}**\n")
    
    # Key coverage points
    if coverage:
        summary_parts.append("**Key Coverage:**")
        for c in coverage[:5]:
            summary_parts.append(f"- {c.get('text', '')[:150]}...")
    
    # Limits
    if limits:
        summary_parts.append("\n**Limits:**")
        for l in limits[:3]:
            summary_parts.append(f"- {l.get('text', '')}")
    
    return "\n".join(summary_parts)


def retrieve_with_fallback(
    query: str,
    policy_type: Optional[str] = None,
    top_k: int = 10
) -> Dict[str, Any]:
    """
    Main retrieval function with formatted output for the AI router.
    
    Returns a dict compatible with the ai.py router expectations:
    {
        "context_text": str,  # Combined text from relevant entries
        "sources": List[Dict],  # Source information for each entry
        "source_type": str,  # "knowledge_base" or "no_match"
        "matched_sections": List[str]  # Sections that matched
    }
    """
    results = search_knowledge_base(query, policy_type, max_results=top_k)
    
    if not results:
        # Try without policy filter as fallback
        if policy_type:
            results = search_knowledge_base(query, policy_type=None, max_results=top_k)
    
    if not results:
        return {
            "context_text": "",
            "sources": [],
            "source_type": "no_match",
            "matched_sections": []
        }
    
    # Build context text
    context_parts = []
    sources = []
    matched_sections = set()
    
    for entry in results:
        # Format each entry
        product = entry.get("product", "Vantage Insurance")
        section = entry.get("section", "general")
        topic = entry.get("topic", "").replace("_", " ").title()
        text = entry.get("text", "")
        
        context_parts.append(f"[{product} - {section.title()}] {topic}: {text}")
        
        matched_sections.add(section)
        
        sources.append({
            "doc_id": entry.get("doc_id", ""),
            "product": product,
            "policy_type": entry.get("policy_type", ""),
            "section": section,
            "topic": topic,
            "source": product,
            "matched_sections": [section],
            "score": entry.get("_score", 0)
        })
    
    context_text = "\n\n".join(context_parts)
    
    return {
        "context_text": context_text,
        "sources": sources,
        "source_type": "knowledge_base",
        "matched_sections": list(matched_sections)
    }


# Alias for backward compatibility
async def retrieve_context_async(
    query: str,
    policy_type: Optional[str] = None,
    top_k: int = 10
) -> Dict[str, Any]:
    """Async wrapper for retrieve_with_fallback."""
    return retrieve_with_fallback(query, policy_type, top_k)


# Initialize on module load
load_knowledge_base()

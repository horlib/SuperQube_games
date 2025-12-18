# -*- coding: utf-8 -*-
"""Rule-based pricing snippet extraction (NO LLM hallucination)."""

import re

from ptm.schemas import TavilySource

# Maximum snippet length to keep prompts safe
MAX_SNIPPET_LENGTH = 500


class ExtractionError(Exception):
    """Exception raised during extraction."""


def extract_pricing_snippets(sources: list[TavilySource]) -> list[str]:
    """Extract pricing-related snippets from sources using rule-based heuristics.

    This function ONLY extracts verbatim text from sources. It does NOT generate
    or invent any text. All snippets are direct substrings from source content.

    Args:
        sources: List of TavilySource objects

    Returns:
        List of verbatim pricing snippets (truncated to safe length)
    """
    snippets = []

    for source in sources:
        content = source.content
        if not content:
            continue

        # Extract snippets using heuristics
        extracted = _extract_with_heuristics(content)
        snippets.extend(extracted)

    # Truncate snippets to safe length
    truncated = [_truncate_snippet(s) for s in snippets]

    # Remove duplicates while preserving order
    seen = set()
    unique_snippets = []
    for snippet in truncated:
        if snippet not in seen:
            seen.add(snippet)
            unique_snippets.append(snippet)

    return unique_snippets


def _extract_with_heuristics(content: str) -> list[str]:
    """Extract pricing snippets using rule-based heuristics.

    Heuristics:
    - Look for currency symbols ($, €, £, ¥, etc.)
    - Look for "starts at" patterns
    - Look for "per month" / "per year" patterns
    - Look for price ranges

    Args:
        content: Source content text

    Returns:
        List of extracted snippets
    """
    snippets = []

    # Pattern 1: Currency symbol followed by numbers
    # Matches: $99, €50, £30, ¥1000, etc.
    currency_pattern = r"[€$£¥₹]\s*\d+(?:[.,]\d+)?(?:\s*/\s*(?:month|year|mo|yr|day|wk))?"

    # Pattern 2: "starts at" or "from" with price
    starts_at_pattern = r"(?:starts?\s+at|from|beginning\s+at)\s+[€$£¥₹]\s*\d+(?:[.,]\d+)?"

    # Pattern 3: "per month" / "per year" patterns
    per_period_pattern = (
        r"\d+(?:[.,]\d+)?\s*(?:USD|EUR|GBP|JPY|INR)?\s*(?:per|/)\s*(?:month|year|mo|yr|day|wk)"
    )

    # Pattern 4: Price ranges (e.g., "$99-$199")
    price_range_pattern = r"[€$£¥₹]\s*\d+(?:[.,]\d+)?\s*[-–—]\s*[€$£¥₹]?\s*\d+(?:[.,]\d+)?"

    # Combine all patterns
    all_patterns = [
        currency_pattern,
        starts_at_pattern,
        per_period_pattern,
        price_range_pattern,
    ]

    for pattern in all_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            # Extract context around the match (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            snippet = content[start:end].strip()

            if snippet and len(snippet) > 10:  # Minimum snippet length
                snippets.append(snippet)

    # Also look for lines containing pricing keywords
    lines = content.split("\n")
    pricing_keywords = ["price", "pricing", "cost", "plan", "tier", "subscription"]

    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in pricing_keywords):
            # Check if line contains currency or numbers
            if re.search(r"[€$£¥₹]\s*\d+|\d+\s*(?:USD|EUR|GBP|JPY|INR)", line):
                if line.strip() and len(line.strip()) > 10:
                    snippets.append(line.strip())

    return snippets


def _truncate_snippet(snippet: str) -> str:
    """Truncate snippet to safe prompt length.

    Args:
        snippet: Snippet text

    Returns:
        Truncated snippet
    """
    if len(snippet) <= MAX_SNIPPET_LENGTH:
        return snippet

    # Truncate and add ellipsis
    return snippet[: MAX_SNIPPET_LENGTH - 3] + "..."


def extract_price_texts(snippets: list[str]) -> list[str]:
    """Extract just the price text portions from snippets.

    This extracts only the price portions (e.g., "$99/month") from snippets,
    not the full context.

    Args:
        snippets: List of pricing snippets

    Returns:
        List of extracted price texts
    """
    price_texts = []

    # Pattern to match price expressions
    price_pattern = r"[€$£¥₹]\s*\d+(?:[.,]\d+)?(?:\s*(?:USD|EUR|GBP|JPY|INR)?\s*(?:per|/)\s*(?:month|year|mo|yr|day|wk))?"

    for snippet in snippets:
        matches = re.findall(price_pattern, snippet, re.IGNORECASE)
        for match in matches:
            price_text = match.strip()
            if price_text and price_text not in price_texts:
                price_texts.append(price_text)

    return price_texts


def extract_product_attributes(sources: list[TavilySource]) -> dict[str, str | list[str] | None]:
    """Extract product attributes from sources using heuristics.
    
    Extracts category, target customer, key features, product description,
    problem statement, decision context, and payment model from source content
    to enable better competitor matching.
    
    Args:
        sources: List of TavilySource objects
        
    Returns:
        Dictionary with keys: category, target_customer, key_features, product_description,
        problem_statement, decision_context, payment_model
    """
    all_content = " ".join([s.content for s in sources if s.content])
    if not all_content:
        return {
            "category": None,
            "target_customer": None,
            "key_features": [],
            "product_description": None,
            "problem_statement": None,
            "decision_context": None,
            "payment_model": None,
        }
    
    category = _extract_category(all_content)
    target_customer = _extract_target_customer(all_content)
    key_features = _extract_key_features(all_content)
    product_description = _extract_product_description(all_content)
    problem_statement = _extract_problem_statement(all_content)
    decision_context = _extract_decision_context(all_content)
    payment_model = _extract_payment_model(all_content)
    
    return {
        "category": category,
        "target_customer": target_customer,
        "key_features": key_features,
        "product_description": product_description,
        "problem_statement": problem_statement,
        "decision_context": decision_context,
        "payment_model": payment_model,
    }


def _extract_category(content: str) -> str | None:
    """Extract product category from content.
    
    Looks for common category indicators like "SaaS", "project management",
    "design tool", etc.
    
    Args:
        content: Source content text
        
    Returns:
        Extracted category or None
    """
    content_lower = content.lower()
    
    # Common category patterns
    category_patterns = [
        (r"(?:is|a|an)\s+(?:a|an)?\s*([a-z\s]+?)\s+(?:tool|platform|software|app|service|solution)",
         ["tool", "platform", "software", "app", "service", "solution"]),
        (r"(?:category|type|kind):\s*([a-z\s]+)", None),
        (r"([a-z\s]+?)\s+software", ["software"]),
        (r"([a-z\s]+?)\s+platform", ["platform"]),
    ]
    
    # Common categories to look for
    known_categories = [
        "saas", "project management", "design", "crm", "marketing",
        "analytics", "collaboration", "communication", "productivity",
        "development", "code", "database", "cloud", "storage", "security",
        "accounting", "finance", "hr", "human resources", "e-commerce",
        "cms", "content management", "cms", "blogging", "email",
    ]
    
    # Check for known categories
    for category in known_categories:
        if category in content_lower:
            # Extract context around the category mention
            pattern = rf"\b{re.escape(category)}\b"
            if re.search(pattern, content_lower):
                return category.title()
    
    # Try pattern matching
    for pattern, suffixes in category_patterns:
        matches = re.finditer(pattern, content_lower, re.IGNORECASE)
        for match in matches:
            extracted = match.group(1).strip()
            if len(extracted) > 2 and len(extracted) < 50:
                return extracted.title()
    
    return None


def _extract_target_customer(content: str) -> str | None:
    """Extract target customer segment from content.
    
    Args:
        content: Source content text
        
    Returns:
        Extracted target customer segment or None
    """
    content_lower = content.lower()
    
    # Common target customer patterns
    customer_patterns = [
        r"(?:for|targeting|designed for|built for)\s+([a-z\s]+?)(?:\.|,|$)",
        r"(?:small business|enterprise|startup|individual|team|developer|designer|marketer)",
    ]
    
    # Known customer segments
    known_segments = [
        "small business", "enterprise", "startup", "individual", "team",
        "developer", "designer", "marketer", "freelancer", "agency",
        "non-profit", "education", "student",
    ]
    
    # Check for known segments
    for segment in known_segments:
        pattern = rf"\b{re.escape(segment)}\b"
        if re.search(pattern, content_lower):
            return segment.title()
    
    # Try pattern matching
    for pattern in customer_patterns:
        matches = re.finditer(pattern, content_lower, re.IGNORECASE)
        for match in matches:
            extracted = match.group(1).strip() if match.groups() else match.group(0).strip()
            if len(extracted) > 2 and len(extracted) < 50:
                return extracted.title()
    
    return None


def _extract_key_features(content: str) -> list[str]:
    """Extract key features from content.
    
    Args:
        content: Source content text
        
    Returns:
        List of extracted features
    """
    features = []
    content_lower = content.lower()
    
    # Common feature indicators
    feature_patterns = [
        r"(?:features?|includes?|offers?|provides?|supports?):\s*([^\.]+)",
        r"(?:✓|•|–|—)\s*([^\.\n]+)",
        r"(?:with|including)\s+([^\.]+)",
    ]
    
    # Common features to look for
    known_features = [
        "collaboration", "real-time", "cloud", "mobile", "api", "integration",
        "analytics", "reporting", "automation", "workflow", "templates",
        "customization", "security", "encryption", "backup", "sync",
        "export", "import", "search", "filter", "notifications",
    ]
    
    # Extract from patterns
    for pattern in feature_patterns:
        matches = re.finditer(pattern, content_lower, re.IGNORECASE)
        for match in matches:
            feature_text = match.group(1).strip()
            # Split by common separators
            parts = re.split(r"[,\n;]", feature_text)
            for part in parts:
                part = part.strip()
                if len(part) > 3 and len(part) < 100:
                    features.append(part.title())
    
    # Check for known features
    for feature in known_features:
        if feature in content_lower:
            features.append(feature.title())
    
    # Remove duplicates and limit
    unique_features = []
    seen = set()
    for feature in features:
        feature_lower = feature.lower()
        if feature_lower not in seen:
            seen.add(feature_lower)
            unique_features.append(feature)
            if len(unique_features) >= 10:  # Limit to 10 features
                break
    
    return unique_features


def _extract_product_description(content: str) -> str | None:
    """Extract brief product description from content.
    
    Args:
        content: Source content text
        
    Returns:
        Brief product description or None
    """
    # Look for description patterns
    description_patterns = [
        r"(?:is|are)\s+([^\.]{20,200})",
        r"(?:description|about|overview):\s*([^\.]{20,200})",
    ]
    
    # Try to find first sentence or short paragraph
    sentences = re.split(r"[\.\n]", content)
    for sentence in sentences:
        sentence = sentence.strip()
        if 30 < len(sentence) < 300:
            # Check if it's not just pricing info
            if not re.search(r"[€$£¥₹]\s*\d+", sentence):
                return sentence
    
    # Try pattern matching
    for pattern in description_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            description = match.group(1).strip()
            if 20 < len(description) < 300:
                return description
    
    return None


def _extract_problem_statement(content: str) -> str | None:
    """Extract problem statement from content.
    
    Looks for phrases indicating what problem the product solves.
    
    Args:
        content: Source content text
        
    Returns:
        Extracted problem statement or None
    """
    content_lower = content.lower()
    
    # Patterns for problem statements
    problem_patterns = [
        r"(?:solves?|addresses?|fixes?|helps? with|designed to|built to|aims? to)\s+([^\.]{10,150})",
        r"(?:problem|issue|challenge|need|pain point):\s*([^\.]{10,150})",
        r"(?:for|to)\s+([^\.]{10,100})\s+(?:problems?|issues?|challenges?|needs?)",
        r"(?:helps?|enables?|allows?)\s+([^\.]{10,150})",
    ]
    
    for pattern in problem_patterns:
        matches = re.finditer(pattern, content_lower, re.IGNORECASE)
        for match in matches:
            problem_text = match.group(1).strip()
            if 10 < len(problem_text) < 200:
                # Clean up the text
                problem_text = re.sub(r'\s+', ' ', problem_text)
                return problem_text.capitalize()
    
    # Look for common problem indicators
    problem_keywords = [
        "manage", "organize", "track", "automate", "collaborate",
        "communicate", "analyze", "create", "design", "develop",
        "monitor", "optimize", "improve", "streamline", "simplify",
    ]
    
    sentences = re.split(r'[\.\n]', content)
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in problem_keywords):
            if 20 < len(sentence) < 200:
                return sentence.strip().capitalize()
    
    return None


def _extract_decision_context(content: str) -> str | None:
    """Extract decision context from content.
    
    Looks for information about who decides, when, and why.
    
    Args:
        content: Source content text
        
    Returns:
        Extracted decision context or None
    """
    content_lower = content.lower()
    
    # Patterns for decision context
    context_patterns = [
        r"(?:for|designed for|built for|targets?)\s+([^\.]{10,100})\s+(?:teams?|users?|companies?|businesses?|individuals?)",
        r"(?:perfect for|ideal for|best for|suited for)\s+([^\.]{10,100})",
        r"([^\.]{10,100})\s+(?:should|can|will|might)\s+(?:use|choose|select|consider)",
        r"(?:when|if)\s+([^\.]{10,100})\s+(?:need|want|require|looking for)",
    ]
    
    # Known decision contexts
    known_contexts = [
        "small business", "startup", "enterprise", "team", "individual",
        "marketing team", "development team", "design team", "sales team",
        "content creators", "developers", "designers", "marketers",
        "project managers", "product managers", "business owners",
    ]
    
    # Check for known contexts first
    for context in known_contexts:
        pattern = rf"\b{re.escape(context)}\b"
        if re.search(pattern, content_lower):
            # Try to extract surrounding context
            matches = re.finditer(pattern, content_lower)
            for match in matches:
                start = max(0, match.start() - 30)
                end = min(len(content_lower), match.end() + 50)
                context_text = content[start:end].strip()
                if 10 < len(context_text) < 150:
                    return context_text.capitalize()
    
    # Try pattern matching
    for pattern in context_patterns:
        matches = re.finditer(pattern, content_lower, re.IGNORECASE)
        for match in matches:
            context_text = match.group(1).strip()
            if 10 < len(context_text) < 150:
                return context_text.capitalize()
    
    return None


def _extract_payment_model(content: str) -> str | None:
    """Extract payment model from content.
    
    Looks for information about how the product is paid for.
    
    Args:
        content: Source content text
        
    Returns:
        Extracted payment model or None
    """
    content_lower = content.lower()
    
    # Payment model patterns
    payment_models = {
        "subscription": ["subscription", "monthly", "yearly", "annual", "recurring", "per month", "per year"],
        "one-time": ["one-time", "one time", "lifetime", "single payment", "pay once"],
        "per-seat": ["per seat", "per user", "per team member", "per employee"],
        "usage-based": ["usage-based", "pay as you go", "pay per use", "metered", "consumption"],
        "freemium": ["freemium", "free tier", "free plan", "free version"],
        "tiered": ["tiered", "tiers", "plans", "packages"],
    }
    
    # Check for payment model keywords
    for model, keywords in payment_models.items():
        for keyword in keywords:
            if keyword in content_lower:
                return model
    
    # Check cadence patterns (already extracted, but can infer model)
    if re.search(r"per\s+(?:month|year|day|week)", content_lower):
        return "subscription"
    
    if re.search(r"(?:one.?time|lifetime|single)", content_lower):
        return "one-time"
    
    if re.search(r"per\s+(?:seat|user|team)", content_lower):
        return "per-seat"
    
    return None

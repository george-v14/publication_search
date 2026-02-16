from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Publication Search API")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    keywords: str
    source: str = "pubmed"  # pubmed or biorxiv
    max_results: int = 20
    search_mode: str = "AND"  # AND or OR
    search_fields: str = "all"  # all, title, abstract, title_abstract

class Article(BaseModel):
    id: str
    title: str
    authors: List[str]
    abstract: str
    publication_date: Optional[str]
    source: str
    url: str
    journal: Optional[str] = None
    is_open_access: Optional[bool] = None
    has_dataset: Optional[bool] = None
    classification_reason: Optional[str] = None
    data_availability: Optional[str] = None
    labels: Optional[List[str]] = None  # e.g., ["Method Development", "Review", etc.]
    method_types: Optional[List[str]] = None  # e.g., ["LC-MS", "GC-MS", "NMR"]

class ClassificationRequest(BaseModel):
    article_id: str
    abstract: str

class QueryGenerationRequest(BaseModel):
    natural_language_query: str

@app.get("/")
async def root():
    return {"message": "Publication Search API", "version": "1.0"}

@app.post("/search", response_model=List[Article])
async def search_publications(request: SearchRequest):
    """Search PubMed or bioRxiv for publications"""
    if request.source == "pubmed":
        return await search_pubmed(
            request.keywords,
            request.max_results,
            request.search_mode,
            request.search_fields
        )
    elif request.source == "biorxiv":
        return await search_biorxiv(request.keywords, request.max_results)
    else:
        raise HTTPException(status_code=400, detail="Invalid source. Use 'pubmed' or 'biorxiv'")

def build_pubmed_query(keywords: str, search_mode: str = "AND", search_fields: str = "all") -> str:
    """Build a PubMed search query from keywords

    Supports two input formats:
    1. Complex query syntax: "(SRM 1950 OR SRM1950) AND HILIC"
       - Preserves parentheses and boolean operators (AND, OR)
       - Adds field tags to individual terms
    2. Simple comma-separated: "SRM 1950, HILIC"
       - Splits by comma and combines with search_mode

    Args:
        keywords: Search terms (complex query or comma-separated)
        search_mode: "AND" or "OR" - used only for simple comma-separated format
        search_fields: "all", "title", "abstract", or "title_abstract"

    Returns:
        Formatted PubMed query string
    """
    import re

    # Map field selection to PubMed field tags
    field_tag = ""
    if search_fields == "title":
        field_tag = "[Title]"
    elif search_fields == "abstract":
        field_tag = "[Abstract]"
    elif search_fields == "title_abstract":
        field_tag = "[Title/Abstract]"
    # "all" uses no field tag (searches all fields)

    # Check if this is a complex query (contains parentheses or AND/OR operators)
    has_parentheses = '(' in keywords or ')' in keywords
    has_operators = re.search(r'\b(AND|OR)\b', keywords, re.IGNORECASE)

    if has_parentheses or has_operators:
        # Complex query mode: preserve structure and add field tags to terms
        query = keywords.strip()

        # Tokenize the query into terms, operators, and parentheses
        # Pattern matches: quoted phrases, parentheses, AND/OR operators, or individual words/numbers
        tokens = re.findall(
            r'"[^"]+"|[()]|\b(?:AND|OR)\b|[A-Za-z0-9]+',
            query,
            flags=re.IGNORECASE
        )

        # Process tokens and build the query
        result_tokens = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            token_upper = token.upper()

            # Keep operators and parentheses as-is
            if token_upper in ['AND', 'OR', '(', ')']:
                result_tokens.append(token_upper if token_upper in ['AND', 'OR'] else token)
                i += 1
            # Handle quoted phrases
            elif token.startswith('"') and token.endswith('"'):
                result_tokens.append(f"{token}{field_tag}")
                i += 1
            # Handle unquoted multi-word phrases (e.g., "SRM 1950" without quotes)
            else:
                # Collect consecutive non-operator, non-parenthesis tokens
                phrase_tokens = [token]
                j = i + 1
                # Look ahead to see if next tokens form a phrase (e.g., "SRM" "1950")
                while j < len(tokens):
                    next_token = tokens[j]
                    next_upper = next_token.upper()
                    # Stop if we hit an operator or parenthesis
                    if next_upper in ['AND', 'OR', '(', ')']:
                        break
                    # Stop if next token is quoted
                    if next_token.startswith('"'):
                        break
                    phrase_tokens.append(next_token)
                    j += 1

                # Join the phrase and add field tag
                phrase = ' '.join(phrase_tokens)
                # Wrap multi-word phrases in quotes
                if len(phrase_tokens) > 1:
                    result_tokens.append(f'"{phrase}"{field_tag}')
                else:
                    result_tokens.append(f"{phrase}{field_tag}")
                i = j

        # Join tokens with spaces
        query = ' '.join(result_tokens)
        return query
    else:
        # Simple mode: split by comma and combine with search_mode
        # First split by comma to preserve phrases
        terms = [term.strip() for term in keywords.split(',') if term.strip()]

        # If no commas, treat the whole string as a single search term
        if len(terms) == 0:
            terms = [keywords.strip()]

        if not terms or (len(terms) == 1 and not terms[0]):
            return ""

        # Wrap multi-word terms in quotes and add field tags
        tagged_terms = []
        for term in terms:
            # If term has spaces, wrap in quotes to preserve as phrase
            if ' ' in term:
                tagged_terms.append(f'"{term}"{field_tag}')
            else:
                tagged_terms.append(f"{term}{field_tag}")

        # Combine with AND or OR
        operator = f" {search_mode.upper()} "
        query = operator.join(tagged_terms)

        return query

async def search_pubmed(keywords: str, max_results: int = 20, search_mode: str = "AND", search_fields: str = "all") -> List[Article]:
    """Search PubMed using E-utilities API

    Args:
        keywords: Search terms (can be comma or space separated)
        max_results: Maximum number of results to return
        search_mode: "AND" or "OR" - how to combine multiple terms
        search_fields: "all", "title", "abstract", or "title_abstract"
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    # Build the search query
    query = build_pubmed_query(keywords, search_mode, search_fields)
    print(f"PubMed Query: {query}")  # Debug logging

    # Search for article IDs
    async with httpx.AsyncClient() as client:
        search_response = await client.get(
            f"{base_url}/esearch.fcgi",
            params={
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json"
            }
        )
        search_data = search_response.json()
        
        if "esearchresult" not in search_data or "idlist" not in search_data["esearchresult"]:
            return []
        
        pmids = search_data["esearchresult"]["idlist"]
        
        if not pmids:
            return []
        
        # Fetch article details
        fetch_response = await client.get(
            f"{base_url}/efetch.fcgi",
            params={
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml"
            }
        )
        
        # Parse XML response (simplified - in production use proper XML parser)
        articles = parse_pubmed_xml(fetch_response.text, pmids)
        return articles

def parse_pubmed_xml(xml_text: str, pmids: List[str]) -> List[Article]:
    """Parse PubMed XML response - simplified version"""
    from xml.etree import ElementTree as ET
    
    articles = []
    try:
        root = ET.fromstring(xml_text)
        
        for article_elem in root.findall(".//PubmedArticle"):
            pmid_elem = article_elem.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else "unknown"
            
            title_elem = article_elem.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else "No title"
            
            abstract_elem = article_elem.find(".//AbstractText")
            abstract = abstract_elem.text if abstract_elem is not None else "No abstract available"
            
            authors = []
            for author_elem in article_elem.findall(".//Author"):
                lastname = author_elem.find("LastName")
                firstname = author_elem.find("ForeName")
                if lastname is not None:
                    name = lastname.text
                    if firstname is not None:
                        name = f"{firstname.text} {name}"
                    authors.append(name)
            
            pub_date_elem = article_elem.find(".//PubDate/Year")
            pub_date = pub_date_elem.text if pub_date_elem is not None else None

            # Extract journal name
            journal_elem = article_elem.find(".//Journal/Title")
            if journal_elem is None:
                journal_elem = article_elem.find(".//Journal/ISOAbbreviation")
            journal = journal_elem.text if journal_elem is not None else None

            # Check if article is open access
            # PubMed marks OA articles with specific attributes
            is_open_access = False
            oa_elem = article_elem.find(".//ArticleId[@IdType='pmc']")
            if oa_elem is not None:
                is_open_access = True  # Has PMC ID, likely open access

            # Also check for explicit OA markers
            pub_type_elems = article_elem.findall(".//PublicationType")
            for pt in pub_type_elems:
                if pt.text and "open access" in pt.text.lower():
                    is_open_access = True

            articles.append(Article(
                id=pmid,
                title=title,
                authors=authors,
                abstract=abstract,
                publication_date=pub_date,
                source="pubmed",
                url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                journal=journal,
                is_open_access=is_open_access
            ))
    except Exception as e:
        print(f"Error parsing PubMed XML: {e}")
    
    return articles

async def search_biorxiv(keywords: str, max_results: int = 20) -> List[Article]:
    """Search bioRxiv using their API"""
    # bioRxiv API endpoint
    base_url = "https://api.biorxiv.org/details/biorxiv"
    
    # Note: bioRxiv API is limited, this is a simplified implementation
    # In production, you might want to use their full-text search or other methods
    articles = []
    
    # Placeholder - bioRxiv doesn't have a direct keyword search API
    # You would need to implement web scraping or use alternative methods
    return articles

@app.post("/generate-query")
async def generate_query(request: QueryGenerationRequest):
    """Use LLM to convert natural language query into optimized PubMed search syntax"""

    # Get OpenAI API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    prompt = f"""You are an expert in PubMed search query optimization and metabolomics research terminology.

Convert the following natural language search request into an optimized PubMed search query.

User's request: "{request.natural_language_query}"

Your task:
1. Extract the main keywords and concepts
2. Identify synonyms, abbreviations, and related terms that should be included
3. Construct a PubMed query using boolean operators (AND, OR) and parentheses
4. Use OR to group synonyms/related terms, and AND to combine different concepts
5. Consider common variations (e.g., "SRM 1950" vs "SRM1950", "HILIC" vs "hydrophilic interaction liquid chromatography")

Examples:
- Input: "Find databases related to SRM 1950 and HILIC"
  Output: (SRM 1950 OR SRM1950 OR "standard reference material 1950") AND (HILIC OR "hydrophilic interaction liquid chromatography" OR "hydrophilic interaction chromatography") AND (database OR repository OR data)

- Input: "metabolomics studies using mass spectrometry"
  Output: (metabolomics OR metabolome OR "metabolic profiling") AND ("mass spectrometry" OR MS OR "mass spec" OR LC-MS OR GC-MS)

Respond in JSON format with:
- "pubmed_query": the optimized PubMed search query string
- "extracted_concepts": array of main concepts identified
- "synonyms_used": object mapping each concept to its synonyms/variations included
- "explanation": brief explanation of the query strategy (1-2 sentences)
"""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are an expert in scientific literature search and PubMed query optimization, specializing in metabolomics and analytical chemistry."},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3
                },
                timeout=30.0
            )

            if response.status_code != 200:
                error_detail = response.text
                print(f"OpenAI API Error: {response.status_code} - {error_detail}")
                raise HTTPException(status_code=500, detail=f"Query generation failed: {error_detail}")

            result = response.json()
            import json
            query_result = json.loads(result["choices"][0]["message"]["content"])

            return {
                "pubmed_query": query_result.get("pubmed_query", ""),
                "extracted_concepts": query_result.get("extracted_concepts", []),
                "synonyms_used": query_result.get("synonyms_used", {}),
                "explanation": query_result.get("explanation", "")
            }
    except Exception as e:
        print(f"Query generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query generation error: {str(e)}")

@app.post("/classify")
async def classify_abstract(request: ClassificationRequest):
    """Use LLM to classify if abstract describes a new metabolomics dataset"""
    
    # Get OpenAI API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    
    prompt = f"""Analyze the following metabolomics scientific abstract and provide a comprehensive classification.

## DATASET CLASSIFICATION (Primary)
Only classify as "has_dataset": true if the abstract EXPLICITLY mentions:
1. Data availability in a public repository (e.g., MetaboLights, Metabolomics Workbench, GNPS, etc.)
2. Data deposition with accession numbers
3. Clear statement that data is publicly accessible or available upon request

DO NOT classify as having a dataset if:
- The abstract only describes methods or analytical techniques
- It mentions using existing reference materials (like SRM 1950) without publishing new data
- It compares methods without explicit data availability statements
- Data availability is not mentioned or unclear

## ARTICLE TYPE LABELS
Assign appropriate labels from this list (can be multiple):
- "Method Development" - Focuses on developing, comparing, or optimizing analytical methods
- "Review" - Review article or meta-analysis
- "Application Study" - Applies metabolomics to study biological questions
- "Reference Material" - Characterizes reference materials or standards
- "Software/Tool" - Presents new software, databases, or computational tools

## METHOD TYPES (if Method Development label applies)
If the article is about method development, extract the analytical method types mentioned:
Examples: "LC-MS", "GC-MS", "NMR", "CE-MS", "HILIC", "UPLC", "QTOF", "Orbitrap", "FT-ICR", etc.
Only include if explicitly mentioned in the abstract.

Abstract:
{request.abstract}

Respond in JSON format with:
- "has_dataset": true or false (be STRICT - only true if data availability is explicitly stated)
- "confidence": "high", "medium", or "low"
- "reason": brief explanation of your decision (1-2 sentences)
- "data_availability": if has_dataset is true, extract the data availability statement or repository information; otherwise null
- "labels": array of applicable labels from the list above (e.g., ["Method Development", "Application Study"])
- "method_types": array of method types if Method Development label applies; otherwise empty array or null
"""
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are a scientific literature analyst specializing in metabolomics research."},
                        {"role": "user", "content": prompt}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3
                },
                timeout=30.0
            )

            if response.status_code != 200:
                error_detail = response.text
                print(f"OpenAI API Error: {response.status_code} - {error_detail}")
                raise HTTPException(status_code=500, detail=f"LLM classification failed: {error_detail}")

            result = response.json()
            import json
            classification = json.loads(result["choices"][0]["message"]["content"])

            return {
                "article_id": request.article_id,
                "has_dataset": classification.get("has_dataset", False),
                "confidence": classification.get("confidence", "low"),
                "reason": classification.get("reason", "Unable to determine"),
                "data_availability": classification.get("data_availability", None),
                "labels": classification.get("labels", []),
                "method_types": classification.get("method_types", [])
            }
    except Exception as e:
        print(f"Classification error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Classification error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


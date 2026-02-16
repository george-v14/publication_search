# Search Functionality Guide

## How Search Works

The application uses PubMed's E-utilities API to search for publications. You have full control over how the search is performed.

## Search Modes

### 🤖 Deep Search (AI-Powered)

**NEW!** Deep Search uses AI to convert your natural language query into an optimized PubMed search with synonyms and related terms.

**How to use:**
1. Enable the "🤖 Deep Search (AI-Powered)" toggle
2. Describe what you're looking for in plain English
3. AI will generate an optimized query with:
   - Extracted main concepts
   - Synonyms and abbreviations
   - Related terms
   - Proper boolean operators

**Examples:**
- Input: `Find databases or repositories related to SRM 1950 and HILIC`
- AI generates: `(SRM 1950 OR SRM1950 OR "standard reference material 1950") AND (HILIC OR "hydrophilic interaction liquid chromatography") AND (database OR repository OR data)`

- Input: `metabolomics studies using mass spectrometry`
- AI generates: `(metabolomics OR metabolome OR "metabolic profiling") AND ("mass spectrometry" OR MS OR "mass spec" OR LC-MS OR GC-MS)`

**Benefits:**
- No need to know PubMed syntax
- Automatically includes synonyms and variations
- Catches abbreviations and full names
- More comprehensive results

### Manual Search

## Query Formats

The application supports two query formats for manual search:

### 1. Simple Format (Comma-Separated)
Use commas to separate search terms. The search mode (AND/OR) determines how they're combined.

**Examples:**
- `SRM1950, HILIC` with AND mode → Articles with BOTH terms
- `SRM1950, metabolomics` with OR mode → Articles with EITHER term

### 2. Complex Format (Boolean Operators)
Use parentheses and AND/OR operators for precise control over search logic.

**Examples:**
- `(SRM 1950 OR SRM1950) AND HILIC` → Articles with (either SRM variant) AND HILIC
- `(HILIC OR hydrophilic interaction) AND metabolomics` → Flexible term matching
- `(SRM1950 AND HILIC) OR (NIST AND reference material)` → Multiple search strategies

**Note:** When using complex format, the search mode dropdown is ignored.

## Search Modes (Simple Format Only)

### AND Mode (Default)
- Finds articles containing **ALL** search terms
- More specific, fewer results
- Best for finding articles about specific topics

**Example:**
- Keywords: `SRM1950, HILIC`
- Result: Articles that mention BOTH SRM1950 AND HILIC
- Use case: Finding articles about HILIC analysis of SRM1950

### OR Mode
- Finds articles containing **ANY** search term
- Broader search, more results
- Best for exploratory searches

**Example:**
- Keywords: `SRM1950, metabolomics`
- Result: Articles that mention EITHER SRM1950 OR metabolomics
- Use case: Finding all metabolomics articles plus SRM1950 articles

## Search Fields

### All Fields (Default)
- Searches in: Title, Abstract, Authors, Affiliations, Keywords, MeSH terms
- Most comprehensive search
- Recommended for general searches

### Title Only
- Searches only in article titles
- Very specific, fewest results
- Best when you know the exact topic

**Example:**
- Keywords: `metabolomics`
- Fields: Title Only
- Result: Only articles with "metabolomics" in the title

### Abstract Only
- Searches only in article abstracts
- Good for finding detailed methodology
- Useful for technical terms

### Title & Abstract
- Searches in both title and abstract
- Balanced approach
- Excludes author names and affiliations

## Keyword Tips

### Simple Format
You can enter multiple keywords separated by commas:
- `SRM1950, HILIC, metabolomics`
- Multi-word phrases are automatically quoted: `SRM 1950, HILIC` → `"SRM 1950" AND HILIC`

### Complex Format
Use parentheses and boolean operators for advanced queries:
- Parentheses group terms: `(term1 OR term2) AND term3`
- AND operator: Both terms must be present
- OR operator: Either term can be present
- Multi-word phrases are automatically quoted: `SRM 1950` → `"SRM 1950"`

**Pro Tip:** Use complex format to search for term variations:
- `(SRM 1950 OR SRM1950)` catches both spacing variants
- `(HILIC OR hydrophilic interaction)` catches abbreviation and full name

### Common Metabolomics Keywords
- **Standards**: `SRM1950`, `NIST`, `reference material`
- **Techniques**: `HILIC`, `LC-MS`, `GC-MS`, `NMR`, `mass spectrometry`
- **Methods**: `untargeted metabolomics`, `targeted metabolomics`, `lipidomics`
- **Sample Types**: `plasma`, `serum`, `urine`, `tissue`
- **Data**: `dataset`, `data repository`, `metabolomics data`

## Search Strategy Examples

### Finding Specific Method Papers
```
Keywords: SRM1950, HILIC
Mode: AND
Fields: All Fields
→ Articles about HILIC analysis of SRM1950
```

### Broad Literature Review
```
Keywords: metabolomics, lipidomics, proteomics
Mode: OR
Fields: Title & Abstract
→ All omics papers
```

### Finding Dataset Publications
```
Keywords: metabolomics, dataset, repository
Mode: AND
Fields: Abstract Only
→ Papers that published metabolomics datasets
```

### Technique Comparison
```
Keywords: HILIC, reversed-phase, comparison
Mode: AND
Fields: Title & Abstract
→ Papers comparing HILIC to reversed-phase chromatography
```

## Understanding Results

The search info bar shows:
- **Search Query**: How your terms were combined (e.g., "SRM1950 AND HILIC")
- **Fields**: Where the search was performed
- **Results**: Number of articles found

## Troubleshooting

### Too Many Results
- Switch from OR to AND mode
- Add more specific keywords
- Search in Title Only or Title & Abstract instead of All Fields

### Too Few Results
- Switch from AND to OR mode
- Use fewer keywords
- Search in All Fields instead of Title Only
- Try alternative terms (e.g., "HILIC" vs "hydrophilic interaction chromatography")

### No Results
- Check spelling
- Try broader terms
- Use OR mode
- Search in All Fields
- Reduce number of keywords

## PubMed Query Format

Behind the scenes, your search is converted to PubMed's query format:

- `SRM1950 AND HILIC` → searches all fields
- `SRM1950[Title] AND HILIC[Title]` → searches titles only
- `SRM1950[Abstract]` → searches abstracts only
- `SRM1950[Title/Abstract]` → searches both

The application handles this conversion automatically based on your selections.


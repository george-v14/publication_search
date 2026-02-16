# 🔬 Metabolomics Publication Search

A web application for searching and analyzing metabolomics publications from PubMed and bioRxiv. Uses AI to automatically identify articles that publish new metabolomics datasets.

## Features

- **Multi-source Search**: Search PubMed and bioRxiv using keywords (e.g., SRM1950, HILIC)
- **AI-Powered Classification**: Automatically analyze abstracts to identify new metabolomics datasets
- **Interactive UI**: Modern React interface for easy demonstration and workflow visualization
- **Batch Processing**: Classify multiple articles at once

## Architecture

- **Frontend**: React + Vite for fast, modern UI
- **Backend**: FastAPI (Python) for search and LLM classification APIs
- **AI**: OpenAI GPT-4 for abstract analysis

## Setup Instructions

### Prerequisites

- Python 3.8+
- Node.js 18+
- OpenAI API key (for abstract classification)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your OpenAI API key:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

5. Run the backend server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Usage

1. **Search Publications**:
   - Enter keywords (e.g., "SRM1950 metabolomics", "HILIC chromatography")
     - Separate multiple terms with commas or spaces
   - Select source (PubMed or bioRxiv)
   - Choose search mode:
     - **AND**: Find articles containing ALL search terms (more specific)
     - **OR**: Find articles containing ANY search term (broader results)
   - Choose where to search:
     - **All Fields**: Search in title, abstract, authors, affiliations, etc.
     - **Title Only**: Search only in article titles
     - **Abstract Only**: Search only in abstracts
     - **Title & Abstract**: Search in both title and abstract
   - Click "Search"

2. **Analyze Abstracts**:
   - Click "Analyze Abstract" on individual articles
   - Or click "Classify All" to analyze all results
   - The AI will determine if the article describes a new metabolomics dataset

3. **Review Results**:
   - Articles are marked with ✓ (has dataset) or ✗ (no dataset)
   - View the AI's reasoning and confidence level
   - Click through to read full articles

### Search Examples

- **Find articles about SRM1950 AND HILIC** (specific):
  - Keywords: `SRM1950, HILIC`
  - Mode: AND
  - Fields: All Fields

- **Find articles about SRM1950 OR metabolomics** (broad):
  - Keywords: `SRM1950 metabolomics`
  - Mode: OR
  - Fields: All Fields

- **Find articles with "metabolomics" in the title**:
  - Keywords: `metabolomics`
  - Mode: AND
  - Fields: Title Only

## Example Keywords

- `SRM1950` - NIST Standard Reference Material
- `HILIC` - Hydrophilic Interaction Liquid Chromatography
- `metabolomics dataset`
- `untargeted metabolomics`
- `LC-MS metabolomics`

## API Endpoints

### POST /search
Search for publications
```json
{
  "keywords": "SRM1950 metabolomics",
  "source": "pubmed",
  "max_results": 20,
  "search_mode": "AND",
  "search_fields": "all"
}
```

**Parameters:**
- `keywords` (string, required): Search terms (comma or space separated)
- `source` (string, default: "pubmed"): "pubmed" or "biorxiv"
- `max_results` (int, default: 20): Maximum number of results
- `search_mode` (string, default: "AND"): "AND" or "OR"
- `search_fields` (string, default: "all"): "all", "title", "abstract", or "title_abstract"

### POST /classify
Classify an abstract
```json
{
  "article_id": "12345",
  "abstract": "Abstract text here..."
}
```

**Returns:**
- `has_dataset` (boolean): Whether the article describes a new dataset
- `confidence` (string): "high", "medium", or "low"
- `reason` (string): Explanation of the classification

## Development

- Backend API docs: `http://localhost:8000/docs`
- Frontend hot reload enabled for rapid development
- CORS configured for local development

## License

MIT

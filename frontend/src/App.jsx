import { useState } from 'react'
import axios from 'axios'
import './App.css'

const API_BASE_URL = 'http://localhost:8000'

function App() {
  const [keywords, setKeywords] = useState('')
  const [source, setSource] = useState('pubmed')
  const [searchMode, setSearchMode] = useState('AND')
  const [searchFields, setSearchFields] = useState('all')
  const [maxResults, setMaxResults] = useState(50)
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(false)
  const [classifying, setClassifying] = useState({})
  const [error, setError] = useState(null)
  const [searchInfo, setSearchInfo] = useState(null)
  const [deepSearchMode, setDeepSearchMode] = useState(false)
  const [generatingQuery, setGeneratingQuery] = useState(false)
  const [generatedQueryInfo, setGeneratedQueryInfo] = useState(null)
  const [selectedFilter, setSelectedFilter] = useState('all')  // Filter by label
  const [classifyProgress, setClassifyProgress] = useState({ current: 0, total: 0, isClassifying: false })

  const handleDeepSearch = async (e) => {
    e.preventDefault()
    setGeneratingQuery(true)
    setError(null)
    setGeneratedQueryInfo(null)

    try {
      // First, generate the optimized query using AI
      const queryResponse = await axios.post(`${API_BASE_URL}/generate-query`, {
        natural_language_query: keywords
      })

      const generatedQuery = queryResponse.data.pubmed_query
      setGeneratedQueryInfo(queryResponse.data)

      // Then perform the search with the generated query
      setLoading(true)
      setGeneratingQuery(false)

      const searchResponse = await axios.post(`${API_BASE_URL}/search`, {
        keywords: generatedQuery,
        source,
        max_results: 50,
        search_mode: searchMode,
        search_fields: searchFields
      })
      setArticles(searchResponse.data)

      setSearchInfo({
        terms: queryResponse.data.extracted_concepts,
        mode: 'AI-Generated',
        fields: searchFields,
        count: searchResponse.data.length
      })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to generate query or search publications')
      console.error('Deep search error:', err)
    } finally {
      setLoading(false)
      setGeneratingQuery(false)
    }
  }

  const handleSearch = async (e) => {
    e.preventDefault()

    // If deep search mode is enabled, use AI query generation
    if (deepSearchMode) {
      return handleDeepSearch(e)
    }

    setLoading(true)
    setError(null)
    setSearchInfo(null)
    setGeneratedQueryInfo(null)

    try {
      const response = await axios.post(`${API_BASE_URL}/search`, {
        keywords,
        source,
        max_results: maxResults,
        search_mode: searchMode,
        search_fields: searchFields
      })
      setArticles(response.data)

      // Set search info for display
      const terms = keywords.split(/[,\s]+/).filter(t => t.trim())
      setSearchInfo({
        terms: terms,
        mode: searchMode,
        fields: searchFields,
        count: response.data.length
      })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to search publications')
      console.error('Search error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleClassify = async (article, showAlert = true) => {
    setClassifying(prev => ({ ...prev, [article.id]: true }))

    try {
      const response = await axios.post(`${API_BASE_URL}/classify`, {
        article_id: article.id,
        abstract: article.abstract
      })

      // Update article with classification
      setArticles(prev => prev.map(a =>
        a.id === article.id
          ? {
              ...a,
              has_dataset: response.data.has_dataset,
              classification_reason: response.data.reason,
              confidence: response.data.confidence,
              data_availability: response.data.data_availability,
              labels: response.data.labels || [],
              method_types: response.data.method_types || []
            }
          : a
      ))
      return { success: true }
    } catch (err) {
      console.error('Classification error:', err)
      if (showAlert) {
        alert('Failed to classify article. Make sure OpenAI API key is configured.')
      }
      return { success: false, error: err }
    } finally {
      setClassifying(prev => ({ ...prev, [article.id]: false }))
    }
  }

  const handleClassifyAll = async () => {
    let errorCount = 0
    const articlesToClassify = articles.filter(a => a.has_dataset === null || a.has_dataset === undefined)

    // Initialize progress
    setClassifyProgress({ current: 0, total: articlesToClassify.length, isClassifying: true })

    for (let i = 0; i < articlesToClassify.length; i++) {
      const article = articlesToClassify[i]
      const result = await handleClassify(article, false) // Don't show alert for each article

      // Update progress
      setClassifyProgress({ current: i + 1, total: articlesToClassify.length, isClassifying: true })

      if (!result.success) {
        errorCount++
        // Stop on first error to avoid spamming requests
        break
      }
      // Add small delay to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 500))
    }

    // Reset progress
    setClassifyProgress({ current: 0, total: 0, isClassifying: false })

    // Show single alert at the end if there were errors
    if (errorCount > 0) {
      alert('Failed to classify articles. Make sure OpenAI API key is configured in backend/.env file.')
    }
  }

  // Get all unique labels from classified articles
  const getAllLabels = () => {
    const labelSet = new Set()
    articles.forEach(article => {
      if (article.labels && article.labels.length > 0) {
        article.labels.forEach(label => labelSet.add(label))
      }
    })
    return Array.from(labelSet).sort()
  }

  // Filter articles based on selected filter
  const getFilteredArticles = () => {
    if (selectedFilter === 'all') {
      return articles
    }
    if (selectedFilter === 'has_dataset') {
      return articles.filter(a => a.has_dataset === true)
    }
    if (selectedFilter === 'no_dataset') {
      return articles.filter(a => a.has_dataset === false)
    }
    if (selectedFilter === 'unclassified') {
      return articles.filter(a => a.has_dataset === null || a.has_dataset === undefined)
    }
    // Filter by label
    return articles.filter(a => a.labels && a.labels.includes(selectedFilter))
  }

  const filteredArticles = getFilteredArticles()
  const availableLabels = getAllLabels()

  return (
    <div className="App">
      <header className="header">
        <h1>🔬 Metabolomics Publication Search</h1>
        <p>Search PubMed and bioRxiv for metabolomics datasets</p>
      </header>

      <main className="main">
        <form onSubmit={handleSearch} className="search-form">
          <div className="form-row">
            <div className="form-group full-width">
              <div className="label-with-toggle">
                <label>Search Query</label>
                <div className="deep-search-toggle">
                  <input
                    type="checkbox"
                    id="deepSearch"
                    checked={deepSearchMode}
                    onChange={(e) => setDeepSearchMode(e.target.checked)}
                  />
                  <label htmlFor="deepSearch" className="toggle-label">
                    🤖 Deep Search (AI-Powered)
                  </label>
                </div>
              </div>
              <input
                type="text"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                placeholder={deepSearchMode
                  ? "e.g., Find databases or repositories related to SRM 1950 and HILIC"
                  : "e.g., (SRM 1950 OR SRM1950) AND HILIC"}
                className="search-input"
                required
              />
              <small className="help-text">
                {deepSearchMode ? (
                  <>
                    💡 <strong>Deep Search:</strong> Describe what you're looking for in natural language.
                    AI will generate an optimized PubMed query with synonyms and related terms.
                  </>
                ) : (
                  <>
                    Simple: <code>SRM1950, HILIC</code> |
                    Complex: <code>(SRM 1950 OR SRM1950) AND HILIC</code>
                  </>
                )}
              </small>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Source</label>
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="source-select"
              >
                <option value="pubmed">PubMed</option>
                <option value="biorxiv">bioRxiv</option>
              </select>
            </div>

            <div className="form-group">
              <label>Search Mode</label>
              <select
                value={searchMode}
                onChange={(e) => setSearchMode(e.target.value)}
                className="source-select"
              >
                <option value="AND">AND (all terms)</option>
                <option value="OR">OR (any term)</option>
              </select>
            </div>

            <div className="form-group">
              <label>Search In</label>
              <select
                value={searchFields}
                onChange={(e) => setSearchFields(e.target.value)}
                className="source-select"
              >
                <option value="all">All Fields</option>
                <option value="title">Title Only</option>
                <option value="abstract">Abstract Only</option>
                <option value="title_abstract">Title & Abstract</option>
              </select>
            </div>

            <div className="form-group">
              <label>Max Results</label>
              <input
                type="number"
                value={maxResults}
                onChange={(e) => setMaxResults(parseInt(e.target.value) || 50)}
                min="1"
                max="500"
                className="max-results-input"
              />
            </div>

            <div className="form-group">
              <label>&nbsp;</label>
              <button type="submit" className="search-button" disabled={loading || generatingQuery}>
                {generatingQuery ? '🤖 Generating Query...' : loading ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>
        </form>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {generatedQueryInfo && (
          <div className="generated-query-info">
            <h3>🤖 AI-Generated Query</h3>
            <div className="query-box">
              <strong>PubMed Query:</strong>
              <code className="query-code">{generatedQueryInfo.pubmed_query}</code>
            </div>
            <div className="query-details">
              <div className="query-detail-item">
                <strong>Extracted Concepts:</strong>
                <div className="concept-tags">
                  {generatedQueryInfo.extracted_concepts.map((concept, idx) => (
                    <span key={idx} className="concept-tag">{concept}</span>
                  ))}
                </div>
              </div>
              {generatedQueryInfo.synonyms_used && Object.keys(generatedQueryInfo.synonyms_used).length > 0 && (
                <div className="query-detail-item">
                  <strong>Synonyms & Variations:</strong>
                  <div className="synonyms-list">
                    {Object.entries(generatedQueryInfo.synonyms_used).map(([concept, synonyms], idx) => (
                      <div key={idx} className="synonym-group">
                        <span className="synonym-concept">{concept}:</span>
                        <span className="synonym-terms">{Array.isArray(synonyms) ? synonyms.join(', ') : synonyms}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              <div className="query-detail-item">
                <strong>Strategy:</strong> {generatedQueryInfo.explanation}
              </div>
            </div>
          </div>
        )}

        {searchInfo && (
          <div className="search-info">
            <strong>Search Query:</strong> {searchInfo.terms.join(` ${searchInfo.mode} `)}
            <span className="separator">•</span>
            <strong>Fields:</strong> {searchInfo.fields === 'all' ? 'All Fields' :
              searchInfo.fields === 'title' ? 'Title Only' :
              searchInfo.fields === 'abstract' ? 'Abstract Only' : 'Title & Abstract'}
            <span className="separator">•</span>
            <strong>Results:</strong> {searchInfo.count}
          </div>
        )}

        {articles.length > 0 && (
          <div className="results-section">
            <div className="results-header">
              <h2>Found {articles.length} articles</h2>
              <button
                onClick={handleClassifyAll}
                className="classify-all-button"
                disabled={classifyProgress.isClassifying}
              >
                {classifyProgress.isClassifying ? 'Classifying...' : 'Classify All'}
              </button>
            </div>

            {/* Progress Bar */}
            {classifyProgress.isClassifying && (
              <div className="progress-container">
                <div className="progress-info">
                  <span>Classifying articles: {classifyProgress.current} of {classifyProgress.total}</span>
                  <span className="progress-percentage">
                    {Math.round((classifyProgress.current / classifyProgress.total) * 100)}%
                  </span>
                </div>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${(classifyProgress.current / classifyProgress.total) * 100}%` }}
                  />
                </div>
              </div>
            )}

            {/* Filter Controls */}
            <div className="filter-section">
              <label className="filter-label">🔍 Filter by:</label>
              <div className="filter-buttons">
                <button
                  className={`filter-btn ${selectedFilter === 'all' ? 'active' : ''}`}
                  onClick={() => setSelectedFilter('all')}
                >
                  All ({articles.length})
                </button>
                <button
                  className={`filter-btn ${selectedFilter === 'has_dataset' ? 'active' : ''}`}
                  onClick={() => setSelectedFilter('has_dataset')}
                >
                  Has Dataset ({articles.filter(a => a.has_dataset === true).length})
                </button>
                <button
                  className={`filter-btn ${selectedFilter === 'no_dataset' ? 'active' : ''}`}
                  onClick={() => setSelectedFilter('no_dataset')}
                >
                  No Dataset ({articles.filter(a => a.has_dataset === false).length})
                </button>
                <button
                  className={`filter-btn ${selectedFilter === 'unclassified' ? 'active' : ''}`}
                  onClick={() => setSelectedFilter('unclassified')}
                >
                  Unclassified ({articles.filter(a => a.has_dataset === null || a.has_dataset === undefined).length})
                </button>
                {availableLabels.map(label => (
                  <button
                    key={label}
                    className={`filter-btn label-filter ${selectedFilter === label ? 'active' : ''}`}
                    onClick={() => setSelectedFilter(label)}
                  >
                    {label} ({articles.filter(a => a.labels && a.labels.includes(label)).length})
                  </button>
                ))}
              </div>
              {selectedFilter !== 'all' && (
                <div className="filter-info">
                  Showing {filteredArticles.length} of {articles.length} articles
                </div>
              )}
            </div>

            <div className="articles-list">
              {filteredArticles.map((article) => (
                <div key={article.id} className="article-card">
                  <div className="article-header">
                    <h3>{article.title}</h3>
                    {article.has_dataset !== null && article.has_dataset !== undefined && (
                      <span className={`badge ${article.has_dataset ? 'badge-yes' : 'badge-no'}`}>
                        {article.has_dataset ? '✓ Has Dataset' : '✗ No Dataset'}
                      </span>
                    )}
                  </div>

                  <div className="article-meta">
                    <span className="source-badge">{article.source.toUpperCase()}</span>
                    {article.publication_date && (
                      <span className="date">{article.publication_date}</span>
                    )}
                  </div>

                  {article.journal && (
                    <div className="article-journal">
                      <strong>📰 Journal:</strong> {article.journal}
                      {article.is_open_access !== null && article.is_open_access !== undefined && (
                        <span className={article.is_open_access ? "oa-badge" : "paywall-badge"}>
                          {article.is_open_access ? "🔓 Open Access" : "🔒 Paywall"}
                        </span>
                      )}
                    </div>
                  )}

                  {article.authors.length > 0 && (
                    <p className="authors">
                      {article.authors.slice(0, 3).join(', ')}
                      {article.authors.length > 3 && ` et al.`}
                    </p>
                  )}

                  <p className="abstract">{article.abstract}</p>

                  {/* Article Labels */}
                  {article.labels && article.labels.length > 0 && (
                    <div className="article-labels">
                      <strong>🏷️ Labels:</strong>
                      <div className="label-tags">
                        {article.labels.map((label, idx) => (
                          <span key={idx} className="label-tag">{label}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Method Types (if Method Development) */}
                  {article.method_types && article.method_types.length > 0 && (
                    <div className="method-types">
                      <strong>🔬 Methods:</strong>
                      <div className="method-tags">
                        {article.method_types.map((method, idx) => (
                          <span key={idx} className="method-tag">{method}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {article.classification_reason && (
                    <div className="classification-reason">
                      <strong>Analysis ({article.confidence} confidence):</strong> {article.classification_reason}
                    </div>
                  )}

                  {article.data_availability && (
                    <div className="data-availability">
                      <strong>📊 Data Availability:</strong> {article.data_availability}
                    </div>
                  )}

                  <div className="article-actions">
                    <a 
                      href={article.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="link-button"
                    >
                      View on {article.source === 'pubmed' ? 'PubMed' : 'bioRxiv'}
                    </a>
                    
                    <button
                      onClick={() => handleClassify(article)}
                      disabled={classifying[article.id]}
                      className="classify-button"
                    >
                      {classifying[article.id] ? 'Analyzing...' : 'Analyze Abstract'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App


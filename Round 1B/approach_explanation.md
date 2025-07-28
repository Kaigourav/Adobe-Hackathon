# Persona-Driven Document Intelligence - Approach Explanation

## Methodology

Our solution employs a multi-stage pipeline to extract and rank document sections based on persona-specific relevance:

1. **Document Parsing**:
   - Uses `pdfplumber` for robust PDF text extraction
   - Implements basic section detection based on text formatting
   - Captures hierarchical structure (H1-H3) and page numbers

2. **Semantic Understanding**:
   - Leverages `all-MiniLM-L6-v2` sentence transformer (67MB) for embeddings
   - Generates composite embedding from persona + job description
   - Computes document section embeddings in batch

3. **Relevance Scoring**:
   - Calculates cosine similarity between persona/job and sections
   - Implements weighted ranking considering:
     - Semantic similarity to persona/job
     - Section hierarchy level (titles > headings > body)
     - Position in document (earlier sections often more important)

4. **Output Generation**:
   - Formats results according to specified JSON schema
   - Includes comprehensive metadata
   - Provides ranked sections with importance scores
   - Offers sub-section analysis with refined text

## Optimization Choices

- Selected `all-MiniLM-L6-v2` for its balance of performance (good semantic understanding) and small size (67MB)
- Implemented batch processing of embeddings for efficiency
- Designed to work within strict CPU-only, no-network constraints
- Ensured processing time <60s for typical document sets

## Limitations and Future Improvements

- Current section detection is basic - could be enhanced with:
  - Advanced layout analysis
  - Font characteristic examination
  - Machine learning classifiers
- Could incorporate:
  - Cross-document analysis
  - Temporal analysis for time-series documents
  - Domain-specific knowledge bases
import os
import json
import pdfplumber
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class DocumentProcessor:
    def __init__(self):
        # Load the embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
    def extract_sections(self, pdf_path):
        """Extract hierarchical sections from PDF"""
        sections = []
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    # Simple section detection - in practice would use more sophisticated logic
                    lines = text.split('\n')
                    for line in lines:
                        if line.strip():
                            # Determine section level based on formatting (simplified)
                            level = "H1" if line.isupper() else "H2" if len(line) < 50 else "H3"
                            sections.append({
                                "text": line.strip(),
                                "page": page_num,
                                "level": level
                            })
        return sections
    
    def compute_relevance(self, persona_job_text, sections):
        """Compute relevance scores for sections"""
        # Embed persona/job description
        persona_embedding = self.model.encode([persona_job_text])[0]
        
        # Embed all sections
        section_texts = [section["text"] for section in sections]
        section_embeddings = self.model.encode(section_texts)
        
        # Calculate similarities
        similarities = cosine_similarity(
            [persona_embedding],
            section_embeddings
        )[0]
        
        # Add scores to sections
        for i, section in enumerate(sections):
            section["similarity"] = float(similarities[i])
        
        return sections
    
    def rank_sections(self, sections):
        """Rank sections by importance"""
        # Sort by similarity score descending
        return sorted(sections, key=lambda x: x["similarity"], reverse=True)

def process_documents(input_dir, output_dir, persona, job):
    processor = DocumentProcessor()
    
    # Prepare output structure
    output = {
        "metadata": {
            "input_documents": [],
            "persona": persona,
            "job_to_be_done": job,
            "processing_timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "extracted_sections": [],
        "sub_section_analysis": []
    }
    
    # Process each PDF in input directory
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(input_dir, filename)
            output["metadata"]["input_documents"].append(filename)
            
            # Extract and process sections
            sections = processor.extract_sections(pdf_path)
            persona_job_text = f"{persona}. {job}"
            scored_sections = processor.compute_relevance(persona_job_text, sections)
            ranked_sections = processor.rank_sections(scored_sections)
            
            # Add to output
            for i, section in enumerate(ranked_sections[:10]):  # Top 10 sections
                output["extracted_sections"].append({
                    "document": filename,
                    "page_number": section["page"],
                    "section_title": section["text"],
                    "importance_rank": i + 1
                })
                
                # For subsections, we'd add more granular analysis
                output["sub_section_analysis"].append({
                    "document": filename,
                    "refined_text": section["text"],
                    "page_number": section["page"]
                })
    
    # Write output
    output_path = os.path.join(output_dir, "output.json")
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    # Read persona and job from environment or config
    persona = os.getenv("PERSONA", "Default Persona")
    job = os.getenv("JOB", "Default Job")
    
    # Directory paths from Docker volume mounts
    input_dir = "/app/input"
    output_dir = "/app/output"
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Process documents
    process_documents(input_dir, output_dir, persona, job)
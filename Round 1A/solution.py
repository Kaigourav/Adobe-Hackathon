import fitz  # PyMuPDF
import json
import os
import re
from collections import Counter

# --- Configuration ---
INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"

# --- Helper Functions (Unchanged) ---

def get_font_statistics(doc):
    """Analyzes the document to find font sizes, their frequencies, and names."""
    styles = Counter()
    for page in doc:
        try:
            for block in page.get_text("dict")["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            styles[(round(span["size"]), span["font"])] += 1
        except Exception:
            continue
    return styles.most_common()

def classify_headings(styles):
    """Classifies font styles into heading levels based on relative size."""
    if not styles: return {}
    
    all_sizes = sorted(list(set(s[0][0] for s in styles)), reverse=True)
    if not all_sizes: return {}

    heading_sizes = all_sizes[:3]
    size_to_level = {size: f"H{i+1}" for i, size in enumerate(heading_sizes)}

    heading_map = {}
    for style, _ in styles:
        size, font = style
        if size in size_to_level:
            heading_map[style] = size_to_level[size]
            
    return heading_map

# --- Core Logic (Revised for De-duplication and Error Handling) ---

def extract_outline_from_pdf(doc_path):
    """
    Extracts a structured outline with advanced de-duplication and error handling.
    """
    try:
        doc = fitz.open(doc_path)
    except Exception as e:
        print(f"Error opening {doc_path}: {e}")
        return None

    styles = get_font_statistics(doc)
    heading_map = classify_headings(styles)
    if not heading_map:
        return {"title": "Could not determine document structure", "outline": []}

    # 1. Extract and de-duplicate lines in a single pass
    raw_lines = {}  # Key: (page_num, y_coord), Value: line_info
    for page_num, page in enumerate(doc, 1):
        try:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        if line["spans"]:
                            span = line["spans"][0]
                            style_key = (round(span["size"]), span["font"])
                            if style_key in heading_map:
                                text = " ".join(s["text"] for s in line["spans"]).strip()
                                if not text: continue
                                
                                # Use y-coordinate as a key to handle layered text
                                y_coord = int(line["bbox"][1])
                                key = (page_num, y_coord)
                                
                                # Only keep the longest text found at a specific y-position
                                if key not in raw_lines or len(text) > len(raw_lines[key]["text"]):
                                    raw_lines[key] = {
                                        "text": text,
                                        "level": heading_map[style_key],
                                        "page": page_num,
                                        "bbox": line["bbox"],
                                        "line_height": line["bbox"][3] - line["bbox"][1]
                                    }
        except Exception as e:
            print(f"Warning: Could not process page {page_num}. Error: {e}")
            continue

    if not raw_lines:
        return {"title": "No headings found", "outline": []}
    
    potential_lines = sorted(raw_lines.values(), key=lambda x: (x["page"], x["bbox"][1]))

    # 2. Merge consecutive lines into single headings
    merged_headings = []
    if not potential_lines: return {"title": "No headings found", "outline": []}

    current_group = [potential_lines[0]]
    for i in range(1, len(potential_lines)):
        prev, curr = current_group[-1], potential_lines[i]
        gap = curr["bbox"][1] - prev["bbox"][3]
        max_gap = prev["line_height"] * 0.7

        if curr["page"] == prev["page"] and curr["level"] == prev["level"] and 0 <= gap < max_gap:
            current_group.append(curr)
        else:
            full_text = " ".join(line["text"] for line in current_group)
            merged_headings.append({"level": current_group[0]["level"], "text": re.sub(r'\s+', ' ', full_text), "page": current_group[0]["page"]})
            current_group = [curr]
    
    full_text = " ".join(line["text"] for line in current_group)
    merged_headings.append({"level": current_group[0]["level"], "text": re.sub(r'\s+', ' ', full_text), "page": current_group[0]["page"]})

    # 3. Determine title from H1s on page 1
    page1_h1s = [h["text"] for h in merged_headings if h["page"] == 1 and h["level"] == 'H1']
    title = ' '.join(page1_h1s) if page1_h1s else (merged_headings[0]["text"] if merged_headings else "Untitled Document")

    return {"title": title, "outline": merged_headings}

# --- Docker Execution Logic (Unchanged) ---

def main():
    """Processes all PDF files in the input directory."""
    print("Starting PDF processing...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input directory '{INPUT_DIR}' not found.")
        return

    for filename in os.listdir(INPUT_DIR):
        if filename.lower().endswith(".pdf"):
            input_path = os.path.join(INPUT_DIR, filename)
            output_filename = os.path.splitext(filename)[0] + ".json"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            print(f"Processing '{input_path}'...")
            result = extract_outline_from_pdf(input_path)
            if result:
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=4, ensure_ascii=False)
                print(f"Successfully generated '{output_path}'")

    print("Processing complete.")

if __name__ == "__main__":
    main()
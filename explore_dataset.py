import os
import glob
import pandas as pd
from collections import Counter
import re

def analyze_american_law_dataset(base_path, max_files=10):
    """Analyze the American Law dataset structure"""
    
    # Find citation files
    citation_files = glob.glob(os.path.join(base_path, "*_citation.parquet"))
    html_files = glob.glob(os.path.join(base_path, "*_html.parquet"))
    
    print(f"Total citation files found: {len(citation_files)}")
    print(f"Total HTML files found: {len(html_files)}")
    
    # Sample analysis
    places = []
    states = []
    chapter_types = []
    
    # Track file identifiers to find matching HTML files
    file_ids = []
    
    # Analyze a subset of citation files
    for file in citation_files[:max_files]:
        try:
            file_id = os.path.basename(file).split('_')[0]
            file_ids.append(file_id)
            
            df = pd.read_parquet(file)
            # Extract unique place and state
            places.append(df['place_name'].iloc[0])
            states.append(df['state_name'].iloc[0])
            # Collect chapter types
            chapter_types.extend(df['chapter'].unique())
        except Exception as e:
            print(f"Error processing {file}: {e}")
    
    # Count unique places and states
    unique_places = set(places)
    unique_states = set(states)
    
    print(f"\nSample of {len(unique_places)} unique places from {max_files} files:")
    for place, state in zip(places, states):
        print(f"  {place}, {state}")
    
    print(f"\nSample of {len(unique_states)} unique states from {max_files} files:")
    for state in sorted(unique_states):
        print(f"  {state}")
    
    # Analyze chapter types
    chapter_counter = Counter(chapter_types)
    print(f"\nTop 10 chapter types from {max_files} files:")
    for chapter, count in chapter_counter.most_common(10):
        print(f"  {chapter}: {count}")
    
    # Analyze HTML file structure
    print("\n--- HTML File Analysis ---")
    
    # Find a matching HTML file to examine
    if file_ids:
        html_file_path = os.path.join(base_path, f"{file_ids[0]}_html.parquet")
        if os.path.exists(html_file_path):
            html_df = pd.read_parquet(html_file_path)
            print(f"\nMatching HTML file found for {file_ids[0]}")
            print(f"Number of HTML documents: {len(html_df)}")
            print(f"HTML file columns: {html_df.columns.tolist()}")
            
            # Show document IDs and titles
            print("\nSample document IDs and titles:")
            for i, row in html_df.head(3).iterrows():
                print(f"  doc_id: {row['doc_id']}")
                print(f"  html_title: {row['html_title']}")
                print("  " + "-" * 40)
            
            # Check for linkage between citation and HTML
            citation_df = pd.read_parquet(os.path.join(base_path, f"{file_ids[0]}_citation.parquet"))
            print("\nCitation to HTML document linkage:")
            print(f"  Citation CIDs: {citation_df['cid'].nunique()} unique values")
            print(f"  HTML CIDs: {html_df['cid'].nunique()} unique values")
            
            # Check for overlap
            common_cids = set(citation_df['cid'].unique()).intersection(set(html_df['cid'].unique()))
            print(f"  Common CIDs between citation and HTML: {len(common_cids)}")
            
            # Show example citation with metadata
            if len(citation_df) > 0:
                print("\nExample citation record:")
                example = citation_df.iloc[0]
                for col in ['title', 'chapter', 'place_name', 'state_name', 'date', 'bluebook_citation']:
                    print(f"  {col}: {example[col]}")
                
                # Try to find matching HTML content for this citation
                example_cid = example['cid']
                matching_html = html_df[html_df['cid'] == example_cid]
                
                if not matching_html.empty:
                    print("\nMatching HTML content found for this citation:")
                    html_content = matching_html.iloc[0]['html']
                    
                    # Clean up HTML for display (show just a preview)
                    clean_html = re.sub(r'<[^>]+>', ' ', html_content)
                    clean_html = re.sub(r'\s+', ' ', clean_html).strip()
                    preview = clean_html[:500] + "..." if len(clean_html) > 500 else clean_html
                    
                    print(f"  HTML Preview: {preview}")
                else:
                    print("\nNo matching HTML content found for this citation CID")
    
    # Overall Dataset Structure Analysis
    print("\n--- Overall Dataset Structure Analysis ---")
    print(f"The American Law dataset contains municipal and county laws from {len(unique_states)} states")
    print("Each municipality has two file types:")
    print("  1. Citation files (_citation.parquet) - Contain metadata about legal citations")
    print("  2. HTML files (_html.parquet) - Contain the actual legal text in HTML format")
    print("\nThe files are linked by CID (Content Identifier) values")
    print("Each municipality's laws are organized into chapters and sections")
    print("The dataset uses bluebook citation format, which is a standard legal citation method")

if __name__ == "__main__":
    # Path to the dataset files
    base_path = "/home/ath/.cache/huggingface/hub/datasets--the-ride-never-ends--american_law/snapshots/9e17b4ed44170a8e688aabd22ceadc9975d92093/american_law/data"
    
    # Analyze dataset
    analyze_american_law_dataset(base_path, max_files=30) 
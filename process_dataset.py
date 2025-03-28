import os
import glob
import pandas as pd
import sqlite3
from tqdm import tqdm
import re
from bs4 import BeautifulSoup

def clean_html(html_content):
    """Clean HTML content for better display"""
    soup = BeautifulSoup(html_content, 'html.parser')
    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()
    # Get text and clean it
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)
    return text

def create_database():
    """Create SQLite database and tables"""
    conn = sqlite3.connect('american_law.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS laws (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cid TEXT UNIQUE,
        title TEXT,
        chapter TEXT,
        place_name TEXT,
        state_code TEXT,
        state_name TEXT,
        date TEXT,
        bluebook_citation TEXT,
        content TEXT,
        search_text TEXT
    )
    ''')
    
    conn.commit()
    return conn

def process_dataset(base_path):
    """Process the dataset and store in SQLite database"""
    conn = create_database()
    cursor = conn.cursor()
    
    # Find all citation files
    citation_files = glob.glob(os.path.join(base_path, "*_citation.parquet"))
    
    for citation_file in tqdm(citation_files, desc="Processing files"):
        try:
            # Get corresponding HTML file
            file_id = os.path.basename(citation_file).split('_')[0]
            html_file = os.path.join(base_path, f"{file_id}_html.parquet")
            
            if not os.path.exists(html_file):
                print(f"Warning: No matching HTML file for {citation_file}")
                continue
            
            # Read citation and HTML data
            citation_df = pd.read_parquet(citation_file)
            html_df = pd.read_parquet(html_file)
            
            # Process each citation
            for _, citation_row in citation_df.iterrows():
                cid = citation_row['cid']
                
                # Find matching HTML content
                matching_html = html_df[html_df['cid'] == cid]
                
                if not matching_html.empty:
                    # Clean HTML content
                    html_content = matching_html.iloc[0]['html']
                    clean_content = clean_html(html_content)
                    
                    # Create search text (combine relevant fields)
                    search_text = f"{citation_row['title']} {citation_row['chapter']} {clean_content}"
                    search_text = re.sub(r'\s+', ' ', search_text).lower()
                    
                    # Insert into database
                    cursor.execute('''
                    INSERT OR REPLACE INTO laws 
                    (cid, title, chapter, place_name, state_code, state_name, date, 
                     bluebook_citation, content, search_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        cid,
                        citation_row['title'],
                        citation_row['chapter'],
                        citation_row['place_name'],
                        citation_row['state_code'],
                        citation_row['state_name'],
                        citation_row['date'],
                        citation_row['bluebook_citation'],
                        clean_content,
                        search_text
                    ))
            
            # Commit after each file
            conn.commit()
            
        except Exception as e:
            print(f"Error processing {citation_file}: {e}")
            continue
    
    # Create search index
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_search_text ON laws(search_text)')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    base_path = "/home/ath/.cache/huggingface/hub/datasets--the-ride-never-ends--american_law/snapshots/9e17b4ed44170a8e688aabd22ceadc9975d92093/american_law/data"
    process_dataset(base_path) 
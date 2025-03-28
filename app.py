from flask import Flask, render_template, request, jsonify
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_db():
    conn = sqlite3.connect('american_law.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search')
def search():
    query = request.args.get('q', '').lower()
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Count total results
    cursor.execute('''
    SELECT COUNT(*) as total
    FROM laws
    WHERE search_text LIKE ?
    ''', (f'%{query}%',))
    total = cursor.fetchone()['total']
    
    # Get paginated results
    cursor.execute('''
    SELECT id, title, chapter, place_name, state_name, date, 
           bluebook_citation, content
    FROM laws
    WHERE search_text LIKE ?
    ORDER BY place_name, title
    LIMIT ? OFFSET ?
    ''', (f'%{query}%', per_page, offset))
    
    results = []
    for row in cursor.fetchall():
        results.append({
            'id': row['id'],
            'title': row['title'],
            'chapter': row['chapter'],
            'place_name': row['place_name'],
            'state_name': row['state_name'],
            'date': row['date'],
            'bluebook_citation': row['bluebook_citation'],
            'content': row['content'][:500] + '...' if len(row['content']) > 500 else row['content']
        })
    
    conn.close()
    
    return jsonify({
        'results': results,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page
    })

@app.route('/api/law/<int:law_id>')
def get_law(law_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT *
    FROM laws
    WHERE id = ?
    ''', (law_id,))
    
    law = cursor.fetchone()
    conn.close()
    
    if law:
        return jsonify({
            'id': law['id'],
            'title': law['title'],
            'chapter': law['chapter'],
            'place_name': law['place_name'],
            'state_name': law['state_name'],
            'date': law['date'],
            'bluebook_citation': law['bluebook_citation'],
            'content': law['content']
        })
    else:
        return jsonify({'error': 'Law not found'}), 404

if __name__ == '__main__':
    app.run(debug=True) 
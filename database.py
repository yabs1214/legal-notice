import sqlite3
import os

DB_PATH = 'bcm_data.db'

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Settings table (for API key and Admin Password)
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Templates table for learned letters
    c.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            type TEXT,
            level TEXT,
            original_text TEXT,
            masked_text TEXT
        )
    ''')
    
    # Insert default admin password if not exists
    c.execute("SELECT value FROM settings WHERE key = 'admin_password'")
    if not c.fetchone():
        c.execute("INSERT INTO settings (key, value) VALUES ('admin_password', 'admin1234')")
        
    conn.commit()
    conn.close()

def get_setting(key):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_setting(key, value):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def add_template(date, type_, level, original_text, masked_text):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO templates (date, type, level, original_text, masked_text)
        VALUES (?, ?, ?, ?, ?)
    ''', (date, type_, level, original_text, masked_text))
    conn.commit()
    conn.close()

def get_all_templates():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, date, type, level, original_text, masked_text FROM templates ORDER BY id DESC")
    results = c.fetchall()
    conn.close()
    
    templates = []
    for row in results:
        templates.append({
            'id': row[0],
            'date': row[1],
            'type': row[2],
            'level': row[3],
            'original_text': row[4],
            'masked_text': row[5]
        })
    return templates

def get_templates_by_criteria(type_=None, level=None):
    conn = get_connection()
    c = conn.cursor()
    
    query = "SELECT original_text, masked_text FROM templates WHERE 1=1"
    params = []
    
    if type_ and type_ != "전체":
        query += " AND type = ?"
        params.append(type_)
        
    if level and level != "전체":
        query += " AND level = ?"
        params.append(level)
        
    c.execute(query, tuple(params))
    results = c.fetchall()
    conn.close()
    
    return [{'original_text': r[0], 'masked_text': r[1]} for r in results]

def update_template(template_id, type_, level, original_text, masked_text):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE templates 
        SET type = ?, level = ?, original_text = ?, masked_text = ?
        WHERE id = ?
    ''', (type_, level, original_text, masked_text, template_id))
    conn.commit()
    conn.close()

def delete_template(template_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM templates WHERE id = ?", (template_id,))
    conn.commit()
    conn.close()

# Initialize DB on import
init_db()

from flask import Flask, jsonify, request
import socket
import threading
import sqlite3
from werkzeug.security import generate_password_hash

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS departments
                 (id INTEGER PRIMARY KEY, 
                  name TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS people
                 (id INTEGER PRIMARY KEY,
                  first_name TEXT,
                  last_name TEXT,
                  phone TEXT,
                  email TEXT,
                  department_id INTEGER,
                  type TEXT CHECK(type IN ('student', 'employee')),
                  FOREIGN KEY(department_id) REFERENCES departments(id))''')
    
    # Insert sample data if empty
    if not c.execute("SELECT 1 FROM departments LIMIT 1").fetchone():
        departments = [('Mathematics',), ('Science',), ('Arts',)]
        c.executemany("INSERT INTO departments (name) VALUES (?)", departments)
        
        people = [
            ('John', 'Doe', '555-0101', 'john.doe@school.edu', 1, 'employee'),
            ('Jane', 'Smith', '555-0102', 'jane.smith@school.edu', 2, 'employee'),
            ('Alice', 'Johnson', '555-0103', 'alice.johnson@school.edu', 3, 'student'),
            ('Bob', 'Williams', '555-0104', 'bob.williams@school.edu', 1, 'student')
        ]
        c.executemany("INSERT INTO people (first_name, last_name, phone, email, department_id, type) VALUES (?, ?, ?, ?, ?, ?)", people)
    
    conn.commit()
    conn.close()
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    
    # Create tables if they don't exist
    c.execute('''CREATE TABLE IF NOT EXISTS departments
                 (id INTEGER PRIMARY KEY, name TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS people
             (id INTEGER PRIMARY KEY,
              first_name TEXT,
              last_name TEXT,
              phone TEXT,
              email TEXT,
              department_id INTEGER,
              type TEXT CHECK(type IN ('student', 'employee')),
              FOREIGN KEY(department_id) REFERENCES departments(id))''') 
    # Insert sample data if empty
    if not c.execute("SELECT 1 FROM departments LIMIT 1").fetchone():
        departments = [('Mathematics',), ('Science',), ('Arts',)]
        c.executemany("INSERT INTO departments (name) VALUES (?)", departments)
        
        people = [
            ('John', 'Doe', '555-0101', 'john.doe@school.edu', 1, 'employee'),
            ('Jane', 'Smith', '555-0102', 'jane.smith@school.edu', 2, 'employee'),
            ('Alice', 'Johnson', '555-0103', 'alice.johnson@school.edu', 3, 'student'),
            ('Bob', 'Williams', '555-0104', 'bob.williams@school.edu', 1, 'student')
        ]
        c.executemany("INSERT INTO people (first_name, last_name, phone, email, department_id, type) VALUES (?, ?, ?, ?, ?, ?)", people)
    
    conn.commit()
    conn.close()

# TCP Server for handling direct socket connections
def tcp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 9999))
    server_socket.listen(5)
    print("TCP Server listening on port 9999")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"TCP Connection from {addr}")
        
        def handle_client(client):
            try:
                data = client.recv(1024).decode('utf-8')
                if not data:
                    return
                
                parts = data.split('|')
                if len(parts) < 2:
                    client.send(b"Invalid request format. Use: REQUEST_TYPE|PARAM1|PARAM2|...")
                    return
                
                request_type = parts[0]
                response = process_tcp_request(request_type, parts[1:])
                client.send(response.encode('utf-8'))
            except Exception as e:
                print(f"TCP Error: {e}")
                client.send(b"Error processing request")
            finally:
                client.close()
        
        threading.Thread(target=handle_client, args=(client_socket,)).start()

def process_tcp_request(request_type, params):
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    
    try:
        if request_type == "EMAIL":
            if len(params) == 2:  # First and last name
                first, last = params
                c.execute("SELECT email FROM people WHERE first_name=? AND last_name=?", (first, last))
            elif len(params) == 2:  # Last name and department
                last, dept = params
                c.execute("SELECT email FROM people WHERE last_name=? AND department_id=?", (last, dept))
            else:
                return "Invalid parameters for EMAIL request"
            
            result = c.fetchone()
            return result[0] if result else "No email found"
            
        elif request_type == "PHONE":
            # Similar to EMAIL but for phone
            pass
            
        elif request_type == "LIST":
            if len(params) == 1:  # Department number
                dept = params[0]
                c.execute("SELECT first_name, last_name, type FROM people WHERE department_id=?", (dept,))
                results = c.fetchall()
                return "\n".join([f"{f} {l} ({t})" for f, l, t in results])
            else:
                return "Invalid parameters for LIST request"
                
        else:
            return "Invalid request type"
            
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()

# REST API endpoints
@app.route('/api/people', methods=['GET'])
def get_people():
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    
    dept = request.args.get('department')
    if dept:
        c.execute("SELECT p.id, p.first_name, p.last_name, p.phone, p.email, d.name, p.type FROM people p JOIN departments d ON p.department_id=d.id WHERE d.id=?", (dept,))
    else:
        c.execute("SELECT p.id, p.first_name, p.last_name, p.phone, p.email, d.name, p.type FROM people p JOIN departments d ON p.department_id=d.id")
    
    results = c.fetchall()
    conn.close()
    
    people = [{
        'id': r[0],
        'first_name': r[1],
        'last_name': r[2],
        'phone': r[3],
        'email': r[4],
        'department': r[5],
        'type': r[6]
    } for r in results]
    
    return jsonify(people)

@app.route('/api/departments', methods=['GET'])
def get_departments():
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM departments")
    results = c.fetchall()
    conn.close()
    
    departments = [{'id': r[0], 'name': r[1]} for r in results]
    return jsonify(departments)

if __name__ == '__main__':
    init_db()
    # Start TCP server in a separate thread
    threading.Thread(target=tcp_server, daemon=True).start()
    # Start Flask web server
    app.run(port=5000, debug=True)
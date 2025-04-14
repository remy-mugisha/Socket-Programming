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
                
                try:
                    parts = data.split('|')
                    if len(parts) < 2:
                        client.send(b"ERROR|Invalid request format. Use: REQUEST_TYPE|PARAM1|PARAM2|...")
                        return
                    
                    response = process_tcp_request(parts[0], *parts[1:])
                    client.send(response.encode('utf-8'))
                except Exception as e:
                    client.send(f"ERROR|Server error: {str(e)}".encode('utf-8'))
            finally:
                client.close()
        
        threading.Thread(target=handle_client, args=(client_socket,)).start()

def process_tcp_request(request_type, *params):
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    
    try:
        if request_type == "EMAIL":
            if len(params) == 2:  # First and last name
                first, last = params
                c.execute("SELECT email FROM people WHERE first_name=? AND last_name=?", (first, last))
                result = c.fetchone()
                if result:
                    return f"EMAIL|{first}|{last}|{result[0]}"
                else:
                    return f"ERROR|No email found for {first} {last}"
            
            elif len(params) == 2:  # Last name and department
                last, dept = params
                c.execute("SELECT p.email, d.name FROM people p JOIN departments d ON p.department_id=d.id WHERE p.last_name=? AND p.department_id=?", (last, dept))
                results = c.fetchall()
                if results:
                    return "\n".join([f"EMAIL|{last}|{dept}|{r[0]}|{r[1]}" for r in results])
                else:
                    return f"ERROR|No email found for {last} in department {dept}"
            
            else:
                return "ERROR|Invalid parameters for EMAIL request"
            
        elif request_type == "PHONE":
            if len(params) == 2:  # First and last name
                first, last = params
                c.execute("SELECT phone FROM people WHERE first_name=? AND last_name=?", (first, last))
                result = c.fetchone()
                if result:
                    return f"PHONE|{first}|{last}|{result[0]}"
                else:
                    return f"ERROR|No phone found for {first} {last}"
            
            elif len(params) == 2:  # Last name and department
                last, dept = params
                c.execute("SELECT p.phone, d.name FROM people p JOIN departments d ON p.department_id=d.id WHERE p.last_name=? AND p.department_id=?", (last, dept))
                results = c.fetchall()
                if results:
                    return "\n".join([f"PHONE|{last}|{dept}|{r[0]}|{r[1]}" for r in results])
                else:
                    return f"ERROR|No phone found for {last} in department {dept}"
            
            else:
                return "ERROR|Invalid parameters for PHONE request"
            
        elif request_type == "LIST":
            if len(params) == 1:  # Department number
                dept = params[0]
                c.execute("SELECT p.first_name, p.last_name, p.type, d.name FROM people p JOIN departments d ON p.department_id=d.id WHERE p.department_id=?", (dept,))
                results = c.fetchall()
                if results:
                    response = [f"LIST|{dept}|{results[0][3]}"]  # Department name
                    response.extend([f"PERSON|{f}|{l}|{t}" for f, l, t, _ in results])
                    return "\n".join(response)
                else:
                    return f"ERROR|No people found in department {dept}"
            else:
                return "ERROR|Invalid parameters for LIST request"
                
        else:
            return "ERROR|Invalid request type"
            
    except Exception as e:
        return f"ERROR|{str(e)}"
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

@app.route('/api/people/<int:person_id>', methods=['GET'])
def get_person(person_id):
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    
    c.execute("SELECT p.id, p.first_name, p.last_name, p.phone, p.email, d.name, p.type, p.department_id FROM people p JOIN departments d ON p.department_id=d.id WHERE p.id=?", (person_id,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        return jsonify({'error': 'Person not found'}), 404
    
    return jsonify({
        'id': result[0],
        'first_name': result[1],
        'last_name': result[2],
        'phone': result[3],
        'email': result[4],
        'department': result[5],
        'type': result[6],
        'department_id': result[7]
    })

@app.route('/api/people/<int:person_id>', methods=['DELETE'])
def delete_person(person_id):
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    
    try:
        # First get the person to return in response
        c.execute("SELECT * FROM people WHERE id=?", (person_id,))
        person = c.fetchone()
        if not person:
            return jsonify({'error': 'Person not found'}), 404
            
        # Now delete the person
        c.execute("DELETE FROM people WHERE id=?", (person_id,))
        conn.commit()
        
        return jsonify({
            'message': 'Person deleted successfully',
            'id': person_id,
            'first_name': person[1],
            'last_name': person[2]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/people/<int:person_id>', methods=['PUT'])
def update_person(person_id):
    data = request.get_json()
    required_fields = ['first_name', 'last_name', 'phone', 'email', 'department_id', 'type']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'All fields are required'}), 400
    
    if data['type'] not in ['student', 'employee']:
        return jsonify({'error': 'Type must be either "student" or "employee"'}), 400
    
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    
    try:
        # Check if person exists
        c.execute("SELECT 1 FROM people WHERE id=?", (person_id,))
        if not c.fetchone():
            return jsonify({'error': 'Person not found'}), 404
            
        # Check if department exists
        c.execute("SELECT 1 FROM departments WHERE id=?", (data['department_id'],))
        if not c.fetchone():
            return jsonify({'error': 'Department does not exist'}), 400
            
        c.execute("""
            UPDATE people 
            SET first_name=?, last_name=?, phone=?, email=?, department_id=?, type=?
            WHERE id=?
        """, (data['first_name'], data['last_name'], data['phone'], data['email'], 
              data['department_id'], data['type'], person_id))
        
        conn.commit()
        return jsonify({
            'id': person_id,
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'phone': data['phone'],
            'email': data['email'],
            'department_id': data['department_id'],
            'type': data['type']
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/departments', methods=['GET'])
def get_departments():
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM departments")
    results = c.fetchall()
    conn.close()
    
    departments = [{'id': r[0], 'name': r[1]} for r in results]
    return jsonify(departments)

@app.route('/api/departments/<int:dept_id>', methods=['GET'])
def get_department(dept_id):
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    c.execute("SELECT id, name FROM departments WHERE id=?", (dept_id,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        return jsonify({'error': 'Department not found'}), 404
    
    return jsonify({'id': result[0], 'name': result[1]})

@app.route('/api/departments/<int:dept_id>', methods=['DELETE'])
def delete_department(dept_id):
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    
    try:
        # First check if department has people
        c.execute("SELECT COUNT(*) FROM people WHERE department_id=?", (dept_id,))
        count = c.fetchone()[0]
        if count > 0:
            return jsonify({
                'error': f'Cannot delete department with {count} people. Move or delete them first.'
            }), 400
            
        # Get department name for response
        c.execute("SELECT name FROM departments WHERE id=?", (dept_id,))
        dept_name = c.fetchone()
        if not dept_name:
            return jsonify({'error': 'Department not found'}), 404
            
        # Delete the department
        c.execute("DELETE FROM departments WHERE id=?", (dept_id,))
        conn.commit()
        
        return jsonify({
            'message': 'Department deleted successfully',
            'id': dept_id,
            'name': dept_name[0]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/departments/<int:dept_id>', methods=['PUT'])
def update_department(dept_id):
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Department name is required'}), 400
    
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    
    try:
        # Check if department exists
        c.execute("SELECT 1 FROM departments WHERE id=?", (dept_id,))
        if not c.fetchone():
            return jsonify({'error': 'Department not found'}), 404
            
        c.execute("UPDATE departments SET name=? WHERE id=?", (data['name'], dept_id))
        conn.commit()
        return jsonify({'id': dept_id, 'name': data['name']}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/departments', methods=['POST'])
def create_department():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Department name is required'}), 400
    
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    
    try:
        c.execute("INSERT INTO departments (name) VALUES (?)", (data['name'],))
        conn.commit()
        return jsonify({'id': c.lastrowid, 'name': data['name']}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/people', methods=['POST'])
def create_person():
    data = request.get_json()
    required_fields = ['first_name', 'last_name', 'phone', 'email', 'department_id', 'type']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'All fields are required'}), 400
    
    if data['type'] not in ['student', 'employee']:
        return jsonify({'error': 'Type must be either "student" or "employee"'}), 400
    
    conn = sqlite3.connect('school_data.db')
    c = conn.cursor()
    
    try:
        # Check if department exists
        c.execute("SELECT 1 FROM departments WHERE id=?", (data['department_id'],))
        if not c.fetchone():
            return jsonify({'error': 'Department does not exist'}), 400
            
        c.execute("""
            INSERT INTO people (first_name, last_name, phone, email, department_id, type) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data['first_name'], data['last_name'], data['phone'], data['email'], 
              data['department_id'], data['type']))
        
        conn.commit()
        return jsonify({
            'id': c.lastrowid,
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'phone': data['phone'],
            'email': data['email'],
            'department_id': data['department_id'],
            'type': data['type']
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# TCP Proxy endpoint
@app.route('/api/tcp-proxy', methods=['GET'])
def tcp_proxy():
    request_param = request.args.get('request')
    if not request_param:
        return jsonify({'error': 'No request provided'}), 400
    
    try:
        parts = request_param.split('|')
        if len(parts) < 2:
            return jsonify({'error': 'Invalid request format'}), 400
        
        response = process_tcp_request(parts[0], *parts[1:])
        return jsonify({'response': response}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    # Start TCP server in a separate thread
    threading.Thread(target=tcp_server, daemon=True).start()
    # Start Flask web server
    app.run(port=5000, debug=True)
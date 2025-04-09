document.addEventListener('DOMContentLoaded', function() {
    // Navigation
    document.querySelectorAll('[data-section]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            
            // Hide all sections
            document.querySelectorAll('[id$="-section"]').forEach(div => {
                div.style.display = 'none';
            });
            
            // Show selected section
            document.getElementById(`${section}-section`).style.display = 'block';
            
            // Update active nav link
            document.querySelectorAll('.nav-link').forEach(navLink => {
                navLink.classList.remove('active');
            });
            this.classList.add('active');
            
            // Load data if needed
            if (section === 'people') {
                loadPeople();
                loadDepartments();
            } else if (section === 'dashboard') {
                loadDashboard();
            }
        });
    });

    // Initialize dashboard
    loadDashboard();
    loadDepartments();

    // TCP Client functionality
    const requestTypeSelect = document.getElementById('request-type');
    const param1Group = document.getElementById('param1-group');
    const param2Group = document.getElementById('param2-group');
    
    requestTypeSelect.addEventListener('change', updateTCPForm);
    document.getElementById('send-request').addEventListener('click', sendTCPRequest);
    
    function updateTCPForm() {
        const requestType = requestTypeSelect.value;
        
        if (requestType === 'EMAIL' || requestType === 'PHONE') {
            param1Group.querySelector('label').textContent = 'First Name';
            param2Group.querySelector('label').textContent = 'Last Name';
            param2Group.style.display = 'block';
        } else if (requestType === 'LIST') {
            param1Group.querySelector('label').textContent = 'Department ID';
            param2Group.style.display = 'none';
        }
    }
    
    function sendTCPRequest() {
        const requestType = requestTypeSelect.value;
        const param1 = document.getElementById('param1').value;
        const param2 = document.getElementById('param2').value;
        
        let request = requestType;
        if (param1) request += `|${param1}`;
        if (param2 && requestType !== 'LIST') request += `|${param2}`;
        
        // In a real app, you'd need a WebSocket or a proxy to handle TCP from browser
        // For this demo, we'll simulate it by calling our REST API
        
        // Simulate TCP response (in real app, this would be a WebSocket or server proxy)
        let response = "Simulated TCP Response:\n";
        
        if (requestType === 'EMAIL') {
            if (param1 && param2) {
                fetch(`/api/people?first_name=${param1}&last_name=${param2}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.length > 0) {
                            response += `Email for ${param1} ${param2}: ${data[0].email}`;
                        } else {
                            response += "No matching person found";
                        }
                        document.getElementById('tcp-response').textContent = response;
                    });
            }
        } else if (requestType === 'LIST') {
            fetch(`/api/people?department=${param1}`)
                .then(res => res.json())
                .then(data => {
                    if (data.length > 0) {
                        response += `People in department ${param1}:\n`;
                        data.forEach(person => {
                            response += `${person.first_name} ${person.last_name} (${person.type})\n`;
                        });
                    } else {
                        response += "No people found in this department";
                    }
                    document.getElementById('tcp-response').textContent = response;
                });
        }
    }

    function loadDashboard() {
        fetch('/api/people')
            .then(res => res.json())
            .then(data => {
                const employees = data.filter(p => p.type === 'employee').length;
                const students = data.filter(p => p.type === 'student').length;
                
                document.getElementById('employee-count').textContent = employees;
                document.getElementById('student-count').textContent = students;
            });
            
        fetch('/api/departments')
            .then(res => res.json())
            .then(data => {
                document.getElementById('dept-count').textContent = data.length;
            });
    }
    
    function loadPeople() {
        const deptFilter = document.getElementById('department-filter').value;
        let url = '/api/people';
        if (deptFilter) url += `?department=${deptFilter}`;
        
        fetch(url)
            .then(res => res.json())
            .then(data => {
                const table = document.getElementById('people-table');
                table.innerHTML = '';
                
                data.forEach(person => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${person.first_name} ${person.last_name}</td>
                        <td><a href="mailto:${person.email}">${person.email}</a></td>
                        <td>${person.phone}</td>
                        <td>${person.department}</td>
                        <td><span class="badge ${person.type === 'employee' ? 'bg-success' : 'bg-info'}">${person.type}</span></td>
                    `;
                    table.appendChild(row);
                });
            });
    }
    
    function loadDepartments() {
        fetch('/api/departments')
            .then(res => res.json())
            .then(data => {
                const select = document.getElementById('department-filter');
                select.innerHTML = '<option value="">All Departments</option>';
                
                data.forEach(dept => {
                    const option = document.createElement('option');
                    option.value = dept.id;
                    option.textContent = dept.name;
                    select.appendChild(option);
                });
                
                select.addEventListener('change', loadPeople);
            });
    }
    
    // Initialize TCP form
    updateTCPForm();
});
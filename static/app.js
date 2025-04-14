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

    // Modal instances
    const editPersonModal = new bootstrap.Modal(document.getElementById('editPersonModal'));
    const editDepartmentModal = new bootstrap.Modal(document.getElementById('editDepartmentModal'));
    const confirmationModal = new bootstrap.Modal(document.getElementById('confirmationModal'));

    // TCP Client functionality
    const requestTypeSelect = document.getElementById('request-type');
    const param1Group = document.getElementById('param1-group');
    const param2Group = document.getElementById('param2-group');
    const deptIdGroup = document.getElementById('dept-id-group');
    
    requestTypeSelect.addEventListener('change', updateTCPForm);
    document.getElementById('send-request').addEventListener('click', sendTCPRequest);
    
    function updateTCPForm() {
        const requestType = requestTypeSelect.value;
        
        if (requestType === 'EMAIL' || requestType === 'PHONE') {
            param1Group.querySelector('label').textContent = 'First Name';
            param1Group.style.display = 'block';
            param2Group.querySelector('label').textContent = 'Last Name';
            param2Group.style.display = 'block';
            deptIdGroup.style.display = 'none';
        } else if (requestType === 'LIST') {
            param1Group.querySelector('label').textContent = 'Department ID';
            param1Group.style.display = 'block';
            param2Group.style.display = 'none';
            deptIdGroup.style.display = 'none';
        }
    }
    
    function sendTCPRequest() {
        const requestType = requestTypeSelect.value;
        const param1 = document.getElementById('param1').value;
        const param2 = document.getElementById('param2').value;
        
        let request = requestType;
        if (param1) request += `|${param1}`;
        if (param2 && requestType !== 'LIST') request += `|${param2}`;
        
        // Display the request
        document.getElementById('tcp-request').textContent = request;
        
        // In a real app, you'd connect to the TCP server here
        // For this demo, we'll simulate it by calling our REST API
        fetch(`/api/tcp-proxy?request=${encodeURIComponent(request)}`)
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('tcp-response').textContent = `ERROR|${data.error}`;
                } else {
                    document.getElementById('tcp-response').textContent = data.response;
                }
            })
            .catch(error => {
                document.getElementById('tcp-response').textContent = `ERROR|${error.message}`;
            });
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
                        <td>
                            <button class="btn btn-sm btn-outline-primary edit-person" data-id="${person.id}">
                                <i class="bi bi-pencil"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger delete-person ms-1" data-id="${person.id}">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    `;
                    table.appendChild(row);
                });
                
                // Add event listeners to the new buttons
                document.querySelectorAll('.edit-person').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const personId = this.getAttribute('data-id');
                        editPerson(personId);
                    });
                });
                
                document.querySelectorAll('.delete-person').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const personId = this.getAttribute('data-id');
                        confirmDeletePerson(personId);
                    });
                });
            });
    }
    
    function editPerson(personId) {
        fetch(`/api/people/${personId}`)
            .then(res => res.json())
            .then(person => {
                document.getElementById('edit-person-id').value = person.id;
                document.getElementById('edit-first-name').value = person.first_name;
                document.getElementById('edit-last-name').value = person.last_name;
                document.getElementById('edit-email').value = person.email;
                document.getElementById('edit-phone').value = person.phone;
                document.getElementById('edit-person-type').value = person.type;
                
                // Load departments dropdown
                fetch('/api/departments')
                    .then(res => res.json())
                    .then(departments => {
                        const select = document.getElementById('edit-person-department');
                        select.innerHTML = '';
                        
                        departments.forEach(dept => {
                            const option = document.createElement('option');
                            option.value = dept.id;
                            option.textContent = dept.name;
                            option.selected = (dept.name === person.department);
                            select.appendChild(option);
                        });
                        
                        editPersonModal.show();
                    });
            });
    }
    
    function confirmDeletePerson(personId) {
        fetch(`/api/people/${personId}`)
            .then(res => res.json())
            .then(person => {
                document.getElementById('confirmationModalTitle').textContent = 'Delete Person';
                document.getElementById('confirmationModalBody').innerHTML = `
                    Are you sure you want to delete <strong>${person.first_name} ${person.last_name}</strong>?
                    <br>This action cannot be undone.
                `;
                
                document.getElementById('confirmAction').onclick = function() {
                    deletePerson(personId);
                    confirmationModal.hide();
                };
                
                confirmationModal.show();
            });
    }
    
    function deletePerson(personId) {
        fetch(`/api/people/${personId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error) });
            }
            return response.json();
        })
        .then(data => {
            alert(`Person deleted successfully: ${data.first_name} ${data.last_name}`);
            loadPeople();
            loadDashboard();
        })
        .catch(error => {
            alert('Error: ' + error.message);
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
    
    // Load departments for the person form dropdown
    function loadDepartmentDropdown() {
        fetch('/api/departments')
            .then(res => res.json())
            .then(data => {
                const select = document.getElementById('person-department');
                select.innerHTML = '<option value="">Select Department</option>';
                
                data.forEach(dept => {
                    const option = document.createElement('option');
                    option.value = dept.id;
                    option.textContent = dept.name;
                    select.appendChild(option);
                });
            });
    }

    // Show/hide forms
    document.getElementById('show-department-form').addEventListener('click', function() {
        document.getElementById('add-department-form').style.display = 'block';
        document.getElementById('add-person-form').style.display = 'none';
        document.getElementById('department-name').focus();
    });

    document.getElementById('show-person-form').addEventListener('click', function() {
        document.getElementById('add-person-form').style.display = 'block';
        document.getElementById('add-department-form').style.display = 'none';
        loadDepartmentDropdown();
        document.getElementById('first-name').focus();
    });

    // Handle department form submission
    document.getElementById('department-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const name = document.getElementById('department-name').value;
        
        fetch('/api/departments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: name })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error) });
            }
            return response.json();
        })
        .then(data => {
            alert('Department added successfully!');
            document.getElementById('department-form').reset();
            document.getElementById('add-department-form').style.display = 'none';
            loadDepartments();
            loadDashboard();
        })
        .catch(error => {
            alert('Error: ' + error.message);
        });
    });

    // Handle person form submission
    document.getElementById('person-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const personData = {
            first_name: document.getElementById('first-name').value,
            last_name: document.getElementById('last-name').value,
            email: document.getElementById('email').value,
            phone: document.getElementById('phone').value,
            type: document.getElementById('person-type').value,
            department_id: document.getElementById('person-department').value
        };
        
        fetch('/api/people', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(personData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error) });
            }
            return response.json();
        })
        .then(data => {
            alert('Person added successfully!');
            document.getElementById('person-form').reset();
            document.getElementById('add-person-form').style.display = 'none';
            loadPeople();
            loadDashboard();
        })
        .catch(error => {
            alert('Error: ' + error.message);
        });
    });

    // Save person changes
    document.getElementById('save-person-changes').addEventListener('click', function() {
        const personId = document.getElementById('edit-person-id').value;
        const personData = {
            first_name: document.getElementById('edit-first-name').value,
            last_name: document.getElementById('edit-last-name').value,
            email: document.getElementById('edit-email').value,
            phone: document.getElementById('edit-phone').value,
            type: document.getElementById('edit-person-type').value,
            department_id: document.getElementById('edit-person-department').value
        };
        
        fetch(`/api/people/${personId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(personData)
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw new Error(err.error) });
            }
            return response.json();
        })
        .then(data => {
            alert('Person updated successfully!');
            editPersonModal.hide();
            loadPeople();
            loadDashboard();
        })
        .catch(error => {
            alert('Error: ' + error.message);
        });
    });

    // Initialize TCP form
    updateTCPForm();
});
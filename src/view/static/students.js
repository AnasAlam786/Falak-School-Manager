const studentData = document.getElementById('StudentData');

// Function to apply both filters (class and search)
function applyFilters() {
  const selectElement = document.getElementById('classView');
  const selectedClass = selectElement.options[selectElement.selectedIndex].text.toLowerCase();
  const searchQuery = document.getElementById('search-input').value.toLowerCase();

  const studentCards = studentData.getElementsByClassName('student-card');

  for (let card of studentCards) {
    const studentClass = card.getAttribute('data-class').toLowerCase();
    const studentName = card.getAttribute('data-name').toLowerCase();
    const studentRoll = card.getAttribute('data-roll').toLowerCase();
    const fatherName = card.getAttribute('data-father').toLowerCase();
    const studentPEN = card.getAttribute('data-PEN').toLowerCase();

    // Check if the class matches
    const classMatches = selectedClass === 'all classes' || studentClass === selectedClass;

    // Check if the search query matches any student data
    const searchMatches = 
      studentName.includes(searchQuery) ||
      studentRoll.includes(searchQuery) ||
      fatherName.includes(searchQuery) ||
      studentPEN.includes(searchQuery);

    console.log("Search Matches", searchMatches)
    console.log("Class Matches", classMatches)


    // Only show cards that match both class and search query
    if (classMatches && searchMatches) {
      card.style.display = '';
    } else {
      card.style.display = 'none';
    }
  }
}


// ---------------- Student Modall Code START ----------------

function viewStudentDetails(studentId, phone) {
   updatePage('/student_modal_data_api', 'studentsDetailsModalBody',   {student_id: studentId, phone: phone})
  openModal()
}
function openModal() {
    document.getElementById('studentDetailsModal').classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    document.getElementById('studentDetailsModal').classList.remove('active');
    document.body.style.overflow = 'auto';
}

// Close modal when clicking outside the content
document.getElementById('studentDetailsModal')
  .addEventListener('click', function (e) {
      if (e.target === this) {
          closeModal();
      }
  });


// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});

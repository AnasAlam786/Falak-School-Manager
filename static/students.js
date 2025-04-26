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
    const classMatches = selectedClass === 'all' || studentClass.includes(selectedClass);

    // Check if the search query matches any student data
    const searchMatches = 
      studentName.includes(searchQuery) ||
      studentRoll.includes(searchQuery) ||
      fatherName.includes(searchQuery) ||
      studentPEN.includes(searchQuery);

    // Only show cards that match both class and search query
    if (classMatches && searchMatches) {
      card.style.display = '';
    } else {
      card.style.display = 'none';
    }
  }
}

  function viewStudentDetails(studentId, phone) {
    document.getElementById('modalBody').innerHTML = 'Loading...';
    
    const backdrop = document.querySelector('.modal-backdrop');
    if (backdrop) {
        backdrop.remove();
    }
    var modal = new bootstrap.Modal(document.getElementById('studentDetailsModal'));    
    
    modal.show()
    updatePage('/studentModal', 'modalBody',   {studentId: studentId, phone: phone})
  }






function openFeesModal(){

  const grandTotal = document.getElementById('grandTotal');
  const contentSections = document.querySelectorAll('[id^="contentSection"]');
  const checkedMonths = document.querySelectorAll('[id^="checkedMonths"]');
  const netAmounts = document.querySelectorAll('[id^="netAmount"]');
  const AllFees = document.querySelectorAll('[id^="m-fees"]');
  

  // Handle netAmount and checkbox interactions
  netAmounts.forEach((netAmount, index) => {
    let checkboxes = contentSections[index].querySelectorAll('.btn-check');

    checkboxes.forEach(checkbox => {
      checkbox.addEventListener('click', function() {
        let checkedMonth = checkedMonths[index].firstChild;
        let newTotal = 0;
        fees=parseInt(AllFees[index].textContent)

        if (checkbox.checked) {
          checkedMonth.textContent = parseInt(checkedMonth.textContent) + 1;
          newTotal = newTotal + fees
        } else {
          checkedMonth.textContent = parseInt(checkedMonth.textContent) - 1;
          newTotal = newTotal - fees
          
        }

        netAmount.firstChild.textContent ="₹" + (parseInt(netAmount.textContent.replace(/\D/g, '')) + newTotal)

        grandTotal.textContent = "₹"+ (parseInt(grandTotal.textContent.replace(/\D/g, '')) + newTotal)
        
      });
    });
  })
}

  function getFees(studentId) {
    document.getElementById('feesModalBody').innerHTML = 'Loading...';

    var modal = new bootstrap.Modal(document.getElementById('feesModal'));    
    
    modal.show()
    updatePage('/getfees', 'feesModalBody', { studentId: studentId, task: "get" })
    .then(() => {
        openFeesModal();
    });
  }
  
  function Pay() {
    const verifycheck = document.getElementById('verifyCheckbox');
  
    if(!verifycheck.checked){
      showAlert(message="First, check the checkbox to confirm payment, then proceed to pay the fees.", type='danger', timeout=4000, element='verifyBody')
      return}
    
  
    const contentSections = document.querySelectorAll('[id^="contentSection"]');
    contentSections.forEach((contentSection, index) => {
  
      var checked = contentSection.querySelectorAll('.btn-check:checked');
      var checkedValues = Array.from(checked).map(function(checkbox) {
          return checkbox.getAttribute("data-name");
      });
  
      fetch('/getfees', { // Replace with your server URL
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            studentId: contentSection.getAttribute('data-id'), // Replace with actual ID
            months: checkedValues, // Replace with desired months
            task: 'update'
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.STATUS === "SUCCESS") {
          // If the status is SUCCESS, close the modal
          localStorage.setItem('reloadFlag', 'true');
          location.reload();
          }
        else {
            console.log("Failed")
          // If the status is FAILED, you can show an error message or leave the modal open
          alert("There is a problem, try again")}
      })
  
    })
  }

  function verifyModal() {

    if (grandTotal.textContent.trim() === '₹0'){
      showAlert(message="You need to select a month in order to pay the fees.", type='danger', timeout=4000,element='feesModalBody'); return
    } else {
      // Hide Modal 1 and Show Modal 2
      bootstrap.Modal.getInstance(document.getElementById('feesModal')).hide();
      new bootstrap.Modal(document.getElementById('verify')).show();
    }
  }
  
  
  function showAlert(message, type, timeout, element) {
    const alertContainer = document.getElementById(element);
  
    // Create the alert div
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show mb-1 mt-1`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
  
    // Append the alert to the container
    alertContainer.prepend(alertDiv);
  
    // Automatically remove the alert after the specified timeout
    setTimeout(() => {
      alertDiv.classList.remove('show'); // Start the fade-out effect
      alertDiv.classList.add('hide');
      setTimeout(() => alertDiv.remove(), 500); // Fully remove the element after fading out
    }, timeout);
  }

  if (localStorage.getItem('reloadFlag')) {
    showAlert('Fees Paid Successfully', 'success', 4000, element='student-container');
    localStorage.removeItem('reloadFlag'); // Clear the flag after showing the alert
  }

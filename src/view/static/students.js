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

function viewStudentDetails(studentId, phone) {
  document.getElementById('modalBody').innerHTML = 'Loading...';
  
  const backdrop = document.querySelector('.modal-backdrop');
  if (backdrop) {
      backdrop.remove();
  }
  var modal = new bootstrap.Modal(document.getElementById('studentDetailsModal'));    
  
  modal.show()
  updatePage('/student_modal_data_api', 'modalBody',   {student_id: studentId, phone: phone})
}






function handleMonthlyFeeLogic() {

  // Grand total element displaying total of all students' fees
  const grandTotalElement = document.getElementById('grandTotal');

  // Each student's section containing checkboxes for monthly fee selection
  const studentSections = document.querySelectorAll('[id^="contentSection"]');

  // Elements showing number of months selected for each student
  const selectedMonthsElements = document.querySelectorAll('[id^="checkedMonths"]');

  // Elements showing total amount per student (based on selected months)
  const studentTotalElements = document.querySelectorAll('[id^="netAmount"]');

  // Elements showing monthly fee for each student
  const monthlyFeeElements = document.querySelectorAll('[id^="m-fees"]');

  // Loop through each student section
  studentSections.forEach((studentSection, studentIndex) => {

    // Get all month checkboxes for this student
    const monthCheckboxes = studentSection.querySelectorAll('.btn-check');

    // Add event listeners to each checkbox
    monthCheckboxes.forEach(checkbox => {
      checkbox.addEventListener('click', function () {

        // Get the element showing how many months are selected
        const selectedMonths = selectedMonthsElements[studentIndex].firstChild;

        // Initialize how much to add/subtract
        let feeDelta = 0;

        // Get this student's monthly fee
        const monthlyFee = parseInt(monthlyFeeElements[studentIndex].textContent);

        // If checkbox is checked, increase months and total
        if (checkbox.checked) {
          selectedMonths.textContent = parseInt(selectedMonths.textContent) + 1;
          feeDelta = feeDelta + monthlyFee;
        } else {
          // Otherwise, reduce both
          selectedMonths.textContent = parseInt(selectedMonths.textContent) - 1;
          feeDelta = feeDelta - monthlyFee;
        }

        // Update student's total fee in student section
        const currentStudentTotal = parseInt(studentTotalElements[studentIndex].textContent.replace(/\D/g, ''));
        studentTotalElements[studentIndex].firstChild.textContent = "₹" + (currentStudentTotal + feeDelta);

        // Update overall grand total
        const currentGrandTotal = parseInt(grandTotalElement.textContent.replace(/\D/g, ''));
        grandTotalElement.textContent = "₹" + (currentGrandTotal + feeDelta);

      });
    });
  });
}

function openFeesModal(studentId, familyId) {
  document.getElementById('feesModalBody').innerHTML = 'Loading...';
  var verifyBackButton = document.getElementById('verifyBackButton');
  var verifyCloseButton = document.getElementById('verifyCloseButton');

  document.getElementById('verifyCheckbox').checked = false;

  messageButton.classList.add('d-none');
  finalPay.classList.remove('d-none');

  messageButton.disabled = true;
  finalPay.disabled = false;

  verifyBackButton.classList.remove("d-none");
  verifyCloseButton.classList.add("d-none");

  document.getElementById('paymentSuccessMessage').classList.add("d-none");

  var modal = new bootstrap.Modal(document.getElementById('feesModal'));    
  
  modal.show()
  updatePage('/api/get_fee', 'feesModalBody', { student_id: studentId, family_id: familyId })
    .then(() => {
      handleMonthlyFeeLogic();
  });
}

  
  
  async function Pay() {
    const verifycheck = document.getElementById('verifyCheckbox');
  
    if(!verifycheck.checked){
      showAlert(400, "First, check the checkbox to confirm payment, then proceed to pay the fees.")
      return
    }

    payload = [];

    const studentSections = document.querySelectorAll('[id^="contentSection"]');
    studentSections.forEach((section, index) => {

      var studentId = section.getAttribute('data-id');
      var checkedButtons = section.querySelectorAll('.btn-check:checked');

      payload.push({student_id: studentId, structure_ids: []});   //populate structureIds below

      checkedButtons.forEach(function(checkbox) {
        var structureId = checkbox.getAttribute("data-structure-id");
        payload[index].structure_ids.push(structureId);
      });
    });


    var button = document.getElementById('finalPay');
    button.disabled = true;

    const spinner = document.createElement('span');
    spinner.className = 'spinner-border spinner-border-sm';
    spinner.setAttribute('role', 'status');
    spinner.setAttribute('aria-hidden', 'true');
    button.appendChild(spinner);

    try {
      const response = await fetch("/api/pay_fee", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ payload: payload })
        });

      const data = await response.json();

      if (response.ok) {
        var messageButton = document.getElementById('messageButton');              // Button to send WhatsApp message
        var finalPay = document.getElementById('finalPay');                        // Button to finalize payment
        var verifyBackButton = document.getElementById('verifyBackButton');        // Button to go back from verification modal
        var verifyCloseButton = document.getElementById('verifyCloseButton');      // Button to close verification modal


        messageButton.classList.remove('d-none');
        finalPay.classList.add('d-none');

        messageButton.disabled = false;
        finalPay.disabled = true;

        verifyBackButton.classList.add("d-none");
        verifyCloseButton.classList.remove("d-none");

        document.getElementById('paymentSuccessMessage').classList.remove("d-none");
        messageButton.setAttribute("onclick", `sendWhatsAppMessage('${data.phone}', \`${data.whatsapp_message}\`)`);
      }
      showAlert(response.status, data.message);

    } catch (error) {
        showAlert(400, error);
        console.error("Error:", error);
    } finally {
        spinner.remove();
        button.disabled = false;

    }

  }

function verifyModal() {

  const grandTotalElement = document.getElementById('grandTotal');

  if (grandTotalElement.textContent.trim() === '₹0'){
    showAlert(400, "You need to select a month in order to pay the fees."); return
  } else {
    // Hide Modal 1 and Show Modal 2
    bootstrap.Modal.getInstance(document.getElementById('feesModal')).hide();
    new bootstrap.Modal(document.getElementById('verify')).show();
  }
}

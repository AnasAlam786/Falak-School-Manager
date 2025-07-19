async function printAdmissionForm(studentID) {
    const response = await fetch(`/create_admission_form_api?student_id=${encodeURIComponent(studentID)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    const data = await response.json();

    if (response.ok) {
      const htmlContent = data.html;
      const printWindow = window.open('', '_blank');
      // @ts-expect-error: document.write is deprecated but safe here for printing
      printWindow.document.write(htmlContent);
      printWindow.document.close();
      printWindow.onload = () => printWindow.print();
    } else {
      showAlert(response.status, data.message);
    }
  }
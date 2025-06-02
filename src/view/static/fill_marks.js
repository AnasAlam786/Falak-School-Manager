document.addEventListener("DOMContentLoaded", function () {
  const classDropdown = document.getElementById("Class");
  const subjectDropdown = document.getElementById("Subject");

  

  // Define mappings for mutual exclusions
  const restrictedClasses = ["Nursery/KG/PP3", "LKG/KG1/PP2", "UKG/KG2/PP1"];
  const restrictedSubjects = ["Science", "Computer", "SST/EVS", "Craft"];

  classDropdown.addEventListener("change", function () {
    const selectedClass = classDropdown.value;

    // Enable all subject options first
    Array.from(subjectDropdown.options).forEach(option => {
      option.disabled = false;
    });

    // Disable restricted subjects if restricted class is selected
    if (restrictedClasses.includes(selectedClass)) {
      restrictedSubjects.forEach(subject => {
        const option = Array.from(subjectDropdown.options).find(opt => opt.value === subject);
        if (option) option.disabled = true;
      });
    }
  });

  subjectDropdown.addEventListener("change", function () {
    const selectedSubject = subjectDropdown.value;

    // Enable all class options first
    Array.from(classDropdown.options).forEach(option => {
      option.disabled = false;
    });

    // Disable restricted classes if restricted subject is selected
    if (restrictedSubjects.includes(selectedSubject)) {
      restrictedClasses.forEach(cls => {
        const option = Array.from(classDropdown.options).find(opt => opt.value === cls);
        if (option) option.disabled = true;
      });
    }
  });
});

async function submit(input, id, exam, subject) {
  const value = input.value;
  

  const isValid =
      ((exam === "FA1" || exam === "FA2") && value >= 0 && value <= 20) ||
      ((exam === "SA1" || exam === "SA2") && value >= 0 && value <= 80) ||
      ((subject === "Drawing" || subject === "Craft") && ["A", "B", "C", "D", "E"].includes(value)) ||
      (exam === "Attendance" && value >= 0 && value <= 250);

  if (!isValid) {
      input.classList.add("is-invalid");
      return;
  }

  const button = input.nextElementSibling;
  button.disabled = true;

  const spinner = document.createElement('span');
  spinner.className = 'spinner-border spinner-border-sm';
  spinner.setAttribute('role', 'status');
  spinner.setAttribute('aria-hidden', 'true');
  button.appendChild(spinner);

  try {
    
      const response = await fetch("/update_marks_api", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id, exam, value })
      });

      const data = await response.json();

      if (response.ok) {
          input.classList.remove("is-invalid");
          input.classList.add("is-valid");

          // Focus on next input in the same table
          const nextInput = input.closest("tr")?.nextElementSibling?.querySelector("input");
          if (nextInput) {
              nextInput.focus();
              nextInput.scrollIntoView({ behavior: "smooth", block: "center" });
          }
      } else {
          input.classList.add("is-invalid");
          showAlert(response.status, data.message);
      }
  } catch (error) {
      showAlert(400, "There is an unexpected error!");
      console.error("Error:", error);
      input.classList.add("is-invalid");
  } finally {
      spinner.remove();
      button.disabled = false;
  }
}

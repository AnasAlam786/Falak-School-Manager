
async function submit(button) {
  const input = button.previousElementSibling;
  let score = input.value;

  let marks_id = button.dataset.id;
  const evaluation_type = button.dataset.evaluation_type;
  const student_id = button.dataset.student_id;
  const subject_id = button.dataset.subject_id;
  const exam_id = button.dataset.exam_id;
  

  if (evaluation_type === 'grading') {
    if (!["A", "B", "C", "D", "E"].includes(score)) {
      input.classList.add("is-invalid");
      return;
    } else {
      input.classList.remove("is-invalid");
    }
  }

  if(score==''){score=null}
  if(marks_id==''){marks_id=null}

  if (evaluation_type === 'numeric' && score!=null) {
    const num = parseFloat(score);
    const min = parseFloat(input.min);
    const max = parseFloat(input.max);
    if (isNaN(num) || num < min || num > max) {
      input.classList.add("is-invalid");
      return;
    }
    else {
      input.classList.remove("is-invalid");
    }
  }

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
          body: JSON.stringify({ marks_id, score, student_id, subject_id, exam_id })
      });

      const data = await response.json();

      if (response.ok) {
          input.classList.remove("is-invalid");
          input.classList.add("is-valid");

          console.log(data.new_mark_id)

          if(data.new_mark_id){
            button.dataset.id = data.new_mark_id
          }

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

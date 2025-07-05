document.querySelectorAll(".change-btn").forEach(button => {
    button.addEventListener("click", function () {
      const parent = button.closest("td");
      const staticForm = parent.querySelector(".static-feedback-form");
      const editForm = parent.querySelector(".edit-feedback-form");

      staticForm.classList.add("d-none");
      editForm.classList.remove("d-none");
    });
  });


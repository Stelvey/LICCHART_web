// JS for disabling form submissions if there are invalid fields
(function () {
  'use strict'

  // Fetch all the forms we want to apply custom Bootstrap validation styles to
  var forms = document.querySelectorAll('.needs-validation')

  // Loop over them and prevent submission
  Array.prototype.slice.call(forms)
    .forEach(function (form) {
      form.addEventListener('submit', function (event) {
        if (!form.checkValidity()) {
          event.preventDefault()
          event.stopPropagation()
        }

        form.classList.add('was-validated')
      }, false)
    })
})()


// Mediocre JS for disabling username or CSV depending on what was chosen
function lockinput(filled, locked) {
  filled.addEventListener('input', function() {
    if (filled.value.length) {
      locked.removeAttribute('required');
      locked.setAttribute('disabled', '');
    }
    else {
      locked.removeAttribute('disabled');
      locked.setAttribute('required', '');
    }
  })
}

user = document.getElementById('user')
file = document.getElementById('file')

lockinput(user, file);
lockinput(file, user);
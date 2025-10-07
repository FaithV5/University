// static/js/main.js
// Small helper: validate student id pattern (client-side)
document.addEventListener('submit', function(e){
  const form = e.target;
  if(form.matches('form')){
    const sid = form.querySelector('input[name="student_id"]');
    if(sid){
      const re = /^\d{2}-\d{5}$/; // Allow any two digits
      if(!re.test(sid.value)){
        e.preventDefault();
        alert('Student ID should be in the format NN-***** (e.g., 25-12345, 99-54321).');
      }
    }
  }
});
document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('.btn-danger');

    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            if (!confirm('¿Estás seguro de que deseas eliminar este elemento?')) {
                event.preventDefault();
            }
        });
    });
});

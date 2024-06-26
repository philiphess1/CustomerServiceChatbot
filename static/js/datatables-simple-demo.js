window.addEventListener('DOMContentLoaded', event => {
    // Simple-DataTables
    // https://github.com/fiduswriter/Simple-DataTables/wiki

    const datatablesSimple = document.getElementById('datatablesSimple');
    if (datatablesSimple) {
        let rows = datatablesSimple.querySelectorAll('tbody tr');
        if (rows.length > 10) {
            for (let i = 10; i < rows.length; i++) {
                rows[i].parentNode.removeChild(rows[i]);
            }
        }

        new simpleDatatables.DataTable(datatablesSimple, {
            paging: false // Ensure paging is disabled
        });
    }
});

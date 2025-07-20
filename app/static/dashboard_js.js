<script>
const ctx = document.getElementById('spendingChart').getContext('2d');
const spendingChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: {{ labels | safe }},  // Example: ['Rent', 'Food', 'Utilities']
        datasets: [{
            label: 'Expenses ($)',
            data: {{ values | safe }}, // Example: [1200, 300, 150]
            backgroundColor: ['#ff6384', '#36a2eb', '#cc65fe'],
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});
</script>
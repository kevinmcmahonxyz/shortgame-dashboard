/**
 * Dashboard App - Fetch stats and render gauges + table
 */

const DISTANCES = [
    'Gimmie', '3ft', '4ft', '5ft',
    '6ft', '7ft', '8ft', '10ft',
    '15ft', '20ft', '25ft', '30ft',
    '40ft', '50ft', '50ft+',
];

async function loadStats() {
    try {
        const resp = await fetch('/api/stats');
        const stats = await resp.json();
        renderDashboard(stats);
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

function renderDashboard(stats) {
    // Total rounds
    document.getElementById('total-rounds').textContent = stats.total_rounds;

    // Gauges
    createGauge({
        container: 'gauge-ppr',
        title: 'Putts Per Round',
        value: stats.putts_per_round,
        displayValue: stats.putts_per_round.toFixed(1),
        goal: stats.goals.putts_per_round,
        goalLabel: `< ${stats.goals.putts_per_round}`,
        min: 26,
        max: 40,
        invertColor: true,
    });

    createGauge({
        container: 'gauge-updown',
        title: 'Up & Down %',
        value: stats.up_and_down_pct,
        displayValue: stats.up_and_down_pct.toFixed(1),
        goal: stats.goals.up_and_down_pct,
        goalLabel: `${stats.goals.up_and_down_pct}%`,
        min: 0,
        max: 100,
        unit: '%',
    });

    createGauge({
        container: 'gauge-approach',
        title: 'Non-GIR Approach',
        value: stats.non_gir_approach_ft,
        displayValue: stats.non_gir_approach_display,
        goal: stats.goals.non_gir_approach_ft,
        goalLabel: `< ${stats.goals.non_gir_approach_ft}ft`,
        min: 0,
        max: 30,
        invertColor: true,
    });

    createGauge({
        container: 'gauge-sg',
        title: 'SG: Putting',
        value: stats.sg_putting,
        displayValue: (stats.sg_putting >= 0 ? '+' : '') + stats.sg_putting.toFixed(2),
        goal: stats.goals.sg_putting,
        goalLabel: '> 0',
        min: -5,
        max: 5,
    });

    createGauge({
        container: 'gauge-3ft',
        title: '3ft Make %',
        value: stats.make_pct_3ft,
        displayValue: stats.make_pct_3ft.toFixed(1),
        goal: stats.goals.make_pct_3ft,
        goalLabel: `${stats.goals.make_pct_3ft}%`,
        min: 0,
        max: 100,
        unit: '%',
    });

    createGauge({
        container: 'gauge-4-5ft',
        title: '4-5ft Make %',
        value: stats.make_pct_4_5ft,
        displayValue: stats.make_pct_4_5ft.toFixed(1),
        goal: stats.goals.make_pct_4_5ft,
        goalLabel: `${stats.goals.make_pct_4_5ft}%`,
        min: 0,
        max: 100,
        unit: '%',
    });

    createGauge({
        container: 'gauge-6-7ft',
        title: '6-7ft Make %',
        value: stats.make_pct_6_7ft,
        displayValue: stats.make_pct_6_7ft.toFixed(1),
        goal: stats.goals.make_pct_6_7ft,
        goalLabel: `${stats.goals.make_pct_6_7ft}%`,
        min: 0,
        max: 100,
        unit: '%',
    });

    // Putting table
    const tbody = document.getElementById('putting-tbody');
    tbody.innerHTML = '';
    for (const dist of DISTANCES) {
        const first = stats.first_putt_stats[dist] || { pct: 0, attempts: 0 };
        const second = stats.second_putt_stats[dist] || { pct: 0, attempts: 0 };
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${dist}</td>
            <td>${first.attempts > 0 ? first.pct + '%' : '--'}</td>
            <td>${second.attempts > 0 ? second.pct + '%' : '--'}</td>
        `;
        tbody.appendChild(row);
    }

    // Other stats
    document.getElementById('gir-approach').textContent = stats.gir_approach_display;
}

// Load on page ready
document.addEventListener('DOMContentLoaded', loadStats);

/**
 * SVG Circular Gauge Component
 *
 * Creates a 270-degree arc gauge with color coding based on goal proximity.
 */

function createGauge(options) {
    const {
        container,
        title,
        value,
        displayValue,
        goal,
        goalLabel,
        min = 0,
        max = 100,
        invertColor = false,  // true = lower is better (e.g., putts per round)
        unit = '',
    } = options;

    const size = 120;
    const strokeWidth = 10;
    const radius = (size - strokeWidth) / 2;
    const cx = size / 2;
    const cy = size / 2;

    // 270-degree arc (from 135° to 405° i.e. 135° to 45°)
    const arcDegrees = 270;
    const startAngle = 135;

    // Calculate progress (clamp 0-1)
    let progress = (value - min) / (max - min);
    progress = Math.max(0, Math.min(1, progress));

    // Goal progress for coloring (0 = far from goal, 1+ = meeting goal)
    let goalProgress;
    if (invertColor) {
        // Lower is better: green when below goal
        if (goal > 0) {
            goalProgress = value <= goal ? 1 : goal / value;
        } else {
            goalProgress = value <= 0 ? 1 : 0;
        }
    } else if (goal === 0) {
        // Special case: goal is zero (e.g., SG:Putting > 0)
        // Map based on value position in the range
        if (value >= 0) {
            goalProgress = 1; // meeting goal
        } else {
            goalProgress = Math.max(0, 1 + value / (max - min) * 2);
        }
    } else {
        // Higher is better: green when above goal
        goalProgress = value / goal;
    }

    // Color based on goal proximity
    let color;
    if (goalProgress >= 1) {
        color = '#4ecca3'; // green - meeting goal
    } else if (goalProgress >= 0.8) {
        color = '#f0a500'; // amber - close
    } else {
        color = '#e74c3c'; // red - far
    }

    // SVG arc path calculations
    const circumference = 2 * Math.PI * radius;
    const arcLength = (arcDegrees / 360) * circumference;
    const dashOffset = arcLength * (1 - progress);

    // Create rotation so arc starts at bottom-left
    const rotation = startAngle;

    // Font size scales down for longer display values
    const textLen = (displayValue + unit).length;
    const fontSize = textLen > 6 ? 18 : textLen > 4 ? 22 : 26;

    const svg = `
        <svg viewBox="0 0 ${size} ${size}" width="${size}" height="${size}">
            <!-- Background arc -->
            <circle
                cx="${cx}" cy="${cy}" r="${radius}"
                fill="none"
                stroke="#2a2a4a"
                stroke-width="${strokeWidth}"
                stroke-dasharray="${arcLength} ${circumference}"
                stroke-linecap="round"
                transform="rotate(${rotation} ${cx} ${cy})"
            />
            <!-- Value arc -->
            <circle
                cx="${cx}" cy="${cy}" r="${radius}"
                fill="none"
                stroke="${color}"
                stroke-width="${strokeWidth}"
                stroke-dasharray="${arcLength} ${circumference}"
                stroke-dashoffset="${dashOffset}"
                stroke-linecap="round"
                transform="rotate(${rotation} ${cx} ${cy})"
                class="gauge-arc"
            />
            <!-- Center value -->
            <text
                x="${cx}" y="${cy + 2}"
                text-anchor="middle"
                dominant-baseline="central"
                fill="${color}"
                font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
                font-size="${fontSize}"
                font-weight="700"
            >${displayValue}${unit}</text>
        </svg>
    `;

    const el = document.getElementById(container);
    el.innerHTML = `
        <div class="gauge-title">${title}</div>
        ${svg}
        <div class="gauge-goal">Goal: ${goalLabel}</div>
    `;
}

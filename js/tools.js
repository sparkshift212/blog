// tools.js - Calculators and Interactive Tools for Yarnoodle Amigurumi

document.addEventListener('DOMContentLoaded', () => {
    // 1. Yarn Calculator
    const yarnForm = document.getElementById('yarn-calc');
    if (yarnForm) {
        yarnForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const gaugeStitches = parseFloat(document.getElementById('yarn-gauge-sts').value);
            const pieceStitches = parseFloat(document.getElementById('yarn-piece-sts').value);
            const yardagePerSkein = parseFloat(document.getElementById('yarn-yardage').value);
            
            if (gaugeStitches && pieceStitches && yardagePerSkein) {
                // Simplified formula for demo: (Stitches in piece / Stitches per yard)
                // Assume 1 yard = approx 4 stitches based on gauge
                const estimatedYards = (pieceStitches / (gaugeStitches / 4)).toFixed(2);
                const skeins = Math.ceil(estimatedYards / yardagePerSkein);
                
                document.getElementById('yarn-result').innerHTML = `
                    <strong>Estimated Yardage:</strong> ${estimatedYards} yards<br>
                    <strong>Skeins Needed:</strong> ${skeins}
                `;
            }
        });
    }

    // 2. Stitch Size Converter
    const stitchForm = document.getElementById('stitch-converter');
    if (stitchForm) {
        stitchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const mmSize = parseFloat(document.getElementById('hook-mm').value);
            let usSize = "Unknown";
            let ukSize = "Unknown";
            
            // Basic lookup table
            if (mmSize === 2.25) { usSize = "B/1"; ukSize = "13"; }
            else if (mmSize === 2.75) { usSize = "C/2"; ukSize = "12"; }
            else if (mmSize === 3.25) { usSize = "D/3"; ukSize = "10"; }
            else if (mmSize === 3.5) { usSize = "E/4"; ukSize = "9"; }
            else if (mmSize === 4.0) { usSize = "G/6"; ukSize = "8"; }
            else if (mmSize === 4.5) { usSize = "7"; ukSize = "7"; }
            else if (mmSize === 5.0) { usSize = "H/8"; ukSize = "6"; }
            else if (mmSize === 5.5) { usSize = "I/9"; ukSize = "5"; }
            else if (mmSize === 6.0) { usSize = "J/10"; ukSize = "4"; }
            
            document.getElementById('stitch-result').innerHTML = `
                <strong>US Size:</strong> ${usSize}<br>
                <strong>UK/Canadian Size:</strong> ${ukSize}
            `;
        });
    }

    // 3. Simple Row Counter
    const rowCounterDisplay = document.getElementById('row-count');
    const rowCounterPlus = document.getElementById('row-plus');
    const rowCounterMinus = document.getElementById('row-minus');
    const rowCounterReset = document.getElementById('row-reset');
    
    if (rowCounterDisplay) {
        let count = 0;
        
        rowCounterPlus.addEventListener('click', () => {
            count++;
            rowCounterDisplay.textContent = count;
        });
        
        rowCounterMinus.addEventListener('click', () => {
            if (count > 0) count--;
            rowCounterDisplay.textContent = count;
        });
        
        rowCounterReset.addEventListener('click', () => {
            count = 0;
            rowCounterDisplay.textContent = count;
        });
    }
});

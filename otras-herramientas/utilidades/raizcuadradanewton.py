<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Visualizador Algoritmo de Newton</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; background: #f4f4f9; }
        .controls { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 20px; }
        #plot { width: 90vw; height: 70vh; }
        input { width: 60px; margin-right: 10px; }
    </style>
</head>
<body>

    <h2>Método de Newton: Raíz Cuadrada</h2>
    
    <div class="controls">
        Número (a): <input type="number" id="target" value="16" step="1">
        Aproximación Inicial (x₀): <input type="number" id="guess" value="1" step="0.5">
        Iteraciones: <input type="number" id="iters" value="5" min="1" max="10">
        <button onclick="visualize()">Calcular y Graficar</button>
    </div>

    <div id="plot"></div>

    <script>
        function visualize() {
            const a = parseFloat(document.getElementById('target').value);
            let xn = parseFloat(document.getElementById('guess').value);
            const iterations = parseInt(document.getElementById('iters').value);

            const xValues = [];
            const yValues = [];
            for (let x = 0; x <= Math.max(a, xn * 1.5) + 2; x += 0.1) {
                xValues.push(x);
                yValues.push(x * x - a);
            }

            const data = [
                { x: xValues, y: yValues, name: 'f(x) = x² - a', line: { color: 'blue' } },
                { x: [0, Math.max(...xValues)], y: [0, 0], name: 'Eje X', line: { color: 'black', dash: 'dash' } }
            ];

            let currentX = xn;
            for (let i = 0; i < iterations; i++) {
                let fx = currentX * currentX - a;
                let dfx = 2 * currentX;
                let nextX = currentX - fx / dfx;

                // Línea vertical hacia la curva
                data.push({
                    x: [currentX, currentX],
                    y: [0, fx],
                    mode: 'lines',
                    line: { color: 'red', dash: 'dot' },
                    showlegend: i === 0,
                    name: 'Proyección'
                });

                // Línea tangente hacia el eje X
                data.push({
                    x: [currentX, nextX],
                    y: [fx, 0],
                    mode: 'lines+markers',
                    line: { color: 'green' },
                    showlegend: i === 0,
                    name: 'Tangente (Newton)'
                });

                currentX = nextX;
            }

            const layout = {
                title: `Buscando √${a} ≈ ${currentX.toFixed(6)}`,
                xaxis: { title: 'x' },
                yaxis: { title: 'f(x)' },
                hovermode: 'closest'
            };

            Plotly.newPlot('plot', data, layout);
        }

        visualize(); // Carga inicial
    </script>
</body>
</html>
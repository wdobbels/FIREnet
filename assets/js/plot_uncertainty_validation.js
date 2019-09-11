// Put all in anonymous function to avoid scope overlap between scripts
(function() {
    let plotname = 'uncertainty_validation';
    let filename = 'https://raw.githubusercontent.com/wdobbels/FIREnet/gh-pages/assets/data/uncertainty_validation.csv';
    let opacity_value = 0.3;
    let size_value = 6.;

    // Array of properties for each datapoint
    let default_colors;
    let default_opacity;
    let default_size;

    let plotDiv;

    function plotFromCsv() {
        Plotly.d3.csv(filename, processData);
    }

    function processData(allRows) {
        let x = [], y = [], c = [], names = [];
        let xbin = [], ybin = [];
        for(let i=0; i < allRows.length; i++) {
            row = allRows[i];
            if(row['galname'] != 'binned') {
                x.push(row['pred_unc']);
                y.push(row['y_diff']);
                c.push(row['density']);
                names.push(row['galname']);
            } else {
                xbin.push(row['pred_unc']);
                ybin.push(row['y_diff']);
            }
        }
        c = toColors(c);  // Immediately go to rgb/hex, so we can change on highlight
        default_colors = c;
        let traces = [scatterTrace(x, y, c, names), oneToOneTrace(false), 
                    oneToOneTrace(true), binnedTrace(xbin, ybin),
                    binnedTrace(xbin, ybin, true)];
        createPlot(traces);
    }

    function createPlot(traces) {
        plotDiv = document.getElementById(plotname);
        let labelsize = 18;
        let layout = {
            hovermode: 'closest',
            title: 'Click a data point to select that galaxy',
            xaxis: {
                title: {
                    text: 'Predicted RMS uncertainty',
                    font: {size: labelsize}
                }
            },
            yaxis: {
                title: {
                    text: 'Predicted - True',
                    font: {size: labelsize}
                }
            }
        }
        Plotly.newPlot(plotDiv, traces, layout);
        plotDiv.on('plotly_click', on_click);
    }

    // Continuous color to rgb or hex
    function toColors(c){
        let scalefunc = d3.interpolateInferno;
        let colors = [];
        let maxcol = Math.max(...c);
        c.forEach(el => {
            colors.push(scalefunc(el / maxcol));
        })
        return colors;
    }

    function scatterTrace(x, y, c, names) {
        let opacity = [];
        let size = [];
        x.forEach(() => {
            opacity.push(opacity_value);
            size.push(size_value);
        });
        default_opacity = opacity;
        default_size = size;
        let trace = {
            x: x,
            y: y,
            mode: 'markers',
            type: 'scattergl',
            text: names,
            marker: {
                color: c,
                size: size,
                opacity: opacity,
                line: { width: 0 }
            },
            name: 'Data points'
        }
        return trace;
    }

    function oneToOneTrace(invert=False) {
        let range = [0, 0.8];
        let yrange = range;
        if(invert) {
            yrange = range.map(x => -x);
        }
        let trace = {
            x: range,
            y: yrange,
            type: 'scattergl',
            mode: 'lines',
            line: {
                color: 'black'
            },
            name: 'one-to-one',
            legendgroup: '1to1',
            showlegend: invert
        }
        return trace;
    }

    function binnedTrace(xbin, ybin, invert=false) {
        if (invert) {
            ybin = ybin.map(x => -x);
        }
        let trace = {
            x: xbin,
            y: ybin,
            type: 'scattergl',
            mode: 'lines',
            line: {
                color: '#029386',
                width: 5.
            },
            name: 'Binned RMS(Predicted - True)',
            legendgroup: 'binned',
            showlegend: invert
        }
        return trace;
    }

    function on_click(data) {
        let selectedColor = '#f76d16';
        let selectedOpacity = 1.;
        let selectedSize = 8.;
        console.log(data);
        console.log('Selected', data.points[0].text);
        let point = data.points[0];  // Only first selected point
        let selectedName = point.text;
        
        let colors = [...default_colors];  // copy from default
        let opacities = [...default_opacity];
        let sizes = [...default_size];
        for(let i=0; i < point.data.text.length; i++) {
            if(point.data.text[i] == selectedName) {
                console.log('Index', i, 'has name', selectedName);
                colors[i] = selectedColor;
                opacities[i] = selectedOpacity;
                sizes[i] = selectedSize;
            }
        }
        let update = {'marker.color': [colors], 'marker.size': [sizes],
                    'marker.opacity': [opacities]};
        Plotly.restyle(plotname, update, [point.curveNumber]);
        update = {title: 'Selected '+selectedName};
        Plotly.relayout(plotname, update);
        sed_globals.selectGalaxySed(selectedName);  // Update SED
    }

    plotFromCsv()
})()
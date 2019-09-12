let tvp_globals = {};

// Put all in anonymous function to avoid scope overlap between scripts
(function(){
    let plotname = 'true_vs_predicted';
    let filename = 'https://raw.githubusercontent.com/wdobbels/FIREnet/gh-pages/assets/data/true_vs_predicted.csv';

    let plotDiv = document.getElementById(plotname);
    // galaxy name + FIR bands for full, pred, fullerr, prederr + properties for each of those
    let allBands;
    let plotBands = ['PACS_70', 'PACS_100', 'PACS_160', 'SPIRE_250', 'SPIRE_350',
                     'SPIRE_500', 'dust luminosity', 'dust mass', 'dust temperature'];
    let band_fluxes = {}; // Map from band (or property) to array of all fluxes

    // defaults. Colors has a separate array for each plotBand, the rest has one array.
    let defaultColors = [], defaultOpacities, defaultSizes;

    function plotFromCsv() {
        Plotly.d3.csv(filename, processData);
    }

    function processData(allRows) {
        // Initialize
        allBands = Object.keys(allRows[0]);
        allBands.forEach(colName => {
            band_fluxes[colName] = [];
        });
        let val;
        allRows.forEach(row => {
            allBands.forEach(band => {
                val = (band == 'galname') ? row[band] : +row[band];
                band_fluxes[band].push(val);
            });
        });
        console.log(band_fluxes);
        createPlot();
    }

    function createPlot() {
        let dataTraces = [];
        let oneToOneTraces = [];
        plotBands.forEach((bandName, bandId) => {
            setDefaults(bandName);
            dataTraces.push(createTrace(bandId + 1, bandName));
            oneToOneTraces.push(createOneToOne(bandId + 1, bandName));
        });
        let layout = createLayout();
        Plotly.newPlot(plotDiv, [...dataTraces, ...oneToOneTraces], layout);
        plotDiv.on('plotly_click', onClick);
    }

    function createLayout(){
        let naxis = 9;
        let ncols = 3, nrows = 3;
        let marginSize = 0.05;
        let plotWidth = (1 - ((ncols - 1) * marginSize)) / ncols;
        let gapHeight = 0.03;
        let plotHeight = (1 - ((nrows - 1) * marginSize) - gapHeight) / nrows;
        let irow, icol, startx, starty, id, bandTitle;
        let layout = {
            title:  'Click a data point to select that galaxy',
            hovermode: 'closest',
            paper_bgcolor: '#fcf6ef',
            plot_bgcolor: '#fffdfa'
        }
        let labelDistance = 0.05;
        let annotations = [
            createAnnotation({x: -labelDistance, y: 2*plotHeight + gapHeight + 1.5*marginSize, 
                              text: 'log(<i>F</i><sub>pred</sub> / <i>F</i><sub>3.4 µm</sub>)', 
                              vertical: true}),
            createAnnotation({x: 0.5, y: plotHeight + gapHeight + marginSize - labelDistance,
                              text: 'log(<i>F</i><sub>true</sub> / <i>F</i><sub>3.4 µm</sub>)'}),
            createAnnotation({x: -labelDistance, y: plotHeight / 2, text: 'Predicted', vertical: true}),
            createAnnotation({x: plotWidth / 2, y: -labelDistance, 
                              text: 'True <i>L<sub>d</sub></i> [<i>L</i><sub>⨀</sub>]'}),
            createAnnotation({x: plotWidth * 1.5 + marginSize, y: -labelDistance, 
                              text: 'True <i>M<sub>d</sub></i> [<i>M</i><sub>⨀</sub>]'}),
            createAnnotation({x: plotWidth * 2.5 + 2 * marginSize, y: -labelDistance, 
                              text: 'True <i>T<sub>d</sub></i> [K]'})
        ];
        
        for(let i=0; i < naxis; i++) {
            irow = Math.floor(i / ncols);
            icol = i % ncols;
            startx = icol * (plotWidth + marginSize);
            starty = irow * (plotHeight + marginSize);
            // Properties: extra gap
            if (irow >= 2) {
                starty += gapHeight;
            }
            // Plotly coordinates centered in bottom left
            starty = 1 - starty - plotHeight;
            // id = i == 0 ? '' : i+1;
            id = i + 1;
            axistype = (i == 6) || (i == 7) ? 'log' : 'linear';
            layout['xaxis'+id] = {
                domain: [startx, startx + plotWidth],
                anchor: 'y'+id,
                type: axistype
            }
            layout['yaxis'+id] = {
                domain: [starty, starty + plotHeight],
                anchor: 'x'+id,
                type: axistype,
            }
            bandTitle = `<b>${plotBands[i].replace('_', ' ')}</b>`
            annotations.push(createAnnotation({x: startx+plotWidth-0.01, y: starty+0.01, text: bandTitle,
                                               xanchor: 'right', yanchor: 'bottom', fontsize: 15}));
        }
        layout.annotations = annotations;
        return layout;
    }

    function createAnnotation({x, y, text, xanchor='center', yanchor='middle', vertical=false, fontsize=16}) {
        let textAngle = vertical ? 270 : 0;
        return {
            xref: 'paper',
            yref: 'paper',
            x: x,
            y: y,
            xanchor: xanchor,
            yanchor: yanchor,
            text: text,
            showarrow: false,
            font: {size: fontsize},
            textangle: textAngle
        }
    }

    function setDefaults(bandname) {
        let c = toColors(band_fluxes['color-'+bandname]);
        defaultColors.push(c);
        defaultOpacities = (new Array(c.length)).fill(0.3);
        defaultSizes = (new Array(c.length)).fill(6);
    }

    function createTrace(plotid, bandname) {
        let trace = {
            x: band_fluxes['full-'+bandname],
            y: band_fluxes['pred-'+bandname],
            text: band_fluxes['galname'],
            type: 'scattergl',
            mode: 'markers',
            name: (plotid == 7) ? 'data points' : bandname,
            xaxis: 'x'+plotid,
            yaxis: 'y'+plotid,
            marker: {
                color: defaultColors[plotid-1],
                opacity: 0.3,
                line: { width: 0 }
            },
            legendgroup: 'data points',
            showlegend: plotid == 7
        }
        return trace;
    }

    function createOneToOne(plotid, bandname) {
        let values = band_fluxes['full-'+bandname];
        let min = Math.min(...values), max = Math.max(...values);
        let trace = {
            x: [min, max],
            y: [min, max],
            type: 'scattergl',
            mode: 'lines',
            legendgroup: 'one-to-one',
            xaxis: 'x'+plotid,
            yaxis: 'y'+plotid,
            line: {
                color: '#00751f' //'#153569'
            },
            name: 'one-to-one',
            showlegend: plotid == 1
        }
        return trace;
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

    tvp_globals.selectGalaxy = function(galname) {
        let {selectedColor, selectedOpacity, selectedSize} = sed_globals;
        let i, j;
        console.log('Selected', galname);
        // Copy from default
        let colors = [], traceIds = [];
        for (i=0; i < defaultColors.length; i++) {
            colors.push([...defaultColors[i]]);
            traceIds.push(i);
        }
        console.log(colors);
        let opacities = [...defaultOpacities];
        let sizes = [...defaultSizes];
        let galnames = band_fluxes['galname'];
        // Highlight selected
        for(i=0; i < galnames.length; i++) {
            if(galnames[i] == galname) {
                for(j=0; j < defaultColors.length; j++) {
                    colors[j][i] = selectedColor;
                }
                opacities[i] = selectedOpacity;
                sizes[i] = selectedSize;
            }
        }
        console.log(colors);
        // Pass updates to Plotly
        let update = {'marker.color': colors, 'marker.size': [sizes],
                      'marker.opacity': [opacities]};
        Plotly.restyle(plotname, update, traceIds);
        update = {title: 'Selected '+galname};
        Plotly.relayout(plotname, update);
    }

    function onClick(data) {
        let selectedName = data.points[0].text;
        // Update this tvp plot
        tvp_globals.selectGalaxy(selectedName);
        // Update uncertainty validation plot
        uncval_globals.selectGalaxy(selectedName);
        // Update SED
        sed_globals.selectGalaxySed(selectedName);
    }

    plotFromCsv();
})()
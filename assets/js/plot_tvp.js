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

    function plotFromCsv() {
        Plotly.d3.csv(filename, processData);
    }

    function processData(allRows) {
        // Initialize
        allBands = Object.keys(allRows[0]);
        allBands.forEach(colName => {
            band_fluxes[colName] = [];
        });
        allRows.forEach(row => {
            allBands.forEach(band => {
                band_fluxes[band].push(+row[band]);
            });
        });
        console.log(band_fluxes);
        createPlot();
    }

    function createPlot() {
        let traces = [];
        plotBands.forEach((bandName, bandId) => {
            traces.push(createTrace(bandId + 1, bandName));
        });
        let layout = createLayout();
        Plotly.newPlot(plotDiv, traces, layout);
    }

    function createLayout(){
        let naxis = 9;
        let ncols = 3, nrows = 3;
        let marginSize = 0.05;
        let plotWidth = (1 - ((ncols - 1) * marginSize)) / ncols;
        let gapHeight = 0.03;
        let plotHeight = (1 - ((nrows - 1) * marginSize) - gapHeight) / nrows;
        let irow, icol, startx, starty, id;
        let layout = {
            title:  'Predicted vs True',
            hovermode: 'closest'
        }
        
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
            layout['xaxis'+id] = {
                domain: [startx, startx + plotWidth],
                anchor: 'y'+id
            }
            layout['yaxis'+id] = {
                domain: [starty, starty + plotHeight],
                anchor: 'x'+id
            }
        }
        return layout;
    }

    function createTrace(plotid, bandname) {
        let trace = {
            x: band_fluxes['full-'+bandname],
            y: band_fluxes['pred-'+bandname],
            text: band_fluxes['galname'],
            type: 'scattergl',
            mode: 'markers',
            name: bandname,
            xaxis: 'x'+plotid,
            yaxis: 'y'+plotid,
            marker: {
                // color: c,
                opacity: 0.3,
                line: { width: 0 }
            }
        }
        return trace;
    }

    plotFromCsv();
})()
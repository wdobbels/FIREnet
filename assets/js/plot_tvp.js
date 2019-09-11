// Put all in anonymous function to avoid scope overlap between scripts
(function(){
    let plotname = 'true_vs_predicted';
    let filename = 'https://raw.githubusercontent.com/wdobbels/FIREnet/gh-pages/assets/data/seds.csv';

    let plotDiv = document.getElementById(plotname);

    function createPlot() {
        let traces = [];
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
        let irow, icol, startx, starty;
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

            layout['xaxis'+i] = {
                domain: [startx, startx + plotWidth],
                anchor: 'y'+i
            }
            layout['yaxis'+i] = {
                domain: [starty, starty + plotHeight],
                anchor: 'x'+i
            }
        }
        return layout;
    }

    createPlot();
})()
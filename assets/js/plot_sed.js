// Global function
let sed_globals = {
    selectedColor: '#f76d16',
    selectedOpacity: 1.,
    selectedSize: 8.
};

// Put all in anonymous function to avoid scope overlap between scripts
(function(){
    let plotname = 'sed';
    let filename = 'https://raw.githubusercontent.com/wdobbels/FIREnet/gh-pages/assets/data/seds.csv';

    let selected = 'G12.DR1.3786';
    let plotDiv = document.getElementById(plotname);
    let galname_fluxes;  // map from galname to its fluxes

    let bands = ['GALEX_FUV', 'GALEX_NUV', 'SDSS_u', 'SDSS_g', 'SDSS_r',
                 'SDSS_i', 'SDSS_z', '2MASS_J', '2MASS_H', '2MASS_Ks',
                 'WISE_3.4', 'WISE_4.6', 'WISE_12', 'WISE_22', 'PACS_70',
                 'PACS_100', 'PACS_160', 'SPIRE_250', 'SPIRE_350', 'SPIRE_500']
    let wavelengths = [
            1.53000e-01, 2.29000e-01, 3.55000e-01, 4.80000e-01, 6.24000e-01,
            7.66000e-01, 9.08000e-01, 1.23500e+00, 1.64500e+00, 2.16000e+00,
            3.36800e+00, 4.61700e+00, 1.20690e+01, 2.21950e+01, 7.07300e+01,
            1.00651e+02, 1.60976e+02, 2.52104e+02, 3.53052e+02, 5.13118e+02
            ]
    let colors = {'short': '#e41a1c', 'pred': '#ff7e19', 'full': '#377eb8',
                  'obs': '#000000'}
    let simnames = Object.keys(colors);

    function plotFromCsv() {
        Plotly.d3.csv(filename, processData);
    }

    function processData(allRows) {
        galname_fluxes = {};
        allRows.forEach(row => {
            galname = row.galname
            delete row.galname
            galname_fluxes[galname] = row
        });
        createPlot(galname_fluxes[selected]);
    }

    function createPlot(fluxes) {
        let traces = [];
        // errors
        simnames.forEach(simname => {
            traces.push(createTrace(simname, fluxes, true));
        });
        // markers + lines
        simnames.forEach(simname => {
            traces.push(createTrace(simname, fluxes, false));
        });
        let labelsize = 18;
        let layout = {
            hovermode: 'closest',
            title: 'SED of '+selected,
            xaxis: {
                title: {
                    text: 'Wavelength (µm)',
                    font: {size: labelsize}
                },
                type: 'log',
                autorange: true
            },
            yaxis: {
                title: {
                    text: 'log(<i>L<sub>ν</sub></i> / (W/Hz))',
                    font: {size: labelsize}
                }
            }
        }
        Plotly.newPlot(plotDiv, traces, layout);
    }

    // Trace for either of the simulations
    function createTrace(simname, fluxes, plot_errors=false) {
        let {flux_values, err_values, wls, bandnames} = extractFluxes(simname, fluxes);
        let trace = {
            x: wls,
            y: flux_values,
            text: bandnames,
            type: 'scatter',
            mode: 'markers+lines',
            error_y: {
                type: 'data',
                array: err_values,
                visible: plot_errors
            },
            line: {
                color: colors[simname]
            },
            marker: {
                size: 7,
                color: colors[simname]
            },
            opacity: 0.7,
            name: simname
        }
        if(simname == 'obs') {
            trace.mode = 'markers';
            trace.marker.symbol = 'square';
        }
        if(plot_errors) {
            trace.opacity = 0.4;
            trace.mode = 'markers';
            trace.marker.size = 0;
            trace.name = 'uncertainties';
            trace.legendgroup = 'uncertainties';
            trace.showlegend = simname == 'full';
        }
        return trace;
    }

    // Get SED data
    function extractFluxes(simname, fluxes) {
        // fluxes example: {'full-2MASS_H': "22.53", 'full-2MASS_J': "22.49", ...}
        let flux_values = [], err_values = [], wls = [], bandnames = [];
        let bandname, errname;
        for(let i=0; i < bands.length; i++) {
            bandname = simname + '-' + bands[i];
            errname = simname +'err-' + bands[i];
            if ((bandname in fluxes) && (fluxes[bandname].length > 0)) {
                flux_values.push(+fluxes[bandname]);
                err_values.push(+fluxes[errname]);
                wls.push(wavelengths[i]);
                bandnames.push(bands[i]);
            }
        }
        return {flux_values, err_values, wls, bandnames};
    }

    sed_globals.selectGalaxySed = function(galname) {
        console.log("Selected", galname, "in SED");
        selected = galname;
        let fluxes = galname_fluxes[selected];
        let flux_values, err_values, wls, bandnames;
        let li_flux_values = new Array(6), li_err_values = new Array(6);
        for(let i=0; i < 3; i++) {
            ({flux_values, err_values, wls, bandnames} = extractFluxes(simnames[i], fluxes));
            li_flux_values[i] = flux_values;
            li_flux_values[i+3] = flux_values;
            li_err_values[i] = err_values;
            li_err_values[i+3] = err_values;
        }
        let update = {
            y: li_flux_values,
            'error_y.array': li_err_values
        };
        // Update short, pred, full
        Plotly.restyle(plotDiv, update, [0, 1, 2, 4, 5, 6]);
        // Update obs (wavelengths can shift)
        ({flux_values, err_values, wls, bandnames} = extractFluxes('obs', fluxes));
        update = {
            x: [wls],
            y: [flux_values],
            'error_y.array': [err_values]
        };
        Plotly.restyle(plotDiv, update, [3, 7]);
        // Update title
        Plotly.relayout(plotDiv, {title: 'SED of '+galname});
    }

    plotFromCsv()
})()
// Plotting functionality for PK Analysis Platform

// Render NCA plots from data
function renderNCAPlots(data) {
    const subjects = Object.keys(data).filter(key => key !== 'summary');
    if (subjects.length === 0) return;

    // Linear concentration-time plot
    const concTimeLinear = document.getElementById('concTimeLinear');
    if (concTimeLinear) {
        const traces = [];

        // Add individual subject traces
        subjects.forEach(subject => {
            traces.push({
                x: data[subject].times,
                y: data[subject].concentrations,
                type: 'scatter',
                mode: 'lines+markers',
                name: `Subject ${subject}`,
                marker: { size: 8 }
            });
        });

        const layout = {
            title: 'Concentration vs. Time',
            xaxis: {
                title: 'Time (h)',
                zeroline: false
            },
            yaxis: {
                title: 'Concentration',
                zeroline: false
            },
            hovermode: 'closest',
            legend: {
                x: 1,
                xanchor: 'right',
                y: 1
            },
            template: 'plotly_dark',
            autosize: true
        };

        Plotly.newPlot(concTimeLinear, traces, layout, { responsive: true });
    }

    // Semi-logarithmic concentration-time plot
    const concTimeSemilog = document.getElementById('concTimeSemilog');
    if (concTimeSemilog) {
        const traces = [];

        // Add individual subject traces
        subjects.forEach(subject => {
            traces.push({
                x: data[subject].times,
                y: data[subject].concentrations,
                type: 'scatter',
                mode: 'lines+markers',
                name: `Subject ${subject}`,
                marker: { size: 8 }
            });
        });

        const layout = {
            title: 'Semi-log Concentration vs. Time',
            xaxis: {
                title: 'Time (h)',
                zeroline: false
            },
            yaxis: {
                title: 'Concentration',
                type: 'log',
                zeroline: false
            },
            hovermode: 'closest',
            legend: {
                x: 1,
                xanchor: 'right',
                y: 1
            },
            template: 'plotly_dark',
            autosize: true
        };

        Plotly.newPlot(concTimeSemilog, traces, layout, { responsive: true });
    }

    // Elimination phase plot for lambda_z visualization
    if (document.getElementById('eliminationPlot')) {
        const subject = subjects[0]; // Default to first subject
        
        if (data[subject].adjusted_points) {
            const traces = [
                // Original data points
                {
                    x: data[subject].times,
                    y: data[subject].concentrations,
                    type: 'scatter',
                    mode: 'markers',
                    name: 'Observed',
                    marker: { size: 10 }
                },
                // Regression line for lambda_z
                {
                    x: data[subject].adjusted_points.map(point => point[0]),
                    y: data[subject].adjusted_points.map(point => point[1]),
                    type: 'scatter',
                    mode: 'lines',
                    name: 'λz Regression',
                    line: { 
                        dash: 'dash',
                        width: 2,
                        color: 'rgba(255, 99, 132, 1)' 
                    }
                }
            ];

            const layout = {
                title: 'Elimination Phase',
                xaxis: {
                    title: 'Time (h)',
                    zeroline: false
                },
                yaxis: {
                    title: 'Concentration (log scale)',
                    type: 'log',
                    zeroline: false
                },
                hovermode: 'closest',
                annotations: [
                    {
                        x: 0.05,
                        y: 0.95,
                        xref: 'paper',
                        yref: 'paper',
                        text: `λz = ${data[subject].lambda_z?.toFixed(4) || 'N/A'}<br>R² = ${data[subject].r_squared?.toFixed(4) || 'N/A'}<br>t½ = ${data[subject].half_life?.toFixed(4) || 'N/A'} h`,
                        showarrow: false,
                        bgcolor: 'rgba(0,0,0,0.7)',
                        bordercolor: 'rgba(255,255,255,0.5)',
                        borderwidth: 1,
                        font: { color: 'white' }
                    }
                ],
                template: 'plotly_dark',
                autosize: true
            };

            Plotly.newPlot('eliminationPlot', traces, layout, { responsive: true });
        }
    }
}

// Render compartmental model plots
function renderCompartmentalPlots(data) {
    const subjects = Object.keys(data).filter(key => key !== 'summary');
    if (subjects.length === 0) return;

    // Default to first subject
    updateModelPlot(data, subjects[0]);

    // Render residual plots for each subject
    subjects.forEach(subject => {
        renderResidualPlot(data[subject], subject);
    });
}

// Update model fit plot for a specific subject
function updateModelPlot(data, subjectId) {
    const modelFitPlot = document.getElementById('modelFitPlot');
    if (!modelFitPlot) return;

    const subjectData = data[subjectId];
    if (!subjectData || 
        !subjectData.observed_times || 
        !subjectData.observed_concentrations ||
        !subjectData.predicted_times ||
        !subjectData.predicted_concentrations) {
        console.error('Missing required plot data for subject', subjectId);
        return;
    }

    const traces = [
        // Observed data
        {
            x: subjectData.observed_times,
            y: subjectData.observed_concentrations,
            type: 'scatter',
            mode: 'markers',
            name: 'Observed',
            marker: { 
                size: 10,
                color: 'rgba(99, 255, 132, 1)' 
            }
        },
        // Predicted curve
        {
            x: subjectData.predicted_times,
            y: subjectData.predicted_concentrations,
            type: 'scatter',
            mode: 'lines',
            name: 'Model Fit',
            line: { 
                width: 2,
                color: 'rgba(132, 99, 255, 1)' 
            }
        }
    ];

    const layout = {
        title: `Model Fit - Subject ${subjectId}`,
        xaxis: {
            title: 'Time (h)',
            zeroline: false
        },
        yaxis: {
            title: 'Concentration',
            zeroline: false
        },
        hovermode: 'closest',
        legend: {
            x: 1,
            xanchor: 'right',
            y: 1
        },
        template: 'plotly_dark',
        autosize: true
    };

    Plotly.newPlot(modelFitPlot, traces, layout, { responsive: true });

    // Create semi-log plot version if exists
    const semilogPlot = document.getElementById('modelFitSemilog');
    if (semilogPlot) {
        const semilogLayout = { ...layout };
        semilogLayout.title += ' (Semi-log)';
        semilogLayout.yaxis.type = 'log';
        
        Plotly.newPlot(semilogPlot, traces, semilogLayout, { responsive: true });
    }
}

// Render residual plot for model diagnostics
function renderResidualPlot(subjectData, subjectId) {
    const residualsPlot = document.getElementById(`residualsPlot-${subjectId}`);
    if (!residualsPlot) return;

    if (!subjectData || 
        !subjectData.goodness_of_fit ||
        !subjectData.goodness_of_fit.residuals) {
        console.error('Missing residuals data for subject', subjectId);
        return;
    }

    const residuals = subjectData.goodness_of_fit.residuals;
    const timePoints = Array.from({ length: residuals.length }, (_, i) => i + 1);

    const traces = [
        {
            x: timePoints,
            y: residuals,
            type: 'scatter',
            mode: 'markers',
            marker: { 
                size: 10,
                color: 'rgba(255, 99, 132, 1)' 
            },
            name: 'Residuals'
        },
        {
            x: [timePoints[0], timePoints[timePoints.length - 1]],
            y: [0, 0],
            type: 'scatter',
            mode: 'lines',
            line: { 
                dash: 'dash',
                width: 1,
                color: 'rgba(200, 200, 200, 0.8)' 
            },
            name: 'Zero Line'
        }
    ];

    const layout = {
        title: `Residuals Plot - Subject ${subjectId}`,
        xaxis: {
            title: 'Observation',
            zeroline: false
        },
        yaxis: {
            title: 'Residual',
            zeroline: true
        },
        hovermode: 'closest',
        template: 'plotly_dark',
        autosize: true
    };

    Plotly.newPlot(residualsPlot, traces, layout, { responsive: true });
}

// Render bioequivalence plots
function renderBioequivalencePlots(data) {
    const parameters = Object.keys(data).filter(key => key !== 'summary' && !data[key].error);
    if (parameters.length === 0) return;

    // Bioequivalence ratio plot with confidence intervals
    const bePlot = document.getElementById('bioequivalencePlot');
    if (bePlot) {
        const ratios = parameters.map(param => data[param].ratio);
        const ciLowers = parameters.map(param => data[param].ci_lower);
        const ciUppers = parameters.map(param => data[param].ci_upper);
        
        // Calculate error bar values (distance from the ratio)
        const errorDown = ratios.map((ratio, i) => ratio - ciLowers[i]);
        const errorUp = ratios.map((ratio, i) => ciUppers[i] - ratio);

        const traces = [
            // Ratio points
            {
                x: parameters,
                y: ratios,
                type: 'scatter',
                mode: 'markers',
                marker: { 
                    size: 12,
                    color: parameters.map(param => 
                        data[param].is_bioequivalent ? 'rgba(99, 255, 132, 1)' : 'rgba(255, 99, 132, 1)'
                    )
                },
                name: 'Ratio'
            },
            // Error bars for confidence intervals
            {
                x: parameters,
                y: ratios,
                type: 'scatter',
                mode: 'markers',
                error_y: {
                    type: 'data',
                    symmetric: false,
                    array: errorUp,
                    arrayminus: errorDown,
                    width: 4,
                    thickness: 2
                },
                marker: { opacity: 0 },
                showlegend: false
            }
        ];

        const layout = {
            title: 'Bioequivalence Assessment',
            xaxis: {
                title: 'Parameter',
                zeroline: false,
                type: 'category'
            },
            yaxis: {
                title: 'Test/Reference Ratio (%)',
                zeroline: false,
                range: [70, 135]  // Set appropriate range to view criteria
            },
            hovermode: 'closest',
            shapes: [
                // 80% lower bound line
                {
                    type: 'line',
                    x0: -0.5,
                    y0: 80,
                    x1: parameters.length - 0.5,
                    y1: 80,
                    line: {
                        color: 'rgba(255, 99, 132, 0.7)',
                        width: 2,
                        dash: 'dash'
                    }
                },
                // 125% upper bound line
                {
                    type: 'line',
                    x0: -0.5,
                    y0: 125,
                    x1: parameters.length - 0.5,
                    y1: 125,
                    line: {
                        color: 'rgba(255, 99, 132, 0.7)',
                        width: 2,
                        dash: 'dash'
                    }
                },
                // 100% reference line
                {
                    type: 'line',
                    x0: -0.5,
                    y0: 100,
                    x1: parameters.length - 0.5,
                    y1: 100,
                    line: {
                        color: 'rgba(200, 200, 200, 0.5)',
                        width: 1
                    }
                }
            ],
            annotations: [
                // 80% label
                {
                    x: -0.1,
                    y: 80,
                    xref: 'paper',
                    yref: 'y',
                    text: '80%',
                    showarrow: false,
                    font: { color: 'rgba(255, 99, 132, 1)' }
                },
                // 125% label
                {
                    x: -0.1,
                    y: 125,
                    xref: 'paper',
                    yref: 'y',
                    text: '125%',
                    showarrow: false,
                    font: { color: 'rgba(255, 99, 132, 1)' }
                }
            ],
            template: 'plotly_dark',
            autosize: true
        };

        Plotly.newPlot(bePlot, traces, layout, { responsive: true });
    }

    // Plot comparing test and reference concentration profiles
    const profilesPlot = document.getElementById('profilesPlot');
    if (profilesPlot && window.testData && window.referenceData) {
        const traces = [];
        
        // Add test subject profiles
        const testSubjects = Object.keys(window.testData).filter(key => key !== 'summary');
        testSubjects.forEach(subject => {
            traces.push({
                x: window.testData[subject].times,
                y: window.testData[subject].concentrations,
                type: 'scatter',
                mode: 'lines+markers',
                name: `Test ${subject}`,
                marker: { size: 6 },
                line: { width: 1 },
                legendgroup: 'test'
            });
        });
        
        // Add reference subject profiles
        const refSubjects = Object.keys(window.referenceData).filter(key => key !== 'summary');
        refSubjects.forEach(subject => {
            traces.push({
                x: window.referenceData[subject].times,
                y: window.referenceData[subject].concentrations,
                type: 'scatter',
                mode: 'lines+markers',
                name: `Ref ${subject}`,
                marker: { size: 6 },
                line: { 
                    width: 1,
                    dash: 'dot'
                },
                legendgroup: 'reference'
            });
        });

        const layout = {
            title: 'Test vs. Reference Profiles',
            xaxis: {
                title: 'Time (h)',
                zeroline: false
            },
            yaxis: {
                title: 'Concentration',
                zeroline: false
            },
            hovermode: 'closest',
            template: 'plotly_dark',
            autosize: true
        };

        Plotly.newPlot(profilesPlot, traces, layout, { responsive: true });
    }
}

// Render statistical analysis plots
function renderStatisticsPlots(data) {
    if (!data) return;

    // Handle different statistics types
    if (data.stat_type === 'ttest' || data.stat_type === 'anova') {
        renderTimeResultsPlot(data);
    } else if (data.stat_type === 'regression') {
        renderRegressionPlots(data);
    }
}

// Render time-based statistical results plot
function renderTimeResultsPlot(data) {
    const timeResultsPlot = document.getElementById('timeResultsPlot');
    if (!timeResultsPlot || !data.time_results) return;

    const times = Object.keys(data.time_results).map(Number).sort((a, b) => a - b);
    const means = times.map(time => data.time_results[time].mean);
    const errors = times.map(time => data.time_results[time].sem || data.time_results[time].std / Math.sqrt(data.n_subjects));
    const significant = times.map(time => data.time_results[time].significant);
    
    const traces = [
        // Mean concentration at each time point
        {
            x: times,
            y: means,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Mean',
            marker: { 
                size: 10,
                color: times.map(time => data.time_results[time].significant ? 'rgba(255, 99, 132, 1)' : 'rgba(99, 255, 132, 1)')
            },
            error_y: {
                type: 'data',
                array: errors,
                visible: true,
                thickness: 1.5,
                width: 5
            }
        }
    ];

    const layout = {
        title: `${data.stat_type === 'ttest' ? 'T-test' : 'ANOVA'} Results by Time Point`,
        xaxis: {
            title: 'Time (h)',
            zeroline: false
        },
        yaxis: {
            title: 'Concentration (Mean ± SEM)',
            zeroline: false
        },
        hovermode: 'closest',
        template: 'plotly_dark',
        autosize: true
    };

    Plotly.newPlot(timeResultsPlot, traces, layout, { responsive: true });
}

// Render regression analysis plots
function renderRegressionPlots(data) {
    if (!data.regression_results) return;

    const subjects = Object.keys(data.regression_results);
    if (subjects.length === 0) return;

    const subjectData = data.regression_results[subjects[0]];
    
    // Render regression plots for the first subject initially
    renderSubjectRegressionPlot('regressionPlot', subjectData);

    // Render half-life comparison if multiple subjects
    if (subjects.length > 1) {
        renderHalfLifeComparisonPlot(data);
    }
}

// Render regression plot for a single subject
function renderSubjectRegressionPlot(elementId, subjectData) {
    const plot = document.getElementById(elementId);
    if (!plot || !subjectData || !subjectData.times) return;

    const traces = [
        // Observed data
        {
            x: subjectData.times,
            y: subjectData.observed,
            type: 'scatter',
            mode: 'markers',
            name: 'Observed',
            marker: { size: 10 }
        },
        // Predicted line
        {
            x: subjectData.times,
            y: subjectData.predicted,
            type: 'scatter',
            mode: 'lines',
            name: 'Regression',
            line: { 
                width: 2,
                color: 'rgba(255, 99, 132, 1)' 
            }
        }
    ];

    const layout = {
        title: 'Regression Analysis',
        xaxis: {
            title: 'Time (h)',
            zeroline: false
        },
        yaxis: {
            title: 'Concentration',
            zeroline: false,
            type: 'log'
        },
        hovermode: 'closest',
        annotations: [
            {
                x: 0.05,
                y: 0.95,
                xref: 'paper',
                yref: 'paper',
                text: `Slope = ${subjectData.slope?.toFixed(4) || 'N/A'}<br>` +
                      `R² = ${subjectData.r_squared?.toFixed(4) || 'N/A'}<br>` +
                      `t½ = ${subjectData.half_life?.toFixed(4) || 'N/A'} h`,
                showarrow: false,
                bgcolor: 'rgba(0,0,0,0.7)',
                bordercolor: 'rgba(255,255,255,0.5)',
                borderwidth: 1,
                font: { color: 'white' }
            }
        ],
        template: 'plotly_dark',
        autosize: true
    };

    Plotly.newPlot(plot, traces, layout, { responsive: true });
}

// Render half-life comparison across subjects
function renderHalfLifeComparisonPlot(data) {
    const plot = document.getElementById('halfLifePlot');
    if (!plot || !data.regression_results) return;

    const subjects = Object.keys(data.regression_results);
    const halfLives = subjects.map(subject => {
        const result = data.regression_results[subject];
        return result.half_life;
    }).filter(h => h !== null && h !== undefined);

    const subjectLabels = subjects.filter((subject, index) => 
        data.regression_results[subject].half_life !== null && 
        data.regression_results[subject].half_life !== undefined
    );

    if (halfLives.length === 0) return;

    const traces = [
        {
            x: subjectLabels,
            y: halfLives,
            type: 'bar',
            marker: {
                color: 'rgba(99, 132, 255, 0.7)',
                line: {
                    color: 'rgba(99, 132, 255, 1)',
                    width: 1.5
                }
            }
        }
    ];

    const layout = {
        title: 'Half-Life Comparison',
        xaxis: {
            title: 'Subject',
            zeroline: false,
            type: 'category'
        },
        yaxis: {
            title: 'Half-Life (h)',
            zeroline: false
        },
        hovermode: 'closest',
        template: 'plotly_dark',
        autosize: true
    };

    Plotly.newPlot(plot, traces, layout, { responsive: true });
}

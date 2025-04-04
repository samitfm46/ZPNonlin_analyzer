from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import io
import json
import numpy as np
import base64
from datetime import datetime

def generate_plot(data, plot_type, title='', xlabel='', ylabel=''):
    """Generate a plot based on data and plot type."""
    plt.figure(figsize=(8, 6))
    
    if plot_type == 'concentration_time':
        for subject_id, subject_data in data.items():
            if subject_id != 'summary':
                plt.plot(subject_data['times'], subject_data['concentrations'], 'o-', label=f"Subject {subject_id}")
        
        plt.title(title or 'Concentration vs. Time')
        plt.xlabel(xlabel or 'Time (h)')
        plt.ylabel(ylabel or 'Concentration (ng/mL)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
    
    elif plot_type == 'semilog':
        for subject_id, subject_data in data.items():
            if subject_id != 'summary':
                plt.semilogy(subject_data['times'], subject_data['concentrations'], 'o-', label=f"Subject {subject_id}")
        
        plt.title(title or 'Log Concentration vs. Time')
        plt.xlabel(xlabel or 'Time (h)')
        plt.ylabel(ylabel or 'Concentration (ng/mL)')
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
    
    elif plot_type == 'model_fit':
        subject_id = list(data.keys())[0]  # Take first subject for model fit plot
        subject_data = data[subject_id]
        
        if 'observed_times' in subject_data and 'predicted_times' in subject_data:
            plt.plot(subject_data['observed_times'], subject_data['observed_concentrations'], 'o', label='Observed')
            plt.plot(subject_data['predicted_times'], subject_data['predicted_concentrations'], '-', label='Predicted')
            
            plt.title(title or f'Model Fit - Subject {subject_id}')
            plt.xlabel(xlabel or 'Time (h)')
            plt.ylabel(ylabel or 'Concentration (ng/mL)')
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.legend()
    
    elif plot_type == 'residuals':
        subject_id = list(data.keys())[0]  # Take first subject for residuals plot
        subject_data = data[subject_id]
        
        if 'goodness_of_fit' in subject_data and 'residuals' in subject_data['goodness_of_fit']:
            residuals = subject_data['goodness_of_fit']['residuals']
            plt.stem(range(len(residuals)), residuals)
            plt.axhline(y=0, color='r', linestyle='-')
            
            plt.title(title or f'Residuals - Subject {subject_id}')
            plt.xlabel(xlabel or 'Observation')
            plt.ylabel(ylabel or 'Residual')
            plt.grid(True, linestyle='--', alpha=0.7)
    
    elif plot_type == 'bioequivalence':
        # Create bar chart for bioequivalence ratios with confidence intervals
        parameters = []
        ratios = []
        ci_lowers = []
        ci_uppers = []
        
        for param, param_data in data.items():
            if param != 'summary' and 'ratio' in param_data:
                parameters.append(param)
                ratios.append(param_data['ratio'])
                ci_lowers.append(param_data['ci_lower'])
                ci_uppers.append(param_data['ci_upper'])
        
        x = range(len(parameters))
        
        plt.bar(x, ratios, width=0.6, label='Ratio (%)')
        plt.errorbar(x, ratios, yerr=[np.array(ratios)-np.array(ci_lowers), np.array(ci_uppers)-np.array(ratios)], 
                    fmt='o', color='r', capsize=5)
        
        # Add reference lines for 80-125% criteria
        plt.axhline(y=80, color='r', linestyle='--', label='80% Lower Limit')
        plt.axhline(y=125, color='r', linestyle='--', label='125% Upper Limit')
        plt.axhline(y=100, color='k', linestyle='-', label='Reference (100%)')
        
        plt.title(title or 'Bioequivalence Assessment')
        plt.ylabel(ylabel or 'Test/Reference Ratio (%)')
        plt.xticks(x, parameters)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
    
    # Save plot to bytes buffer
    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format='png', dpi=300)
    buf.seek(0)
    
    # Close the plot to free memory
    plt.close()
    
    return buf

def create_table(data, headers=None):
    """Create a table from data."""
    if headers:
        table_data = [headers]
    else:
        table_data = []
    
    for row in data:
        table_data.append(row)
    
    table = Table(table_data)
    
    # Add table styling
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    
    table.setStyle(style)
    return table

def generate_report(analysis, report_type='pdf'):
    """
    Generate a report for an analysis.
    
    Parameters:
    - analysis: Analysis object from database
    - report_type: Type of report ('pdf' or 'docx')
    
    Returns:
    - Bytes data of the generated report
    """
    # Currently supporting only PDF
    if report_type != 'pdf':
        raise ValueError(f"Unsupported report type: {report_type}")
    
    # Get analysis data
    analysis_type = analysis.type
    parameters = json.loads(analysis.parameters)
    results = json.loads(analysis.results)
    
    # Create buffer for PDF
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=72)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    heading1_style = styles['Heading1']
    heading2_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create custom styles
    body_style = ParagraphStyle(
        'BodyText',
        parent=normal_style,
        spaceBefore=6,
        spaceAfter=6,
        leading=14
    )
    
    # Create document elements
    elements = []
    
    # Add title and header information
    elements.append(Paragraph(f"{analysis_type} Analysis Report", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    elements.append(Paragraph(f"Analysis Name: {analysis.name}", heading2_style))
    elements.append(Paragraph(f"Analysis Type: {analysis.type}", body_style))
    elements.append(Paragraph(f"Date Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add parameters section
    elements.append(Paragraph("Analysis Parameters", heading1_style))
    
    param_data = []
    for key, value in parameters.items():
        param_data.append([key, str(value)])
    
    elements.append(create_table(param_data, headers=['Parameter', 'Value']))
    elements.append(Spacer(1, 0.25*inch))
    
    # Generate appropriate content based on analysis type
    if analysis_type == 'NCA':
        elements.append(Paragraph("Non-Compartmental Analysis Results", heading1_style))
        
        # Add summary statistics
        if 'summary' in results:
            elements.append(Paragraph("Summary Statistics", heading2_style))
            
            summary_data = []
            for key, value in results['summary'].items():
                if isinstance(value, (int, float)):
                    summary_data.append([key, f"{value:.4g}"])
                else:
                    summary_data.append([key, str(value)])
            
            elements.append(create_table(summary_data, headers=['Parameter', 'Value']))
            elements.append(Spacer(1, 0.25*inch))
        
        # Add individual subject results
        elements.append(Paragraph("Individual Subject Results", heading2_style))
        
        subject_ids = [s for s in results if s != 'summary']
        
        param_keys = ['tmax', 'cmax', 'auc_last', 'auc_inf', 'half_life', 'mrt']
        
        # Create table with individual results
        headers = ['Subject ID'] + [p.upper() for p in param_keys]
        ind_data = []
        
        for subject_id in subject_ids:
            row = [subject_id]
            for param in param_keys:
                if param in results[subject_id] and results[subject_id][param] is not None:
                    row.append(f"{results[subject_id][param]:.4g}")
                else:
                    row.append('NA')
            ind_data.append(row)
        
        elements.append(create_table(ind_data, headers=headers))
        elements.append(Spacer(1, 0.5*inch))
        
        # Add plots
        elements.append(Paragraph("Concentration-Time Profiles", heading2_style))
        
        # Linear scale plot
        plot_buf = generate_plot(results, 'concentration_time')
        img = Image(plot_buf, width=6*inch, height=4*inch)
        elements.append(img)
        elements.append(Spacer(1, 0.25*inch))
        
        # Semi-log scale plot
        elements.append(Paragraph("Semi-logarithmic Concentration-Time Profiles", heading2_style))
        plot_buf = generate_plot(results, 'semilog')
        img = Image(plot_buf, width=6*inch, height=4*inch)
        elements.append(img)
    
    elif analysis_type == 'Compartmental':
        elements.append(Paragraph("Compartmental Modeling Results", heading1_style))
        
        # Add model information
        model_type = parameters.get('model_type', 'Unknown')
        absorption = parameters.get('absorption', 'Unknown')
        elements.append(Paragraph(f"Model: {model_type}-compartment with {absorption} absorption", body_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add summary statistics if available
        if 'summary' in results and 'derived_parameters' in results['summary']:
            elements.append(Paragraph("Summary of Derived Parameters", heading2_style))
            
            summary_data = []
            for key, value in results['summary']['derived_parameters'].items():
                if isinstance(value, (int, float)):
                    summary_data.append([key, f"{value:.4g}"])
                else:
                    summary_data.append([key, str(value)])
            
            elements.append(create_table(summary_data, headers=['Parameter', 'Value']))
            elements.append(Spacer(1, 0.25*inch))
        
        # Individual subject results
        subject_ids = [s for s in results if s != 'summary']
        
        for subject_id in subject_ids:
            elements.append(Paragraph(f"Subject {subject_id}", heading2_style))
            
            # Add derived parameters table
            if 'derived_parameters' in results[subject_id]:
                elements.append(Paragraph("Derived Parameters", heading2_style))
                
                derived_data = []
                for key, value in results[subject_id]['derived_parameters'].items():
                    if isinstance(value, (int, float)):
                        derived_data.append([key, f"{value:.4g}"])
                    else:
                        derived_data.append([key, str(value)])
                
                elements.append(create_table(derived_data, headers=['Parameter', 'Value']))
                elements.append(Spacer(1, 0.25*inch))
            
            # Add goodness of fit metrics
            if 'goodness_of_fit' in results[subject_id]:
                elements.append(Paragraph("Goodness of Fit", heading2_style))
                
                gof_data = []
                for key, value in results[subject_id]['goodness_of_fit'].items():
                    if key != 'residuals':  # Skip residuals array
                        if isinstance(value, (int, float)):
                            gof_data.append([key, f"{value:.4g}"])
                        else:
                            gof_data.append([key, str(value)])
                
                elements.append(create_table(gof_data, headers=['Metric', 'Value']))
                elements.append(Spacer(1, 0.25*inch))
            
            # Add model fit plot
            plot_buf = generate_plot({subject_id: results[subject_id]}, 'model_fit')
            img = Image(plot_buf, width=6*inch, height=4*inch)
            elements.append(img)
            elements.append(Spacer(1, 0.25*inch))
            
            # Add residuals plot
            if 'goodness_of_fit' in results[subject_id] and 'residuals' in results[subject_id]['goodness_of_fit']:
                plot_buf = generate_plot({subject_id: results[subject_id]}, 'residuals')
                img = Image(plot_buf, width=6*inch, height=4*inch)
                elements.append(img)
            
            # Add page break between subjects (except for the last one)
            if subject_id != subject_ids[-1]:
                elements.append(PageBreak())
    
    elif analysis_type == 'Bioequivalence':
        elements.append(Paragraph("Bioequivalence Analysis Results", heading1_style))
        
        # Add study design information
        design = parameters.get('design', 'Unknown')
        alpha = parameters.get('alpha', 0.05)
        ci_level = (1 - alpha) * 100
        
        elements.append(Paragraph(f"Study Design: {design}", body_style))
        elements.append(Paragraph(f"Confidence Interval Level: {ci_level}%", body_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Add bioequivalence results for each parameter
        params = [p for p in results if p != 'summary']
        
        for param in params:
            elements.append(Paragraph(f"Bioequivalence Results for {param.upper()}", heading2_style))
            
            if 'error' in results[param]:
                elements.append(Paragraph(f"Error: {results[param]['error']}", body_style))
                continue
            
            be_data = []
            for key, value in results[param].items():
                if isinstance(value, (int, float)):
                    be_data.append([key, f"{value:.4g}"])
                else:
                    be_data.append([key, str(value)])
            
            elements.append(create_table(be_data, headers=['Metric', 'Value']))
            elements.append(Spacer(1, 0.25*inch))
        
        # Add bioequivalence plot
        plot_buf = generate_plot(results, 'bioequivalence')
        img = Image(plot_buf, width=6*inch, height=4*inch)
        elements.append(img)
    
    elif analysis_type == 'Statistics':
        elements.append(Paragraph("Statistical Analysis Results", heading1_style))
        
        stat_type = parameters.get('stat_type', results.get('stat_type', 'Unknown'))
        elements.append(Paragraph(f"Statistical Method: {stat_type}", body_style))
        elements.append(Spacer(1, 0.25*inch))
        
        if stat_type == 'ttest' or stat_type == 'anova':
            if 'time_results' in results:
                elements.append(Paragraph("Results by Time Point", heading2_style))
                
                # Create table for time results
                headers = ['Time']
                if stat_type == 'ttest':
                    headers.extend(['Mean', 'SD', 'CV%', 't-statistic', 'p-value', 'Significant'])
                else:  # anova
                    headers.extend(['Mean', 'SD', 'CV%', 'F-statistic', 'p-value', 'Significant'])
                
                time_data = []
                for time, time_result in sorted(results['time_results'].items()):
                    row = [time]
                    row.append(f"{time_result['mean']:.4g}")
                    row.append(f"{time_result['std']:.4g}")
                    if time_result['cv_percent'] is not None:
                        row.append(f"{time_result['cv_percent']:.2f}%")
                    else:
                        row.append('NA')
                    
                    if stat_type == 'ttest':
                        row.append(f"{time_result['t_stat']:.4g}")
                    else:  # anova
                        row.append(f"{time_result['f_stat']:.4g}")
                    
                    row.append(f"{time_result['p_value']:.4g}")
                    row.append('Yes' if time_result['significant'] else 'No')
                    
                    time_data.append(row)
                
                elements.append(create_table(time_data, headers=headers))
                elements.append(Spacer(1, 0.25*inch))
        
        elif stat_type == 'regression':
            if 'regression_results' in results:
                elements.append(Paragraph("Regression Results by Subject", heading2_style))
                
                # Create table for regression results
                headers = ['Subject ID', 'Slope', 'Intercept', 'R²', 'p-value', 'Half-life']
                reg_data = []
                
                for subject_id, reg_result in results['regression_results'].items():
                    if 'error' in reg_result:
                        continue
                    
                    row = [subject_id]
                    row.append(f"{reg_result['slope']:.4g}")
                    row.append(f"{reg_result['intercept']:.4g}")
                    row.append(f"{reg_result['r_squared']:.4g}")
                    row.append(f"{reg_result['p_value']:.4g}")
                    
                    if reg_result['half_life'] is not None:
                        row.append(f"{reg_result['half_life']:.4g}")
                    else:
                        row.append('NA')
                    
                    reg_data.append(row)
                
                elements.append(create_table(reg_data, headers=headers))
                elements.append(Spacer(1, 0.25*inch))
                
                # Add summary if available
                if 'summary' in results:
                    elements.append(Paragraph("Summary Statistics", heading2_style))
                    
                    summary_data = []
                    for key, value in results['summary'].items():
                        if isinstance(value, (int, float)):
                            summary_data.append([key, f"{value:.4g}"])
                        else:
                            summary_data.append([key, str(value)])
                    
                    elements.append(create_table(summary_data, headers=['Metric', 'Value']))
                    elements.append(Spacer(1, 0.25*inch))
    
    # Build the PDF document
    doc.build(elements)
    
    # Get the PDF data from the buffer
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

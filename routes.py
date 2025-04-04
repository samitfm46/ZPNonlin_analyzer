import os
import uuid
import json
import pandas as pd
import numpy as np
from flask import render_template, request, jsonify, send_file, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from io import BytesIO
import tempfile

from app import app, db
from models import Study, Dataset, Subject, Sample, Analysis, Report
from pk_tools.nca import calculate_nca_parameters
from pk_tools.compartmental import fit_compartmental_model
from pk_tools.bioequivalence import calculate_bioequivalence
from pk_tools.statistics import perform_statistical_analysis
from pk_tools.reports import generate_report
from pk_tools.utils import validate_dataset, transform_data, merge_datasets

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'xls'}

def parse_file(file):
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[1].lower()
    
    if file_ext == 'csv':
        df = pd.read_csv(file)
    else:  # Excel
        df = pd.read_excel(file)
    
    return df

# Main routes
@app.route('/')
def index():
    return render_template('index.html')

# Study management
@app.route('/studies', methods=['GET', 'POST'])
def studies():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Study name is required', 'danger')
            return redirect(url_for('studies'))
        
        study = Study(name=name, description=description)
        db.session.add(study)
        db.session.commit()
        flash('Study created successfully', 'success')
        return redirect(url_for('studies'))
    
    studies = Study.query.all()
    return render_template('index.html', studies=studies)

@app.route('/study/<int:study_id>')
def study_detail(study_id):
    study = Study.query.get_or_404(study_id)
    return render_template('index.html', study=study, active_tab='study')

# Dataset management
@app.route('/study/<int:study_id>/upload', methods=['POST'])
def upload_dataset(study_id):
    study = Study.query.get_or_404(study_id)
    
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('study_detail', study_id=study_id))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('study_detail', study_id=study_id))
    
    if file and allowed_file(file.filename):
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Dataset name is required', 'danger')
            return redirect(url_for('study_detail', study_id=study_id))
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Create dataset in database
        dataset = Dataset(
            name=name,
            description=description,
            file_path=file_path,
            file_type=file_ext,
            study_id=study_id
        )
        db.session.add(dataset)
        db.session.commit()
        
        # Process file
        try:
            df = parse_file(file)
            
            # Validate
            valid, message = validate_dataset(df)
            if not valid:
                flash(f'Invalid dataset: {message}', 'danger')
                return redirect(url_for('study_detail', study_id=study_id))
            
            # Import into database
            for _, group in df.groupby('subject_id'):
                subject_id = group['subject_id'].iloc[0]
                subject = Subject(subject_id=subject_id, dataset_id=dataset.id)
                db.session.add(subject)
                db.session.flush()  # Get subject.id
                
                for _, row in group.iterrows():
                    sample = Sample(
                        time=float(row['time']),
                        concentration=float(row['concentration']),
                        subject_id=subject.id
                    )
                    db.session.add(sample)
            
            db.session.commit()
            flash('Dataset uploaded and processed successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing dataset: {str(e)}', 'danger')
        
        return redirect(url_for('study_detail', study_id=study_id))
    
    flash('Invalid file type. Please upload CSV or Excel file.', 'danger')
    return redirect(url_for('study_detail', study_id=study_id))

@app.route('/dataset/<int:dataset_id>')
def dataset_detail(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    return render_template('data_processing.html', dataset=dataset)

# NCA Analysis
@app.route('/nca', methods=['GET', 'POST'])
def nca():
    if request.method == 'POST':
        dataset_id = request.form.get('dataset_id')
        name = request.form.get('analysis_name')
        
        if not dataset_id or not name:
            flash('Dataset and analysis name are required', 'danger')
            return redirect(url_for('nca'))
        
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Get subjects and samples
        subjects_data = {}
        for subject in dataset.subjects:
            times = []
            concentrations = []
            for sample in subject.samples:
                times.append(sample.time)
                concentrations.append(sample.concentration)
            
            subjects_data[subject.subject_id] = {
                'times': times,
                'concentrations': concentrations
            }
        
        # Calculate NCA parameters
        try:
            results = calculate_nca_parameters(subjects_data)
            
            # Create analysis record
            analysis = Analysis(
                name=name,
                type='NCA',
                parameters=json.dumps({
                    'method': request.form.get('method', 'linear-log'),
                    'dose': float(request.form.get('dose', 0)),
                    'dose_unit': request.form.get('dose_unit', 'mg'),
                    'conc_unit': request.form.get('conc_unit', 'ng/mL'),
                    'time_unit': request.form.get('time_unit', 'h')
                }),
                results=json.dumps(results),
                dataset_id=dataset.id
            )
            db.session.add(analysis)
            db.session.commit()
            
            flash('NCA analysis completed successfully', 'success')
            return redirect(url_for('analysis_detail', analysis_id=analysis.id))
        except Exception as e:
            flash(f'Error performing NCA analysis: {str(e)}', 'danger')
            return redirect(url_for('nca'))
    
    datasets = Dataset.query.all()
    return render_template('nca.html', datasets=datasets)

# Compartmental Analysis
@app.route('/compartmental', methods=['GET', 'POST'])
def compartmental():
    if request.method == 'POST':
        dataset_id = request.form.get('dataset_id')
        name = request.form.get('analysis_name')
        model_type = request.form.get('model_type')
        
        if not dataset_id or not name or not model_type:
            flash('Dataset, analysis name, and model type are required', 'danger')
            return redirect(url_for('compartmental'))
        
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Get subjects and samples
        subjects_data = {}
        for subject in dataset.subjects:
            times = []
            concentrations = []
            for sample in subject.samples:
                times.append(sample.time)
                concentrations.append(sample.concentration)
            
            subjects_data[subject.subject_id] = {
                'times': times,
                'concentrations': concentrations
            }
        
        # Fit compartmental model
        try:
            results = fit_compartmental_model(
                subjects_data,
                model_type=model_type,
                dose=float(request.form.get('dose', 0)),
                absorption=request.form.get('absorption', 'first-order')
            )
            
            # Create analysis record
            analysis = Analysis(
                name=name,
                type='Compartmental',
                parameters=json.dumps({
                    'model_type': model_type,
                    'absorption': request.form.get('absorption', 'first-order'),
                    'dose': float(request.form.get('dose', 0)),
                    'dose_unit': request.form.get('dose_unit', 'mg'),
                    'conc_unit': request.form.get('conc_unit', 'ng/mL'),
                    'time_unit': request.form.get('time_unit', 'h')
                }),
                results=json.dumps(results),
                dataset_id=dataset.id
            )
            db.session.add(analysis)
            db.session.commit()
            
            flash('Compartmental analysis completed successfully', 'success')
            return redirect(url_for('analysis_detail', analysis_id=analysis.id))
        except Exception as e:
            flash(f'Error performing compartmental analysis: {str(e)}', 'danger')
            return redirect(url_for('compartmental'))
    
    datasets = Dataset.query.all()
    return render_template('compartmental.html', datasets=datasets)

# Bioequivalence Analysis
@app.route('/bioequivalence', methods=['GET', 'POST'])
def bioequivalence():
    if request.method == 'POST':
        test_dataset_id = request.form.get('test_dataset_id')
        reference_dataset_id = request.form.get('reference_dataset_id')
        name = request.form.get('analysis_name')
        design = request.form.get('design', 'crossover')
        
        if not test_dataset_id or not reference_dataset_id or not name:
            flash('Test dataset, reference dataset, and analysis name are required', 'danger')
            return redirect(url_for('bioequivalence'))
        
        test_dataset = Dataset.query.get_or_404(test_dataset_id)
        reference_dataset = Dataset.query.get_or_404(reference_dataset_id)
        
        # Get NCA parameters for both datasets
        test_analysis = Analysis.query.filter_by(dataset_id=test_dataset.id, type='NCA').first()
        ref_analysis = Analysis.query.filter_by(dataset_id=reference_dataset.id, type='NCA').first()
        
        if not test_analysis or not ref_analysis:
            flash('NCA analysis must be performed on both datasets first', 'danger')
            return redirect(url_for('bioequivalence'))
        
        test_results = json.loads(test_analysis.results)
        ref_results = json.loads(ref_analysis.results)
        
        # Calculate bioequivalence
        try:
            results = calculate_bioequivalence(test_results, ref_results, design=design)
            
            # Create analysis record
            analysis = Analysis(
                name=name,
                type='Bioequivalence',
                parameters=json.dumps({
                    'design': design,
                    'test_dataset_id': test_dataset_id,
                    'reference_dataset_id': reference_dataset_id,
                    'alpha': 0.05
                }),
                results=json.dumps(results),
                dataset_id=test_dataset.id  # Associate with test dataset
            )
            db.session.add(analysis)
            db.session.commit()
            
            flash('Bioequivalence analysis completed successfully', 'success')
            return redirect(url_for('analysis_detail', analysis_id=analysis.id))
        except Exception as e:
            flash(f'Error performing bioequivalence analysis: {str(e)}', 'danger')
            return redirect(url_for('bioequivalence'))
    
    datasets = Dataset.query.all()
    return render_template('bioequivalence.html', datasets=datasets)

# Data Processing
@app.route('/data-processing', methods=['GET', 'POST'])
def data_processing():
    if request.method == 'POST':
        dataset_id = request.form.get('dataset_id')
        transformation = request.form.get('transformation')
        
        if not dataset_id or not transformation:
            flash('Dataset and transformation are required', 'danger')
            return redirect(url_for('data_processing'))
        
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Get data
        subjects_data = {}
        for subject in dataset.subjects:
            times = []
            concentrations = []
            for sample in subject.samples:
                times.append(sample.time)
                concentrations.append(sample.concentration)
            
            subjects_data[subject.subject_id] = {
                'times': times,
                'concentrations': concentrations
            }
        
        # Apply transformation
        try:
            transformed_data = transform_data(subjects_data, transformation=transformation)
            
            # Create new dataset with transformed data
            new_dataset = Dataset(
                name=f"{dataset.name} - {transformation}",
                description=f"Transformed dataset: {transformation} applied to {dataset.name}",
                file_type=dataset.file_type,
                study_id=dataset.study_id
            )
            db.session.add(new_dataset)
            db.session.flush()  # Get new_dataset.id
            
            # Add transformed data to new dataset
            for subject_id, data in transformed_data.items():
                subject = Subject(subject_id=subject_id, dataset_id=new_dataset.id)
                db.session.add(subject)
                db.session.flush()  # Get subject.id
                
                for i in range(len(data['times'])):
                    sample = Sample(
                        time=data['times'][i],
                        concentration=data['concentrations'][i],
                        subject_id=subject.id
                    )
                    db.session.add(sample)
            
            db.session.commit()
            flash('Data transformation completed successfully', 'success')
            return redirect(url_for('dataset_detail', dataset_id=new_dataset.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error applying transformation: {str(e)}', 'danger')
            return redirect(url_for('data_processing'))
    
    datasets = Dataset.query.all()
    return render_template('data_processing.html', datasets=datasets)

# Statistics
@app.route('/statistics', methods=['GET', 'POST'])
def statistics():
    if request.method == 'POST':
        dataset_id = request.form.get('dataset_id')
        stat_type = request.form.get('stat_type')
        name = request.form.get('analysis_name')
        
        if not dataset_id or not stat_type or not name:
            flash('Dataset, statistical test type, and analysis name are required', 'danger')
            return redirect(url_for('statistics'))
        
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Get data
        subjects_data = {}
        for subject in dataset.subjects:
            times = []
            concentrations = []
            for sample in subject.samples:
                times.append(sample.time)
                concentrations.append(sample.concentration)
            
            subjects_data[subject.subject_id] = {
                'times': times,
                'concentrations': concentrations
            }
        
        # Perform statistical analysis
        try:
            results = perform_statistical_analysis(subjects_data, stat_type=stat_type)
            
            # Create analysis record
            analysis = Analysis(
                name=name,
                type='Statistics',
                parameters=json.dumps({
                    'stat_type': stat_type,
                    'alpha': 0.05
                }),
                results=json.dumps(results),
                dataset_id=dataset.id
            )
            db.session.add(analysis)
            db.session.commit()
            
            flash('Statistical analysis completed successfully', 'success')
            return redirect(url_for('analysis_detail', analysis_id=analysis.id))
        except Exception as e:
            flash(f'Error performing statistical analysis: {str(e)}', 'danger')
            return redirect(url_for('statistics'))
    
    datasets = Dataset.query.all()
    return render_template('statistics.html', datasets=datasets)

# Reports
@app.route('/reports', methods=['GET', 'POST'])
def reports():
    if request.method == 'POST':
        analysis_id = request.form.get('analysis_id')
        name = request.form.get('report_name')
        report_type = request.form.get('report_type', 'pdf')
        
        if not analysis_id or not name:
            flash('Analysis and report name are required', 'danger')
            return redirect(url_for('reports'))
        
        analysis = Analysis.query.get_or_404(analysis_id)
        
        # Generate report
        try:
            report_data = generate_report(analysis, report_type=report_type)
            
            # Save report to file
            unique_filename = f"{uuid.uuid4().hex}.{report_type}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            with open(file_path, 'wb') as f:
                f.write(report_data)
            
            # Create report record
            report = Report(
                name=name,
                file_path=file_path,
                analysis_id=analysis.id
            )
            db.session.add(report)
            db.session.commit()
            
            flash('Report generated successfully', 'success')
            return redirect(url_for('report_detail', report_id=report.id))
        except Exception as e:
            flash(f'Error generating report: {str(e)}', 'danger')
            return redirect(url_for('reports'))
    
    analyses = Analysis.query.all()
    return render_template('reports.html', analyses=analyses)

@app.route('/report/<int:report_id>')
def report_detail(report_id):
    report = Report.query.get_or_404(report_id)
    return render_template('reports.html', report=report)

@app.route('/download-report/<int:report_id>')
def download_report(report_id):
    report = Report.query.get_or_404(report_id)
    
    return send_file(
        report.file_path,
        as_attachment=True,
        download_name=f"{report.name}.{report.file_path.split('.')[-1]}"
    )

# Analysis details
@app.route('/analysis/<int:analysis_id>')
def analysis_detail(analysis_id):
    analysis = Analysis.query.get_or_404(analysis_id)
    
    # Render appropriate template based on analysis type
    if analysis.type == 'NCA':
        return render_template('nca.html', analysis=analysis)
    elif analysis.type == 'Compartmental':
        return render_template('compartmental.html', analysis=analysis)
    elif analysis.type == 'Bioequivalence':
        return render_template('bioequivalence.html', analysis=analysis)
    elif analysis.type == 'Statistics':
        return render_template('statistics.html', analysis=analysis)
    else:
        flash('Unknown analysis type', 'danger')
        return redirect(url_for('index'))

# API endpoints for AJAX calls
@app.route('/api/dataset/<int:dataset_id>/preview')
def api_dataset_preview(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    
    # Get first 10 samples from the dataset
    samples_data = []
    for subject in dataset.subjects[:5]:
        for sample in subject.samples[:10]:
            samples_data.append({
                'subject_id': subject.subject_id,
                'time': sample.time,
                'concentration': sample.concentration
            })
    
    return jsonify({
        'success': True,
        'data': samples_data
    })

@app.route('/api/dataset/<int:dataset_id>/plot-data')
def api_dataset_plot_data(dataset_id):
    dataset = Dataset.query.get_or_404(dataset_id)
    
    # Format data for plotting
    plot_data = []
    for subject in dataset.subjects:
        times = []
        concentrations = []
        for sample in subject.samples:
            times.append(sample.time)
            concentrations.append(sample.concentration)
        
        plot_data.append({
            'subject_id': subject.subject_id,
            'times': times,
            'concentrations': concentrations
        })
    
    return jsonify({
        'success': True,
        'data': plot_data
    })

@app.route('/api/analysis/<int:analysis_id>/plot-data')
def api_analysis_plot_data(analysis_id):
    analysis = Analysis.query.get_or_404(analysis_id)
    
    results = json.loads(analysis.results)
    
    return jsonify({
        'success': True,
        'data': results,
        'type': analysis.type,
        'parameters': json.loads(analysis.parameters)
    })

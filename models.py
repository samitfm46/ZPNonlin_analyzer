from app import db
from datetime import datetime

class Study(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    datasets = db.relationship('Dataset', backref='study', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Study {self.name}>"

class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255))
    file_type = db.Column(db.String(20))  # CSV, Excel, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    study_id = db.Column(db.Integer, db.ForeignKey('study.id'), nullable=False)
    subjects = db.relationship('Subject', backref='dataset', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Dataset {self.name}>"

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.String(50), nullable=False)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    samples = db.relationship('Sample', backref='subject', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Subject {self.subject_id}>"

class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.Float, nullable=False)
    concentration = db.Column(db.Float)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    
    def __repr__(self):
        return f"<Sample {self.id} at {self.time}h: {self.concentration}>"

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # NCA, Compartmental, Bioequivalence
    parameters = db.Column(db.JSON)
    results = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    dataset = db.relationship('Dataset')
    
    def __repr__(self):
        return f"<Analysis {self.id} ({self.type})>"

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    analysis_id = db.Column(db.Integer, db.ForeignKey('analysis.id'), nullable=False)
    analysis = db.relationship('Analysis')
    
    def __repr__(self):
        return f"<Report {self.name}>"

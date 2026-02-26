from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.orm import joinedload
import os
import subprocess
import json
from dotenv import load_dotenv
from code_intelligence import CodeIntelligenceEngine

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'Parth@33')

# MySQL Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'mysql+pymysql://username:parthsparsh@localhost:3306/codesphere_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Gemini API configuration removed as per user request
# Local CodeIntelligenceEngine is used instead

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    submissions = db.relationship('Submission', backref='user', lazy=True)

class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # Easy, Medium, Hard
    category = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    test_cases = db.relationship('TestCase', backref='problem', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('Submission', backref='problem', lazy=True)

class TestCase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    input_data = db.Column(db.Text, nullable=False)
    expected_output = db.Column(db.Text, nullable=False)
    is_hidden = db.Column(db.Boolean, default=False)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(20), nullable=False)  # python, cpp, java
    status = db.Column(db.String(50), default='Pending')  # Accepted, Wrong Answer, Runtime Error, etc.
    test_cases_passed = db.Column(db.Integer, default=0)
    total_test_cases = db.Column(db.Integer, default=0)
    execution_time = db.Column(db.Float)  # in seconds
    memory_used = db.Column(db.Float)  # in MB
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    quality_report = db.relationship('CodeQualityReport', backref='submission', uselist=False, cascade='all, delete-orphan')

class CodeQualityReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submission.id'), nullable=False)
    overall_score = db.Column(db.Float)  # 0-100
    readability_score = db.Column(db.Float)
    maintainability_score = db.Column(db.Float)
    efficiency_score = db.Column(db.Float)
    best_practices_score = db.Column(db.Float)
    time_complexity = db.Column(db.String(100))
    space_complexity = db.Column(db.String(100))
    suggestions = db.Column(db.Text)  # JSON string of suggestions
    detailed_feedback = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Template Filters
@app.template_filter('from_json')
def from_json_filter(value):
    """Parse JSON string in templates"""
    if not value:
        return []
    try:
        return json.loads(value)
    except:
        return []

# Helper Functions
def execute_code(code, language, input_data, timeout=5):
    """
    Execute user code and return output
    Returns: (success: bool, output: str, error: str, execution_time: float)
    """
    import sys
    
    if language != 'python':
        return False, '', f'Language {language} not supported yet', 0

    temp_file = None
    try:
        # Create temp file with unique name
        import uuid
        temp_file = f'temp_code_{os.getpid()}_{uuid.uuid4().hex[:8]}.py'
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Prepare input
        input_str = input_data if isinstance(input_data, str) else str(input_data)
        
        import time
        start_time = time.time()
        
        # Use sys.executable to ensure we use the same Python interpreter
        # This is more robust than trying 'python3' or 'python' commands
        cmd = [sys.executable, temp_file]
        
        result = subprocess.run(
            cmd,
            input=input_str,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        
        execution_time = time.time() - start_time
        
        # Clean up
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        
        if result.returncode == 0:
            return True, result.stdout.strip(), '', execution_time
        else:
            # Capture both stderr and stdout for errors
            error_msg = result.stderr.strip()
            if not error_msg:
                error_msg = result.stdout.strip()
            return False, '', error_msg if error_msg else 'Unknown/Runtime error occurred', execution_time
            
    except subprocess.TimeoutExpired:
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        return False, '', 'Time Limit Exceeded', timeout
    except Exception as e:
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        return False, '', f'Execution error: {str(e)}', 0

def analyze_code_quality(code, language, problem_title):
    """
    Analyze code quality using the local Code Intelligence Engine.
    """
    print(f"Analyzing {language} code for '{problem_title}' using local engine...")
    
    try:
        engine = CodeIntelligenceEngine()
        analysis = engine.analyze(code)
        
        # Default values
        default_score = 70
        
        if analysis['success']:
            metrics = analysis.get('metrics', {})
            
            return {
                "overall_score": analysis.get('overall_quality_score', default_score),
                "readability_score": default_score, # Not reliably in analysis root initially
                "maintainability_score": analysis.get('maintainability_index', default_score),
                "efficiency_score": 70, # Not directly measured by static analysis
                "best_practices_score": default_score,
                "time_complexity": "O(n)", # Placeholder for static analysis
                "space_complexity": "O(1)", # Placeholder
                "suggestions": [{"category": "General", "issue": "Improvement", "suggestion": s, "priority": "medium"} for s in analysis.get('suggestions', [])],
                "detailed_feedback": "Analysis performed by local Code Intelligence Engine.",
                "coding_habits_to_improve": [],
                "raw_metrics": metrics
            }
    except Exception as e:
        print(f"Local analysis failed: {e}")
        
    return {
        "overall_score": 70,
        "readability_score": 70,
        "maintainability_score": 70,
        "efficiency_score": 70,
        "best_practices_score": 70,
        "time_complexity": "O(n)",
        "space_complexity": "O(1)",
        "suggestions": [],
        "detailed_feedback": "Local analysis failed to generate results.",
        "coding_habits_to_improve": []
    }

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    
    # Validation
    if not username or not email or not password:
        flash('All fields are required', 'error')
        return redirect(url_for('login'))
    
    if len(username) < 3:
        flash('Username must be at least 3 characters long', 'error')
        return redirect(url_for('login'))
    
    if len(password) < 6:
        flash('Password must be at least 6 characters long', 'error')
        return redirect(url_for('login'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already registered', 'error')
        return redirect(url_for('login'))
    
    if User.query.filter_by(username=username).first():
        flash('Username already taken', 'error')
        return redirect(url_for('login'))
    
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()
    
    login_user(user)
    return redirect(url_for('user_dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def user_dashboard():
    # Get user stats
    total_solved = Submission.query.filter_by(
        user_id=current_user.id, 
        status='Accepted'
    ).count()
    
    total_submissions = Submission.query.filter_by(user_id=current_user.id).count()
    accuracy = (total_solved / total_submissions * 100) if total_submissions > 0 else 0
    
    recent_submissions = Submission.query.filter_by(
        user_id=current_user.id
    ).options(joinedload(Submission.problem)).order_by(Submission.submitted_at.desc()).limit(5).all()
    
    # Get average quality score
    quality_reports = CodeQualityReport.query.join(Submission).filter(
        Submission.user_id == current_user.id
    ).all()
    
    avg_quality = sum([r.overall_score for r in quality_reports]) / len(quality_reports) if quality_reports else 0
    
    return render_template('userdashboard.html', 
                         user=current_user,
                         total_solved=total_solved,
                         accuracy=round(accuracy, 1),
                         recent_submissions=recent_submissions,
                         avg_quality=round(avg_quality, 1) if quality_reports else 0)

@app.route('/problems')
@login_required
def problem_library():
    problems = Problem.query.all()
    return render_template('problemLibrary.html', problems=problems)

@app.route('/solve/<int:problem_id>', methods=['GET', 'POST'])
@login_required
def solve_problem(problem_id):
    problem = Problem.query.get_or_404(problem_id)
    
    if request.method == 'POST':
        code = request.form.get('code')
        language = request.form.get('language', 'python')
        
        if not code:
            return jsonify({'error': 'Code is required'}), 400
        
        # Get test cases
        test_cases = TestCase.query.filter_by(problem_id=problem_id).all()
        
        if not test_cases:
            return jsonify({'error': 'No test cases found for this problem'}), 400
        
        # Run test cases
        passed = 0
        total = len(test_cases)
        execution_time = 0
        status = 'Wrong Answer'
        error_message = ''
        failed_test_case = None
        results = []
        
        for idx, test_case in enumerate(test_cases):
            success, output, error, exec_time = execute_code(
                code, language, test_case.input_data
            )
            execution_time += exec_time
            
            # Normalize for comparison
            actual = output.strip() if success else error.strip()
            expected = test_case.expected_output.strip()
            
            is_passed = False
            if success and actual == expected:
                is_passed = True
                passed += 1
            else:
                if not status or status == 'Accepted':
                    status = 'Runtime Error' if not success else 'Wrong Answer'
                    if not failed_test_case:
                        failed_test_case = idx + 1
                        error_message = f'Test case {idx + 1} failed. Expected: {expected}, Got: {actual}'

            results.append({
                'input': test_case.input_data,
                'expected': expected,
                'output': actual,
                'passed': is_passed
            })
        
        # Determine final status
        if passed == total:
            status = 'Accepted'
            error_message = ''  # Clear error message on success
        
        # Determine final status string differently if needed, keeping 'Accepted' logic
        
        # Create submission record
        submission = Submission(
            user_id=current_user.id,
            problem_id=problem_id,
            code=code,
            language=language,
            status=status,
            test_cases_passed=passed,
            total_test_cases=total,
            execution_time=execution_time / total if total > 0 else 0
        )
        db.session.add(submission)
        db.session.commit()
        
        # Analyze code quality using Gemini or Local Engine (handled by analyze_code_quality)
        quality_data = analyze_code_quality(code, language, problem.title)
        
        # Create quality report
        quality_report = CodeQualityReport(
            submission_id=submission.id,
            overall_score=quality_data.get('overall_score', 70),
            readability_score=quality_data.get('readability_score', 70),
            maintainability_score=quality_data.get('maintainability_score', 70),
            efficiency_score=quality_data.get('efficiency_score', 70),
            best_practices_score=quality_data.get('best_practices_score', 70),
            time_complexity=quality_data.get('time_complexity', 'O(n)'),
            space_complexity=quality_data.get('space_complexity', 'O(1)'),
            suggestions=json.dumps(quality_data.get('suggestions', [])),
            detailed_feedback=quality_data.get('detailed_feedback', '')
        )
        db.session.add(quality_report)
        db.session.commit()
        
        # Return results as JSON for AJAX
        try:
            return jsonify({
                'status': status,
                'test_cases_passed': passed,
                'total_test_cases': total,
                'execution_time': round(execution_time / total, 3) if total > 0 else 0,
                'error': error_message,
                'results': results, # Detailed results for each test case
                'quality_report': {
                    'overall_score': float(quality_report.overall_score) if quality_report.overall_score else 70.0,
                    'readability_score': float(quality_report.readability_score) if quality_report.readability_score else 70.0,
                    'maintainability_score': float(quality_report.maintainability_score) if quality_report.maintainability_score else 70.0,
                    'efficiency_score': float(quality_report.efficiency_score) if quality_report.efficiency_score else 70.0,
                    'best_practices_score': float(quality_report.best_practices_score) if quality_report.best_practices_score else 70.0,
                    'time_complexity': quality_report.time_complexity or 'O(n)',
                    'space_complexity': quality_report.space_complexity or 'O(1)',
                    'suggestions': json.loads(quality_report.suggestions) if quality_report.suggestions else [],
                    'detailed_feedback': quality_report.detailed_feedback or 'No detailed feedback available.',
                    'coding_habits': quality_data.get('coding_habits_to_improve', []),
                    'raw_metrics': quality_data.get('raw_metrics', {})
                }
            })
        except Exception as e:
            print(f"Error creating JSON response: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'status': status,
                'test_cases_passed': passed,
                'total_test_cases': total,
                'execution_time': round(execution_time / total, 3) if total > 0 else 0,
                'error': error_message,
                'results': results,
                'quality_report': {
                    'overall_score': 70.0,
                    'readability_score': 70.0,
                    'maintainability_score': 70.0,
                    'efficiency_score': 70.0,
                    'best_practices_score': 70.0,
                    'time_complexity': 'O(n)',
                    'space_complexity': 'O(1)',
                    'suggestions': [],
                    'detailed_feedback': 'Error generating quality report.',
                    'coding_habits': [],
                    'raw_metrics': {}
                }
            }), 500
    
    return render_template('problemsolver.html', problem=problem)

# Admin Routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('user_dashboard'))
    
    total_problems = Problem.query.count()
    total_users = User.query.count()
    total_submissions = Submission.query.count()
    
    return render_template('admindashboard.html',
                         total_problems=total_problems,
                         total_users=total_users,
                         total_submissions=total_submissions)

@app.route('/admin/problems/add', methods=['GET', 'POST'])
@login_required
def add_problem():
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        difficulty = request.form.get('difficulty', '').strip()
        category = request.form.get('category', '').strip()
        
        # Validation
        if not title or not description or not difficulty or not category:
            flash('All fields are required', 'error')
            return render_template('addnewproblem.html')
        
        if difficulty not in ['Easy', 'Medium', 'Hard']:
            flash('Invalid difficulty level', 'error')
            return render_template('addnewproblem.html')
        
        problem = Problem(
            title=title,
            description=description,
            difficulty=difficulty,
            category=category
        )
        db.session.add(problem)
        db.session.commit()
        
        flash('Problem added successfully!', 'success')
        return redirect(url_for('manage_testcases', problem_id=problem.id))
    
    return render_template('addnewproblem.html')

@app.route('/admin/problems/<int:problem_id>/testcases', methods=['GET', 'POST'])
@login_required
def manage_testcases(problem_id):
    if not current_user.is_admin:
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('user_dashboard'))
    
    problem = Problem.query.get_or_404(problem_id)
    
    if request.method == 'POST':
        input_data = request.form.get('input_data', '').strip()
        expected_output = request.form.get('expected_output', '').strip()
        is_hidden = request.form.get('is_hidden') == 'on'
        
        # Validation
        if not input_data or not expected_output:
            flash('Both input and expected output are required', 'error')
            test_cases = TestCase.query.filter_by(problem_id=problem_id).all()
            return render_template('adminmanagetestcases.html', problem=problem, test_cases=test_cases)
        
        test_case = TestCase(
            problem_id=problem_id,
            input_data=input_data,
            expected_output=expected_output,
            is_hidden=is_hidden
        )
        db.session.add(test_case)
        db.session.commit()
        
        flash('Test case added successfully!', 'success')
        return redirect(url_for('manage_testcases', problem_id=problem_id))
    
    test_cases = TestCase.query.filter_by(problem_id=problem_id).all()
    return render_template('adminmanagetestcases.html', problem=problem, test_cases=test_cases)

# Database Initialization
def init_db():
    """Initialize the database with tables"""
    with app.app_context():
        # Drop all tables to reset (As per user request: "remove all problems from database")
        # WARNING: This deletes all data!
        # db.drop_all() # Commented out to stabilize problem IDs
        db.create_all()
        print("Database initialized (Reset)!")
        
        # Create a default admin user (password: admin123)
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@codesphere.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created!")
            
        # Seed "Find Missing Numbers" problem
        if not Problem.query.filter_by(title="Find Missing Numbers").first():
            print("Seeding 'Find Missing Numbers' problem...")
            problem = Problem(
                title="Find Missing Numbers",
                description="You are given an array of integers where each number is in the range [1, n]. Some numbers appear twice and others appear once. Return all numbers in the range [1, n] that do not appear in the array.\n\nExample:\nInput: 4 3 2 7 8 2 3 1\nOutput: 5 6",
                difficulty="Medium",
                category="Arrays"
            )
            db.session.add(problem)
            db.session.commit()
            
            # Add test cases for it
            test_cases = [
                {"input": "4 3 2 7 8 2 3 1", "expected": "5 6"},
                {"input": "1 1", "expected": "2"}
            ]
            
            for tc in test_cases:
                test_case = TestCase(
                    problem_id=problem.id,
                    input_data=tc['input'],
                    expected_output=tc['expected'],
                    is_hidden=False
                )
                db.session.add(test_case)
            db.session.commit()
            print("Problem seeded successfully!")
        else:
            print("Problem already exists, skipping seed.")


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)

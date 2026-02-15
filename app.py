from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import subprocess
import os
import json
import time
import uuid
from code_intelligence import CodeIntelligenceEngine

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Create temp directory if it doesn't exist
TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def cleanup_temp_files():
    """Remove all files in the temp directory on startup."""
    try:
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
        print("Temp directory cleaned up.")
    except Exception as e:
        print(f"Error cleaning temp directory: {e}")

# Clean up on startup
cleanup_temp_files()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/run', methods=['POST'])
def run_code():
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        # Load test cases and get test case 1
        testcases_path = os.path.join(os.path.dirname(__file__), 'testcases.json')
        try:
            with open(testcases_path, 'r', encoding='utf-8') as f:
                testcases = json.load(f)
        except FileNotFoundError:
            return jsonify({'error': 'testcases.json not found'}), 500
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid testcases.json format'}), 500
        
        if not testcases or len(testcases) == 0:
            return jsonify({'error': 'No test cases available'}), 500
        
        # Get first test case
        testcase = testcases[0]
        test_input = testcase.get('input', '')
        expected = testcase.get('expected', '').strip()
        
        # Generate unique filename
        filename = os.path.join(TEMP_DIR, f'temp_{uuid.uuid4().hex}.py')
        
        # Write code to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(code)
        
        try:
            # Measure execution time
            start_time = time.time()
            
            # Execute code with test case 1 input
            result = subprocess.run(
                ['python', filename],
                input=test_input,
                capture_output=True,
                text=True,
                timeout=2,
                cwd=TEMP_DIR
            )
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Clean up file
            try:
                if os.path.exists(filename):
                     os.remove(filename)
            except Exception as e:
                print(f"Error deleting temp file {filename}: {e}")
            
            # Get actual output
            actual_output = result.stdout.strip() if result.stdout else ''
            
            # If there's stderr, it's a runtime error
            if result.stderr and result.stderr.strip():
                actual_output = result.stderr.strip()
                return jsonify({
                    'output': actual_output,
                    'expected': expected,
                    'execution_time': round(execution_time, 2),
                    'passed': False,
                    'error': True
                }), 200
            
            # Normalize expected output
            expected_normalized = expected.strip() if expected else ''
            
            # Compare outputs
            is_passed = (actual_output == expected_normalized)
            
            return jsonify({
                'output': actual_output if actual_output else '(no output)',
                'expected': expected_normalized,
                'execution_time': round(execution_time, 2),
                'passed': is_passed,
                'input': test_input
            }), 200
            
        except subprocess.TimeoutExpired:
            # Clean up file
            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except Exception as e:
                 print(f"Error deleting temp file {filename}: {e}")

            return jsonify({
                'error': 'Execution timeout (exceeded 2 seconds)',
                'expected': expected,
                'output': 'Timeout',
                'execution_time': 2000,
                'passed': False
            }), 200
            
        except Exception as e:
            # Clean up file
            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except Exception as e:
                 print(f"Error deleting temp file {filename}: {e}")

            return jsonify({
                'error': f'Runtime error: {str(e)}',
                'expected': expected,
                'output': f'Error: {str(e)}',
                'execution_time': 0,
                'passed': False
            }), 200
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


@app.route('/submit', methods=['POST'])
def submit_code():
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'No code provided'}), 400
        
        # Load test cases
        testcases_path = os.path.join(os.path.dirname(__file__), 'testcases.json')
        with open(testcases_path, 'r', encoding='utf-8') as f:
            testcases = json.load(f)
        
        # Generate unique filename
        filename = os.path.join(TEMP_DIR, f'submit_{uuid.uuid4().hex}.py')
        
        # Write code to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(code)
        
        results = []
        passed = 0
        total = len(testcases)
        total_start_time = time.time()
        runtime_error = False
        
        try:
            for testcase in testcases:
                test_input = testcase.get('input', '')
                expected = testcase.get('expected', '').strip()
                
                try:
                    # Execute code with test input
                    result = subprocess.run(
                        ['python', filename],
                        input=test_input,
                        capture_output=True,
                        text=True,
                        timeout=2,
                        cwd=TEMP_DIR
                    )
                    
                    # Get actual output from stdout (strip whitespace)
                    actual_output = result.stdout.strip() if result.stdout else ''
                    
                    # If there's stderr, it's a runtime error
                    if result.stderr and result.stderr.strip():
                        actual_output = result.stderr.strip()
                        results.append({
                            'input': test_input,
                            'expected': expected.strip(),
                            'output': actual_output,
                            'passed': False
                        })
                        runtime_error = True
                        break
                    
                    # Normalize expected output (strip whitespace)
                    expected_normalized = expected.strip() if expected else ''
                    
                    # Compare outputs exactly (both are already stripped)
                    is_passed = (actual_output == expected_normalized)
                    if is_passed:
                        passed += 1
                    
                    # Always return the actual user output (even if it doesn't match)
                    results.append({
                        'input': test_input,
                        'expected': expected_normalized,
                        'output': actual_output if actual_output else '(no output)',
                        'passed': is_passed
                    })
                    
                except subprocess.TimeoutExpired:
                    results.append({
                        'input': test_input,
                        'expected': expected,
                        'output': 'Timeout (exceeded 2 seconds)',
                        'passed': False
                    })
                    runtime_error = True
                    break
                    
                except Exception as e:
                    results.append({
                        'input': test_input,
                        'expected': expected,
                        'output': f'Error: {str(e)}',
                        'passed': False
                    })
                    runtime_error = True
                    break
            
            total_end_time = time.time()
            total_execution_time = (total_end_time - total_start_time) * 1000
            
            # Clean up file
            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except Exception as e:
                print(f"Error deleting temp file {filename}: {e}")
            
            # Analyze code quality using Code Intelligence Engine
            code_intelligence = None
            try:
                intelligence_engine = CodeIntelligenceEngine()
                code_intelligence = intelligence_engine.analyze(code)
            except Exception as e:
                # If analysis fails, continue without breaking submission
                code_intelligence = {
                    "success": False,
                    "error": f"Analysis error: {str(e)}",
                    "overall_quality_score": 0,
                    "maintainability_index": 0,
                    "suggestions": []
                }
            
            return jsonify({
                'passed': passed,
                'total': total,
                'execution_time': round(total_execution_time, 2),
                'results': results,
                'code_intelligence': code_intelligence
            }), 200
            
        except Exception as e:
            # Clean up file
            try:
                if os.path.exists(filename):
                     os.remove(filename)
            except Exception as e:
                 print(f"Error deleting temp file {filename}: {e}")
            # Analyze code quality even if execution failed
            code_intelligence = None
            try:
                intelligence_engine = CodeIntelligenceEngine()
                code_intelligence = intelligence_engine.analyze(code)
            except Exception:
                code_intelligence = {
                    "success": False,
                    "error": "Analysis unavailable",
                    "overall_quality_score": 0,
                    "maintainability_index": 0,
                    "suggestions": []
                }
            
            return jsonify({
                'error': f'Execution error: {str(e)}',
                'passed': 0,
                'total': total,
                'execution_time': 0,
                'results': results,
                'code_intelligence': code_intelligence
            }), 200
            
    except FileNotFoundError:
        return jsonify({'error': 'testcases.json not found'}), 500
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid testcases.json format'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)


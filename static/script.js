// Monaco Editor instance
let monacoEditor = null;

// Get DOM elements
const codeEditorContainer = document.getElementById('codeEditor');
const runBtn = document.getElementById('runBtn');
const submitBtn = document.getElementById('submitBtn');
const runOutput = document.getElementById('runOutput');
const runOutputContent = document.getElementById('runOutputContent');
const runExecutionTime = document.getElementById('runExecutionTime');
const submitResults = document.getElementById('submitResults');
const passedCount = document.getElementById('passedCount');
const totalCount = document.getElementById('totalCount');
const totalExecutionTime = document.getElementById('totalExecutionTime');
const testCasesTable = document.getElementById('testCasesTable');
const errorMessage = document.getElementById('errorMessage');

// Initialize Monaco Editor
function initializeMonaco() {
    if (typeof require === 'undefined') {
        console.error('Monaco Editor loader not found. Please check if the script is loaded correctly.');
        showError('Failed to load code editor. Please refresh the page.');
        return;
    }

    require.config({ paths: { vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs' } });
    require(['vs/editor/editor.main'], function () {
        const defaultCode = `# Write your solution here
# Example solution:
nums = list(map(int, input().split()))
n = len(nums)
present = set(nums)
missing = []
for i in range(1, n + 1):
    if i not in present:
        missing.append(i)
print(' '.join(map(str, missing)))`;

        try {
            monacoEditor = monaco.editor.create(codeEditorContainer, {
                value: defaultCode,
                language: 'python',
                theme: 'vs-dark',
                automaticLayout: true,
                fontSize: 14,
                minimap: { enabled: true },
                scrollBeyondLastLine: false,
                wordWrap: 'on',
                lineNumbers: 'on',
                roundedSelection: false,
                readOnly: false,
                cursorStyle: 'line',
                formatOnPaste: true,
                formatOnType: true
            });

            // Handle window resize
            window.addEventListener('resize', () => {
                if (monacoEditor) {
                    monacoEditor.layout();
                }
            });

            console.log('Monaco Editor initialized successfully');
        } catch (error) {
            console.error('Error creating Monaco editor:', error);
            showError('Failed to initialize code editor. Please refresh the page.');
        }
    });
}

// Wait for DOM and Monaco loader to be ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeMonaco);
} else {
    // DOM is already ready, but wait a bit for Monaco loader
    setTimeout(initializeMonaco, 100);
}

// Get code from Monaco editor
function getCode() {
    if (monacoEditor) {
        return monacoEditor.getValue();
    }
    return '';
}

// Hide error message
function hideError() {
    errorMessage.style.display = 'none';
    errorMessage.textContent = '';
}

// Show error message
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

// Set loading state
function setLoading(isLoading) {
    runBtn.disabled = isLoading;
    submitBtn.disabled = isLoading;
    if (isLoading) {
        document.body.classList.add('loading');
    } else {
        document.body.classList.remove('loading');
    }
}

// Handle Run button click
runBtn.addEventListener('click', async () => {
    hideError();
    const code = getCode().trim();

    if (!code) {
        showError('Please write some code first!');
        return;
    }

    setLoading(true);
    runOutput.style.display = 'none';

    try {
        const response = await fetch('/run', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                code: code
            })
        });

        const data = await response.json();

        // Update test case information
        const runInput = document.getElementById('runInput');
        const runExpected = document.getElementById('runExpected');
        const runOutputContent = document.getElementById('runOutputContent');
        const runStatus = document.getElementById('runStatus');

        if (data.error && !data.passed) {
            // Runtime error or timeout
            runInput.textContent = data.input || 'N/A';
            runExpected.textContent = data.expected || 'N/A';
            runOutputContent.textContent = data.output || data.error || 'Error';
            runOutputContent.className = 'value output-failed';
            runStatus.textContent = 'FAILED';
            runStatus.className = 'value status-failed';
        } else {
            // Normal execution
            runInput.textContent = data.input || 'N/A';
            runExpected.textContent = data.expected || 'N/A';
            runOutputContent.textContent = data.output || '(no output)';
            
            if (data.passed) {
                runOutputContent.className = 'value';
                runStatus.textContent = 'PASSED';
                runStatus.className = 'value status-passed';
            } else {
                runOutputContent.className = 'value output-failed';
                runStatus.textContent = 'FAILED';
                runStatus.className = 'value status-failed';
            }
        }

        runExecutionTime.textContent = `Execution Time: ${data.execution_time || 0} ms`;
        runOutput.style.display = 'block';
    } catch (error) {
        showError('Failed to execute code: ' + error.message);
    } finally {
        setLoading(false);
    }
});

// Handle Submit button click
submitBtn.addEventListener('click', async () => {
    hideError();
    const code = getCode().trim();

    if (!code) {
        showError('Please write some code first!');
        return;
    }

    setLoading(true);
    submitResults.style.display = 'none';

    try {
        const response = await fetch('/submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                code: code
            })
        });

        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        // Update summary
        passedCount.textContent = data.passed || 0;
        totalCount.textContent = data.total || 0;
        totalExecutionTime.textContent = data.execution_time || 0;

        // Update test cases table
        if (data.results && data.results.length > 0) {
            let tableHTML = `
                <table>
                    <thead>
                        <tr>
                            <th>Test Case</th>
                            <th>Input</th>
                            <th>Expected</th>
                            <th>Output</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            data.results.forEach((result, index) => {
                const status = result.passed ? 'PASSED' : 'FAILED';
                const statusClass = result.passed ? 'status-passed' : 'status-failed';
                const outputClass = result.passed ? '' : 'output-failed';
                const outputDisplay = result.output || '(no output)';
                
                tableHTML += `
                    <tr>
                        <td>#${index + 1}</td>
                        <td>${escapeHtml(result.input || '')}</td>
                        <td>${escapeHtml(result.expected || '')}</td>
                        <td class="${outputClass}">${escapeHtml(outputDisplay)}</td>
                        <td class="${statusClass}">${status}</td>
                    </tr>
                `;
            });

            tableHTML += `
                    </tbody>
                </table>
            `;

            testCasesTable.innerHTML = tableHTML;
        } else {
            testCasesTable.innerHTML = '<p>No test cases to display.</p>';
        }

        submitResults.style.display = 'block';
    } catch (error) {
        showError('Failed to submit code: ' + error.message);
    } finally {
        setLoading(false);
    }
});

// Helper function to escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


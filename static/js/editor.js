/**
 * Monaco Editor Integration for CodeSphere
 * Handles Monaco Editor initialization, language switching, and code retrieval
 */

let editor = null;
let isEditorReady = false;

// Language mapping
const languageMap = {
    'python': 'python',
    'cpp': 'cpp',
    'java': 'java'
};

// Default code templates
const defaultCode = {
    'python': `def solve():
    # Your code here
    pass`,
    'cpp': `#include <iostream>
#include <vector>
using namespace std;

int main() {
    // Your code here
    return 0;
}`,
    'java': `public class Solution {
    public static void main(String[] args) {
        // Your code here
    }
}`
};

/**
 * Initialize Monaco Editor
 */
function initMonacoEditor() {
    // Check if Monaco is already loaded
    if (typeof monaco === 'undefined') {
        console.error('Monaco Editor not loaded. Please check CDN link.');
        showEditorFallback();
        return;
    }

    const editorContainer = document.getElementById('editor');
    if (!editorContainer) {
        console.error('Editor container not found');
        return;
    }

    try {
        // Determine theme based on dark mode
        const isDark = document.documentElement.classList.contains('dark');
        const theme = isDark ? 'vs-dark' : 'vs';

        // Get initial language
        const languageSelect = document.getElementById('language');
        const initialLanguage = languageSelect ? languageSelect.value : 'python';
        const monacoLanguage = languageMap[initialLanguage] || 'python';

        // Create editor instance
        editor = monaco.editor.create(editorContainer, {
            value: defaultCode[initialLanguage] || defaultCode['python'],
            language: monacoLanguage,
            theme: theme,
            automaticLayout: true,
            minimap: {
                enabled: window.innerWidth > 768 // Disable minimap on mobile
            },
            fontSize: 14,
            lineNumbers: 'on',
            roundedSelection: false,
            scrollBeyondLastLine: false,
            readOnly: false,
            cursorStyle: 'line',
            wordWrap: 'on',
            formatOnPaste: true,
            formatOnType: true,
            tabSize: 4,
            insertSpaces: true,
            autoIndent: 'full',
            suggestOnTriggerCharacters: true,
            quickSuggestions: {
                other: true,
                comments: true,
                strings: true
            },
            acceptSuggestionOnEnter: 'on',
            tabCompletion: 'on',
            wordBasedSuggestions: 'matchingDocuments',
            renderWhitespace: 'selection',
            matchBrackets: 'always',
            folding: true,
            foldingStrategy: 'indentation'
        });

        isEditorReady = true;

        // Handle window resize with debounce (only add once)
        if (!window._monacoResizeHandler) {
            let resizeTimeout;
            window._monacoResizeHandler = () => {
                clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(() => {
                    if (editor) {
                        editor.layout();
                        // Update minimap based on screen size
                        const isMobile = window.innerWidth <= 768;
                        editor.updateOptions({
                            minimap: { enabled: !isMobile }
                        });
                    }
                }, 100);
            };
            window.addEventListener('resize', window._monacoResizeHandler);
        }

        // Handle theme changes
        const observer = new MutationObserver(() => {
            if (editor) {
                const isDark = document.documentElement.classList.contains('dark');
                monaco.editor.setTheme(isDark ? 'vs-dark' : 'vs');
            }
        });

        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['class']
        });

        console.log('Monaco Editor initialized successfully');
    } catch (error) {
        console.error('Error initializing Monaco Editor:', error);
        showEditorFallback();
    }
}

/**
 * Change editor language
 */
function changeEditorLanguage(language) {
    if (!editor || !isEditorReady) {
        return;
    }

    const monacoLanguage = languageMap[language] || 'python';
    
    // Get current code
    const currentCode = editor.getValue();
    
    // If editor is empty or has default code, set new default
    const isDefaultCode = Object.values(defaultCode).some(code => 
        currentCode.trim() === code.trim()
    );
    
    if (isDefaultCode || !currentCode.trim()) {
        editor.setValue(defaultCode[language] || defaultCode['python']);
    }
    
    // Change language
    monaco.editor.setModelLanguage(editor.getModel(), monacoLanguage);
    
    console.log(`Language changed to: ${monacoLanguage}`);
}

/**
 * Get code from editor
 */
function getEditorCode() {
    if (!editor || !isEditorReady) {
        // Fallback to textarea if editor not available
        const textarea = document.getElementById('code');
        return textarea ? textarea.value : '';
    }
    return editor.getValue();
}

/**
 * Set code in editor
 */
function setEditorCode(code) {
    if (!editor || !isEditorReady) {
        const textarea = document.getElementById('code');
        if (textarea) {
            textarea.value = code;
        }
        return;
    }
    editor.setValue(code || '');
}

/**
 * Show fallback UI if Monaco fails to load
 */
function showEditorFallback() {
    const editorContainer = document.getElementById('editor');
    const textarea = document.getElementById('code');
    
    if (editorContainer && textarea) {
        // Hide Monaco container and show textarea
        editorContainer.style.display = 'none';
        textarea.classList.remove('hidden');
        textarea.style.display = 'block';
        
        // Show warning message (only if not already shown)
        if (!document.getElementById('monaco-fallback-warning')) {
            const warningDiv = document.createElement('div');
            warningDiv.id = 'monaco-fallback-warning';
            warningDiv.className = 'p-2 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg mb-2';
            warningDiv.innerHTML = '<p class="text-yellow-700 dark:text-yellow-300 text-xs">⚠️ Monaco Editor unavailable. Using basic text editor.</p>';
            
            // Insert warning before the editor container's parent or before textarea
            const parent = editorContainer.parentNode;
            if (parent) {
                parent.insertBefore(warningDiv, editorContainer);
            } else if (textarea.parentNode) {
                textarea.parentNode.insertBefore(warningDiv, textarea);
            }
        }
    }
}

/**
 * Resize editor dynamically
 */
function resizeEditor() {
    if (editor && isEditorReady) {
        editor.layout();
    }
}

// Export functions for use in other scripts
window.CodeEditor = {
    init: initMonacoEditor,
    changeLanguage: changeEditorLanguage,
    getCode: getEditorCode,
    setCode: setEditorCode,
    resize: resizeEditor,
    isReady: () => isEditorReady
};


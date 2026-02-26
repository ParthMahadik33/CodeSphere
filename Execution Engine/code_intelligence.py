"""
Code Intelligence Engine
Analyzes Python code using AST for structural analysis and quality metrics.
"""

import ast
import re
from typing import Dict, List, Any, Optional, Tuple


class CodeIntelligenceEngine:
    """Analyzes Python code structure and quality using AST."""
    
    def __init__(self):
        self.complexity_visitor = None
        self.structure_visitor = None
    
    def analyze(self, code: str) -> Dict[str, Any]:
        """
        Main entry point for code analysis.
        
        Args:
            code: Raw Python code string
            
        Returns:
            Dictionary containing all analysis results
        """
        if not code or not code.strip():
            return self._error_response("Empty code provided")
        
        try:
            # Parse code into AST
            tree = ast.parse(code)
        except SyntaxError as e:
            return self._error_response(f"Syntax error: {str(e)}")
        except Exception as e:
            return self._error_response(f"Parse error: {str(e)}")
        
        # Extract metrics
        structural_metrics = self._analyze_structure(tree, code)
        readability_metrics = self._analyze_readability(code)
        variable_metrics = self._analyze_variables(tree)
        
        # Compute scores
        scores = self._compute_scores(structural_metrics, readability_metrics, variable_metrics)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(
            structural_metrics, readability_metrics, variable_metrics, scores
        )
        
        return {
            "success": True,
            "readability": readability_metrics,
            "structural_complexity": structural_metrics,
            "variable_analysis": variable_metrics,
            "maintainability_index": scores["maintainability_index"],
            "overall_quality_score": scores["overall_quality_score"],
            "suggestions": suggestions,
            "metrics": {
                **structural_metrics,
                **readability_metrics,
                **variable_metrics
            }
        }
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """Return error response structure."""
        return {
            "success": False,
            "error": error_message,
            "readability": {},
            "structural_complexity": {},
            "variable_analysis": {},
            "maintainability_index": 0,
            "overall_quality_score": 0,
            "suggestions": []
        }
    
    def _analyze_structure(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Analyze code structure using AST."""
        visitor = StructureVisitor()
        visitor.visit(tree)
        
        # Count non-empty code lines (excluding comments)
        lines = code.splitlines()
        code_lines = 0
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                code_lines += 1
        
        return {
            "total_functions": visitor.function_count,
            "max_nesting_depth": visitor.max_nesting_depth,
            "max_loop_depth": visitor.max_loop_depth,
            "max_if_depth": visitor.max_if_depth,
            "total_branching_points": visitor.branching_points,
            "cyclomatic_complexity": visitor.cyclomatic_complexity,
            "return_statements": visitor.return_count,
            "deeply_nested_blocks": visitor.deep_nesting_count,
            "total_lines": len(lines),
            "code_lines": code_lines
        }
    
    def _analyze_readability(self, code: str) -> Dict[str, Any]:
        """Analyze code readability metrics."""
        lines = code.splitlines()
        non_empty_lines = [line for line in lines if line.strip()]
        total_lines = len(lines)
        non_empty_count = len(non_empty_lines)
        
        # Count comment lines
        comment_lines = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#') or (stripped.startswith('"""') or stripped.startswith("'''")):
                comment_lines += 1
        
        # Calculate average line length
        if non_empty_lines:
            avg_line_length = sum(len(line) for line in non_empty_lines) / len(non_empty_lines)
        else:
            avg_line_length = 0
        
        # Count long lines (> 80 characters)
        long_lines = sum(1 for line in non_empty_lines if len(line) > 80)
        very_long_lines = sum(1 for line in non_empty_lines if len(line) > 120)
        
        # Comment ratio
        comment_ratio = (comment_lines / non_empty_count * 100) if non_empty_count > 0 else 0
        
        return {
            "total_lines": total_lines,
            "non_empty_lines": non_empty_count,
            "comment_lines": comment_lines,
            "comment_ratio": round(comment_ratio, 2),
            "average_line_length": round(avg_line_length, 1),
            "long_lines_count": long_lines,
            "very_long_lines_count": very_long_lines
        }
    
    def _analyze_variables(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze variable naming quality."""
        visitor = VariableVisitor()
        visitor.visit(tree)
        
        total_vars = len(visitor.variable_names)
        short_vars = sum(1 for name in visitor.variable_names if len(name) <= 2)
        weak_names = sum(1 for name in visitor.variable_names if self._is_weak_name(name))
        meaningful_names = total_vars - weak_names
        
        meaningful_ratio = (meaningful_names / total_vars * 100) if total_vars > 0 else 100
        
        return {
            "total_variables": total_vars,
            "short_variable_names": short_vars,
            "weak_variable_names": weak_names,
            "meaningful_variable_names": meaningful_names,
            "meaningful_naming_ratio": round(meaningful_ratio, 2),
            "variable_names": list(visitor.variable_names)[:20]  # Limit for response size
        }
    
    def _is_weak_name(self, name: str) -> bool:
        """Check if variable name is weak/non-descriptive."""
        # Common weak patterns
        weak_patterns = [
            r'^[a-z]$',  # Single letter
            r'^[a-z]{1,2}$',  # Very short
            r'^(tmp|temp|var|val|data|obj|item|elem|x|y|z|i|j|k)$',  # Generic names
            r'^[a-z]+\d+$'  # name123 pattern (often weak)
        ]
        
        for pattern in weak_patterns:
            if re.match(pattern, name.lower()):
                return True
        
        # Check if too short and not a common exception
        if len(name) <= 2 and name.lower() not in ['id', 'ok', 'no', 'pi', 'e']:
            return True
        
        return False
    
    def _compute_scores(self, structural: Dict, readability: Dict, variables: Dict) -> Dict[str, float]:
        """Compute dynamic scores based on measured metrics."""
        
        # Readability Score (0-100)
        readability_score = self._score_readability(readability)
        
        # Structural Score (0-100) - lower complexity = higher score
        structural_score = self._score_structure(structural)
        
        # Variable Naming Score (0-100)
        naming_score = self._score_naming(variables)
        
        # Maintainability Index (0-100)
        # Based on complexity, readability, and structure
        maintainability = (
            readability_score * 0.3 +
            structural_score * 0.4 +
            naming_score * 0.3
        )
        
        # Overall Quality Score (weighted combination)
        overall = (
            readability_score * 0.25 +
            structural_score * 0.35 +
            naming_score * 0.20 +
            maintainability * 0.20
        )
        
        return {
            "readability_score": round(readability_score, 2),
            "structural_score": round(structural_score, 2),
            "naming_score": round(naming_score, 2),
            "maintainability_index": round(maintainability, 2),
            "overall_quality_score": round(overall, 2)
        }
    
    def _score_readability(self, metrics: Dict) -> float:
        """Score readability based on metrics."""
        score = 100.0
        
        # Penalize low comment ratio
        if metrics["comment_ratio"] < 5:
            score -= 20
        elif metrics["comment_ratio"] < 10:
            score -= 10
        
        # Penalize very long lines
        if metrics["very_long_lines_count"] > 0:
            score -= min(15, metrics["very_long_lines_count"] * 2)
        
        if metrics["long_lines_count"] > metrics["non_empty_lines"] * 0.3:
            score -= 10
        
        # Penalize very long average line length
        if metrics["average_line_length"] > 100:
            score -= 15
        elif metrics["average_line_length"] > 80:
            score -= 5
        
        return max(0, min(100, score))
    
    def _score_structure(self, metrics: Dict) -> float:
        """Score structural quality based on complexity."""
        score = 100.0
        
        # Penalize high cyclomatic complexity
        complexity = metrics["cyclomatic_complexity"]
        if complexity > 20:
            score -= 30
        elif complexity > 15:
            score -= 20
        elif complexity > 10:
            score -= 10
        elif complexity > 5:
            score -= 5
        
        # Penalize deep nesting
        if metrics["max_nesting_depth"] > 5:
            score -= 25
        elif metrics["max_nesting_depth"] > 4:
            score -= 15
        elif metrics["max_nesting_depth"] > 3:
            score -= 8
        
        # Penalize too many branching points
        if metrics["total_branching_points"] > 15:
            score -= 15
        elif metrics["total_branching_points"] > 10:
            score -= 8
        
        # Penalize deeply nested blocks
        if metrics["deeply_nested_blocks"] > 3:
            score -= 10
        
        return max(0, min(100, score))
    
    def _score_naming(self, metrics: Dict) -> float:
        """Score variable naming quality."""
        if metrics["total_variables"] == 0:
            return 100.0
        
        meaningful_ratio = metrics["meaningful_naming_ratio"]
        score = meaningful_ratio
        
        # Additional penalty for very short names
        if metrics["short_variable_names"] > metrics["total_variables"] * 0.3:
            score -= 10
        
        return max(0, min(100, score))
    
    def _generate_suggestions(self, structural: Dict, readability: Dict, 
                            variables: Dict, scores: Dict) -> List[str]:
        """Generate improvement suggestions based on metrics."""
        suggestions = []
        
        # Structural suggestions
        if structural["cyclomatic_complexity"] > 10:
            suggestions.append(
                f"High cyclomatic complexity ({structural['cyclomatic_complexity']}). "
                "Consider breaking down complex functions into smaller, focused functions."
            )
        
        if structural["max_nesting_depth"] > 4:
            suggestions.append(
                f"Deep nesting detected (depth: {structural['max_nesting_depth']}). "
                "Consider using early returns or extracting nested logic into separate functions."
            )
        
        if structural["deeply_nested_blocks"] > 2:
            suggestions.append(
                f"Multiple deeply nested blocks detected ({structural['deeply_nested_blocks']}). "
                "Refactor to reduce nesting levels for better readability."
            )
        
        # Readability suggestions
        if readability["comment_ratio"] < 5:
            suggestions.append(
                f"Low comment density ({readability['comment_ratio']:.1f}%). "
                "Add comments to explain complex logic and improve code documentation."
            )
        
        if readability["very_long_lines_count"] > 0:
            suggestions.append(
                f"Found {readability['very_long_lines_count']} very long line(s) (>120 chars). "
                "Break long lines to improve readability."
            )
        
        if readability["average_line_length"] > 100:
            suggestions.append(
                f"Average line length is high ({readability['average_line_length']:.1f} chars). "
                "Consider breaking long lines into multiple shorter lines."
            )
        
        # Variable naming suggestions
        if variables["meaningful_naming_ratio"] < 70:
            suggestions.append(
                f"Variable naming could be improved ({variables['meaningful_naming_ratio']:.1f}% meaningful). "
                "Use descriptive variable names that clearly indicate purpose."
            )
        
        if variables["short_variable_names"] > variables["total_variables"] * 0.3:
            suggestions.append(
                f"Many short variable names detected ({variables['short_variable_names']}). "
                "Use more descriptive names instead of single-letter or very short names."
            )
        
        # Positive feedback
        if scores["overall_quality_score"] > 80:
            suggestions.append("Code quality is good! Keep up the excellent work.")
        elif scores["overall_quality_score"] > 60:
            suggestions.append("Code quality is decent. Consider the suggestions above for improvement.")
        
        return suggestions if suggestions else ["No specific suggestions. Code structure looks reasonable."]


class StructureVisitor(ast.NodeVisitor):
    """AST visitor for structural analysis."""
    
    def __init__(self):
        self.function_count = 0
        self.max_nesting_depth = 0
        self.max_loop_depth = 0
        self.max_if_depth = 0
        self.branching_points = 0
        self.cyclomatic_complexity = 1  # Base complexity
        self.return_count = 0
        self.deep_nesting_count = 0
        self._current_depth = 0
        self._loop_depth = 0
        self._if_depth = 0
    
    def visit_FunctionDef(self, node):
        """Visit function definitions."""
        self.function_count += 1
        self._current_depth += 1
        self.generic_visit(node)
        self._current_depth -= 1
    
    def visit_For(self, node):
        """Visit for loops."""
        self._loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self._loop_depth)
        self.branching_points += 1
        self.cyclomatic_complexity += 1
        
        if self._current_depth > 4:
            self.deep_nesting_count += 1
        
        self._current_depth += 1
        self.generic_visit(node)
        self._current_depth -= 1
        self._loop_depth -= 1
    
    def visit_While(self, node):
        """Visit while loops."""
        self._loop_depth += 1
        self.max_loop_depth = max(self.max_loop_depth, self._loop_depth)
        self.branching_points += 1
        self.cyclomatic_complexity += 1
        
        if self._current_depth > 4:
            self.deep_nesting_count += 1
        
        self._current_depth += 1
        self.generic_visit(node)
        self._current_depth -= 1
        self._loop_depth -= 1
    
    def visit_If(self, node):
        """Visit if statements."""
        self._if_depth += 1
        self.max_if_depth = max(self.max_if_depth, self._if_depth)
        self.branching_points += 1
        self.cyclomatic_complexity += 1
        
        if self._current_depth > 4:
            self.deep_nesting_count += 1
        
        self._current_depth += 1
        self.generic_visit(node)
        self._current_depth -= 1
        self._if_depth -= 1
        
        # Visit else/elif
        for child in node.orelse:
            if isinstance(child, ast.If):
                self.visit_If(child)
            else:
                self.visit(child)
    
    def visit_Return(self, node):
        """Visit return statements."""
        self.return_count += 1
        self.generic_visit(node)
    
    def visit(self, node):
        """Override visit to track depth."""
        self.max_nesting_depth = max(self.max_nesting_depth, self._current_depth)
        return super().visit(node)


class VariableVisitor(ast.NodeVisitor):
    """AST visitor for variable name analysis."""
    
    def __init__(self):
        self.variable_names = set()
    
    def visit_Name(self, node):
        """Visit variable names."""
        # Only count variables being assigned (Store context)
        if isinstance(node.ctx, ast.Store):
            self.variable_names.add(node.id)
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Visit function parameters."""
        for arg in node.args.args:
            self.variable_names.add(arg.arg)
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Visit assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variable_names.add(target.id)
            elif isinstance(target, ast.Tuple):
                # Handle tuple unpacking: a, b = ...
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self.variable_names.add(elt.id)
        self.generic_visit(node)
    
    def visit_For(self, node):
        """Visit for loop targets."""
        if isinstance(node.target, ast.Name):
            self.variable_names.add(node.target.id)
        elif isinstance(node.target, ast.Tuple):
            for elt in node.target.elts:
                if isinstance(elt, ast.Name):
                    self.variable_names.add(elt.id)
        self.generic_visit(node)


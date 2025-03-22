from rapidfuzz import process, fuzz
from models.rule import Rule


class ColumnMatcher:
    """Service for matching CSV columns to validation rules using fuzzy matching."""
    
    def __init__(self, match_threshold=80):
        """
        Initialize the column matcher.
        
        Args:
            match_threshold (int): Threshold for fuzzy matching (0-100)
        """
        self.match_threshold = match_threshold
    
    def match_columns(self, column_names, active_only=True):
        """
        Match column names to validation rules using fuzzy matching.
        
        Args:
            column_names (list): List of column names from the CSV
            active_only (bool): If True, only match against active rules
            
        Returns:
            dict: Mapping of column names to matched rules
        """
        # Get all available rule column patterns
        query = Rule.query
        if active_only:
            query = query.filter_by(is_active=True)
        
        rules = query.order_by(Rule.priority.desc()).all()
        rule_patterns = {rule.id: rule.column_pattern for rule in rules}
        
        # Match each column to the best rule
        column_rule_map = {}
        
        for column in column_names:
            # Find the best match for this column
            matches = process.extract(
                column,
                rule_patterns.values(),
                scorer=fuzz.token_sort_ratio,
                limit=3
            )
            
            # Check if the best match is above our threshold
            if matches and matches[0][1] >= self.match_threshold:
                best_match_pattern = matches[0][0]
                # Find the rule ID for this pattern
                rule_id = next(
                    (rule_id for rule_id, pattern in rule_patterns.items() 
                     if pattern == best_match_pattern),
                    None
                )
                
                if rule_id:
                    rule = next((r for r in rules if r.id == rule_id), None)
                    column_rule_map[column] = {
                        'rule': rule,
                        'match_score': matches[0][1],
                        'alternative_matches': [
                            {'pattern': m[0], 'score': m[1]} 
                            for m in matches[1:] if m[1] >= self.match_threshold
                        ]
                    }
        
        return column_rule_map
    
    def suggest_rules(self, column_name, limit=5):
        """
        Suggest rules for a specific column name.
        
        Args:
            column_name (str): Column name to find suggestions for
            limit (int): Maximum number of suggestions
            
        Returns:
            list: List of rule suggestions with match scores
        """
        rules = Rule.query.filter_by(is_active=True).all()
        rule_patterns = {rule.id: rule.column_pattern for rule in rules}
        
        matches = process.extract(
            column_name,
            rule_patterns.values(),
            scorer=fuzz.token_sort_ratio,
            limit=limit
        )
        
        suggestions = []
        for match_pattern, score in matches:
            rule_id = next(
                (rule_id for rule_id, pattern in rule_patterns.items() 
                 if pattern == match_pattern),
                None
            )
            if rule_id:
                rule = next((r for r in rules if r.id == rule_id), None)
                suggestions.append({
                    'rule': rule,
                    'match_score': score
                })
        
        return suggestions
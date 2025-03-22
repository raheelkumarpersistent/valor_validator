import pandas as pd
import io
import os
from werkzeug.utils import secure_filename


class CSVProcessor:
    """Service for processing and analyzing CSV files using pandas."""
    
    def __init__(self, upload_folder):
        """
        Initialize the CSV processor.
        
        Args:
            upload_folder (str): Directory to save uploaded CSV files
        """
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
    
    def save_file(self, file_obj):
        """
        Save an uploaded file to disk.
        
        Args:
            file_obj: File-like object from request.files
            
        Returns:
            str: Path to saved file
        """
        filename = secure_filename(file_obj.filename)
        filepath = os.path.join(self.upload_folder, filename)
        file_obj.save(filepath)
        return filepath
    
    def read_csv(self, file_path_or_obj, preview_rows=5, sample_size=None):
        """
        Read a CSV file and return basic statistics and a preview.
        
        Args:
            file_path_or_obj: Path to CSV file or file-like object
            preview_rows (int): Number of rows to preview
            sample_size (int): Number of rows to sample for analysis (None for all)
            
        Returns:
            dict: Dictionary with file statistics and preview data
        """
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    # Read with low memory mode for large files
                    df = pd.read_csv(file_path_or_obj, encoding=encoding, low_memory=False)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # If all encodings fail
                raise ValueError("Could not determine file encoding")
            
            # Take a sample if specified
            if sample_size and len(df) > sample_size:
                df_sample = df.sample(sample_size, random_state=42)
            else:
                df_sample = df
            
            # Get column information
            columns = []
            for col in df.columns:
                col_info = {
                    'name': col,
                    'dtype': str(df[col].dtype),
                    'unique_values': df_sample[col].nunique(),
                    'missing_values': df_sample[col].isna().sum(),
                    'sample_values': df_sample[col].dropna().sample(min(5, df_sample[col].count())).tolist()
                }
                columns.append(col_info)
            
            return {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'column_names': df.columns.tolist(),
                'column_details': columns,
                'preview': df.head(preview_rows).to_dict(orient='records')
            }
        
        except Exception as e:
            raise ValueError(f"Error reading CSV: {str(e)}")
    
    def get_column_sample(self, file_path, column_name, sample_size=100):
        """
        Get a sample of values from a specific column.
        
        Args:
            file_path (str): Path to CSV file
            column_name (str): Name of the column
            sample_size (int): Number of samples to return
            
        Returns:
            list: Sample of values from the column
        """
        try:
            df = pd.read_csv(file_path, usecols=[column_name], low_memory=False)
            return df[column_name].dropna().sample(min(sample_size, len(df))).tolist()
        except Exception as e:
            raise ValueError(f"Error sampling column: {str(e)}")
    
    def validate_with_iterator(self, file_path, callback, batch_size=1000):
        """
        Process a CSV file in batches, calling a callback for each batch.
        Useful for large files where memory is a concern.
        
        Args:
            file_path (str): Path to CSV file
            callback (function): Function to call for each batch
            batch_size (int): Size of each batch
            
        Returns:
            dict: Summary of validation
        """
        total_rows = 0
        valid_rows = 0
        invalid_rows = 0
        
        # Use chunked iterator to process large files
        for chunk_index, chunk in enumerate(pd.read_csv(file_path, chunksize=batch_size)):
            chunk_results = callback(chunk, start_row=chunk_index * batch_size)
            
            total_rows += len(chunk)
            valid_rows += chunk_results.get('valid_rows', 0)
            invalid_rows += chunk_results.get('invalid_rows', 0)
        
        return {
            'total_rows': total_rows,
            'valid_rows': valid_rows,
            'invalid_rows': invalid_rows,
            'percent_valid': (valid_rows / total_rows * 100) if total_rows > 0 else 0
        }
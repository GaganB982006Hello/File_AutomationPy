import os
from PyPDF2 import PdfMerger

def merge_pdfs(files, output_filename):
    import tempfile
    
    try:
        merger = PdfMerger()
        
        # Sort files if possible, or trust the order they were uploaded
        # Flask request.files comes as a MultiDict, usually preserving order of selection
        # But robust robustness, we can try to sort by filename
        
        # We need to save files to disk for PdfMerger? 
        # Actually PdfMerger can take file-like objects!
        
        # Filter for PDFs
        pdf_files = [f for f in files if f.filename.lower().endswith('.pdf')]
        
        # Sort by filename
        pdf_files.sort(key=lambda x: x.filename)
        
        if not pdf_files:
            return None, "No PDF files uploaded."

        for pdf in pdf_files:
            merger.append(pdf)

        # Ensure output filename ends with .pdf
        if not output_filename.lower().endswith('.pdf'):
            output_filename += '.pdf'
            
        # Define output path
        output_dir = "/tmp" if os.path.exists("/tmp") else tempfile.gettempdir()
        output_path = os.path.join(output_dir, output_filename)
        
        merger.write(output_path)
        merger.close()
        
        return output_path, f"PDFs merged successfully!"
    except Exception as e:
        return None, f"Error: {str(e)}"

if __name__ == "__main__":
    pass

import re
import os
import sys

def split_novel_by_chapters(file_path):
    """
    Split a Chinese novel text file into individual chapter files.
    
    Args:
        file_path (str): Path to the input text file
    """
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found!")
        return
    
    # Get the base filename without extension for the output folder
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_folder = base_name
    
    # Create output directory
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")
    
    try:
        # Read the entire file
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Pattern to match chapter headers: 第X章 followed by chapter title
        # This pattern captures both the chapter number and title
        chapter_pattern = r'^第(\d+)章\s+(.+)$'
        
        # Split content by lines and find chapter starts
        lines = content.split('\n')
        chapters = []
        current_chapter = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # Check if this line is a chapter header
            match = re.match(chapter_pattern, line)
            
            if match:
                # Save previous chapter if exists
                if current_chapter is not None:
                    chapters.append({
                        'number': current_chapter['number'],
                        'title': current_chapter['title'],
                        'content': '\n'.join(current_content)
                    })
                
                # Start new chapter
                chapter_num = match.group(1)
                chapter_title = match.group(2).strip()
                current_chapter = {
                    'number': chapter_num,
                    'title': chapter_title
                }
                current_content = [line]  # Include the chapter header
                
            else:
                # Add line to current chapter content
                if current_chapter is not None:
                    current_content.append(line)
        
        # Don't forget the last chapter
        if current_chapter is not None:
            chapters.append({
                'number': current_chapter['number'],
                'title': current_chapter['title'],
                'content': '\n'.join(current_content)
            })
        
        # Write each chapter to a separate file
        for chapter in chapters:
            # Clean up title for filename (remove invalid characters)
            clean_title = re.sub(r'[<>:"/\\|?*]', '', chapter['title'])
            
            # Create filename: chapter number + title
            filename = f"第{chapter['number'].zfill(4)}章_{clean_title}.txt"
            filepath = os.path.join(output_folder, filename)
            
            # Write chapter content to file
            with open(filepath, 'w', encoding='utf-8') as chapter_file:
                chapter_file.write(chapter['content'])
            
            print(f"Created: {filename}")
        
        print(f"\nSuccessfully split {len(chapters)} chapters into '{output_folder}' folder!")
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")

def main():
    """
    Main function to handle command line arguments or prompt for input.
    """
    if len(sys.argv) > 1:
        # File path provided as command line argument
        file_path = sys.argv[1]
    else:
        # Prompt user for file path
        file_path = input("Enter the path to your novel text file: ").strip()
        
        # Remove quotes if user copied path with quotes
        if file_path.startswith('"') and file_path.endswith('"'):
            file_path = file_path[1:-1]
    
    split_novel_by_chapters(file_path)

if __name__ == "__main__":
    main()

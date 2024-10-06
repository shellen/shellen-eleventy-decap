import os
import shutil
import re
import yaml
from datetime import datetime
import argparse

def normalize_frontmatter(content):
    # Extract front matter
    front_matter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not front_matter_match:
        return content

    front_matter_str = front_matter_match.group(1)
    body = content[front_matter_match.end():]

    # Pre-process problematic fields
    front_matter_lines = front_matter_str.split('\n')
    in_excerpt = False
    excerpt_lines = []
    normalized_lines = []

    for line in front_matter_lines:
        if line.startswith('excerpt:'):
            in_excerpt = True
            excerpt_content = line.split(':', 1)[1].strip()
            if excerpt_content.startswith(('">-', '"|-', "'>-", "'|-")):
                excerpt_content = excerpt_content[3:].strip()
            excerpt_lines.append(excerpt_content.strip('"').strip("'"))
        elif in_excerpt and (line.strip().startswith('>-') or line.strip().startswith('|-')):
            continue
        elif in_excerpt and line.strip():
            excerpt_lines.append(line.strip().strip('"').strip("'"))
        else:
            if in_excerpt:
                in_excerpt = False
                excerpt = ' '.join(excerpt_lines).replace('"', '\\"').strip()
                normalized_lines.append(f'excerpt: "{excerpt}"')
                excerpt_lines = []
            normalized_lines.append(line)

    if excerpt_lines:
        excerpt = ' '.join(excerpt_lines).replace('"', '\\"').strip()
        normalized_lines.append(f'excerpt: "{excerpt}"')

    front_matter_str = '\n'.join(normalized_lines)

    try:
        front_matter = yaml.safe_load(front_matter_str)
    except yaml.YAMLError as e:
        print(f"YAML parsing error: {e}")
        return content

    # Rest of the function remains the same...

    # Normalize fields
    front_matter['layout'] = front_matter.get('layout', 'post')
    front_matter['author'] = front_matter.get('author', 'Jason Shellen')

    # Convert date to ISO format
    if 'date' in front_matter:
        date_str = str(front_matter['date'])
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S%z")
        except ValueError:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
            except ValueError:
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        print(f"Unable to parse date: {date_str}")
                        date_obj = datetime.now()
        front_matter['date'] = date_obj.strftime("%Y-%m-%dT%H:%M:%S%z")

    # Ensure tags are a list
    if 'tags' in front_matter:
        if isinstance(front_matter['tags'], str):
            front_matter['tags'] = [tag.strip() for tag in front_matter['tags'].split(',')]
        front_matter['tags'] = [tag for tag in front_matter['tags'] if tag]  # Remove empty tags

    # Remove unnecessary fields
    fields_to_remove = ['blogger_id', 'blogger_orig_url']
    for field in fields_to_remove:
        front_matter.pop(field, None)

    # Fix escaping issues
    for key, value in front_matter.items():
        if isinstance(value, str):
            # Remove unnecessary quotes and escape characters
            value = value.strip('"').strip("'")
            value = value.replace('\\"', '"')
            value = value.replace('\\n', '\n')
            front_matter[key] = value

    # Ensure boolean values are proper YAML booleans
    for key in ['featured', 'comments']:
        if key in front_matter:
            front_matter[key] = bool(front_matter[key])

    # Serialize front matter
    new_front_matter = yaml.dump(front_matter, default_flow_style=False, allow_unicode=True)

    # Combine new front matter with body
    return f"---\n{new_front_matter}---\n\n{body}"

def fix_escaping(content):
    # Fix double quotes
    content = re.sub(r'""([^"]+)""', r'"\1"', content)
    
    # Fix links
    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: f'[{m.group(1)}]({m.group(2).replace("+", "%20")})', content)
    
    # Remove unnecessary backslashes
    content = content.replace('\\"', '"')
    
    # Fix newline escaping
    content = content.replace('\\n', '\n')
    
    # Remove YAML block scalar indicators from the content
    content = re.sub(r'^(\s*)([|>]-?)\s*$', r'\1', content, flags=re.MULTILINE)
    
    return content

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Normalize front matter
    content = normalize_frontmatter(content)

    # Fix escaping issues
    content = fix_escaping(content)

    return content

def main(content_dir):
    if not os.path.isdir(content_dir):
        print(f"Error: The directory '{content_dir}' does not exist.")
        return

    backup_dir = os.path.join(content_dir, 'backup')
    try:
        os.makedirs(backup_dir, exist_ok=True)
    except OSError as e:
        print(f"Error: Unable to create backup directory. {e}")
        return

    for filename in os.listdir(content_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(content_dir, filename)
            backup_path = os.path.join(backup_dir, filename)

            try:
                # Backup original file
                shutil.copy2(file_path, backup_path)

                # Process and update file
                updated_content = process_file(file_path)

                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(updated_content)

                print(f"Processed and updated: {filename}")
            except IOError as e:
                print(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize Markdown files for Eleventy and Decap CMS")
    parser.add_argument("content_dir", help="Path to the content directory")
    args = parser.parse_args()

    main(args.content_dir)
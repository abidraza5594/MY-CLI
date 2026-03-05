"""
@ File Mention System

Resolves @mentions in user input to actual file paths.
When user types @auth, @component, @service etc., this module
finds matching files in the project and includes their context.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


# Common file category patterns
CATEGORY_PATTERNS = {
    "component": ["*component*", "*Component*", "*.component.*"],
    "service": ["*service*", "*Service*", "*.service.*"],
    "model": ["*model*", "*Model*", "*.model.*", "*schema*", "*entity*"],
    "util": ["*util*", "*utils*", "*helper*", "*helpers*"],
    "config": ["*config*", "*configuration*", "*.conf*", "*.env*", "*.json", "*.yaml", "*.yml", "*.toml"],
    "test": ["*test*", "*spec*", "*_test.*", "*.test.*", "*.spec.*"],
    "route": ["*route*", "*router*", "*routing*"],
    "guard": ["*guard*", "*middleware*", "*interceptor*"],
    "style": ["*.css", "*.scss", "*.sass", "*.less", "*.styled.*"],
    "hook": ["*hook*", "use*"],
    "store": ["*store*", "*redux*", "*ngrx*", "*state*", "*slice*", "*reducer*", "*action*"],
    "api": ["*api*", "*endpoint*", "*controller*"],
    "auth": ["*auth*", "*login*", "*register*", "*token*", "*jwt*", "*session*"],
    "type": ["*type*", "*types*", "*interface*", "*.d.ts"],
}

# File extensions to search
SEARCHABLE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte",
    ".java", ".kt", ".go", ".rs", ".rb", ".php", ".cs",
    ".html", ".css", ".scss", ".sass", ".less",
    ".json", ".yaml", ".yml", ".toml", ".xml",
    ".md", ".txt", ".sh", ".bat", ".ps1",
    ".sql", ".graphql", ".proto",
}

# Directories to skip
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "coverage",
    ".idea", ".vscode", "vendor", "target",
}


def extract_mentions(text: str) -> List[str]:
    """Extract @mentions from user input text.
    
    Matches patterns like @auth, @component, @src/utils, @package.json
    """
    # Match @ followed by word chars, dots, slashes, hyphens
    pattern = r'@([\w./\-]+)'
    matches = re.findall(pattern, text)
    return matches


def find_matching_files(mention: str, cwd: Path, max_results: int = 20) -> List[Path]:
    """Find files matching a @mention.
    
    Strategy:
    1. Check if it's a known category (component, service, etc.)
    2. Check if it's an exact file path
    3. Search for files containing the mention in their name
    """
    results = []
    mention_lower = mention.lower()
    
    # Strategy 1: Check if it's a known category
    if mention_lower in CATEGORY_PATTERNS:
        patterns = CATEGORY_PATTERNS[mention_lower]
        results = _search_by_patterns(cwd, patterns, max_results)
        if results:
            return results
    
    # Strategy 2: Check if it's an exact file path
    exact_path = cwd / mention
    if exact_path.exists() and exact_path.is_file():
        return [exact_path]
    
    # Strategy 3: Search for files containing the mention in their name
    results = _search_by_name(cwd, mention_lower, max_results)
    
    return results


def _search_by_patterns(cwd: Path, patterns: List[str], max_results: int) -> List[Path]:
    """Search for files matching glob patterns."""
    results = []
    
    for pattern in patterns:
        try:
            for match in cwd.rglob(pattern):
                if match.is_file() and _should_include(match, cwd):
                    if match not in results:
                        results.append(match)
                        if len(results) >= max_results:
                            return results
        except (PermissionError, OSError):
            continue
    
    return results


def _search_by_name(cwd: Path, name: str, max_results: int) -> List[Path]:
    """Search for files containing the name in their path."""
    results = []
    
    try:
        for root, dirs, files in os.walk(cwd):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            
            root_path = Path(root)
            
            for file in files:
                file_path = root_path / file
                
                if not _should_include(file_path, cwd):
                    continue
                
                # Check if name appears in file name or relative path
                rel_path = str(file_path.relative_to(cwd)).lower()
                file_name_lower = file.lower()
                
                if name in file_name_lower or name in rel_path:
                    results.append(file_path)
                    if len(results) >= max_results:
                        return results
    except (PermissionError, OSError):
        pass
    
    return results


def _should_include(file_path: Path, cwd: Path) -> bool:
    """Check if a file should be included in results."""
    # Check extension
    if file_path.suffix.lower() not in SEARCHABLE_EXTENSIONS:
        return False
    
    # Check if in skip directory
    try:
        rel_parts = file_path.relative_to(cwd).parts
        for part in rel_parts:
            if part in SKIP_DIRS:
                return False
    except ValueError:
        return False
    
    return True


def resolve_mentions(text: str, cwd: Path) -> Tuple[str, str]:
    """Resolve @mentions in user text.
    
    Returns:
        Tuple of (processed_text, context_info)
        - processed_text: Original text with @mentions preserved
        - context_info: Additional context about mentioned files to prepend
    """
    mentions = extract_mentions(text)
    
    if not mentions:
        return text, ""
    
    context_parts = []
    
    for mention in mentions:
        files = find_matching_files(mention, cwd)
        
        if files:
            file_list = []
            for f in files:
                try:
                    rel = f.relative_to(cwd)
                    file_list.append(str(rel))
                except ValueError:
                    file_list.append(str(f))
            
            context_parts.append(
                f"[@ File Mention: @{mention}]\n"
                f"Found {len(files)} matching file(s):\n"
                + "\n".join(f"  - {fp}" for fp in file_list)
            )
        else:
            context_parts.append(
                f"[@ File Mention: @{mention}]\n"
                f"No matching files found for '@{mention}'"
            )
    
    context_info = "\n\n".join(context_parts)
    
    return text, context_info


def format_mention_context(text: str, cwd: Path) -> str:
    """Process user message and return enhanced message with file context.
    
    If @mentions are found, prepends file context information to the message.
    """
    original_text, context_info = resolve_mentions(text, cwd)
    
    if not context_info:
        return original_text
    
    # Combine context with original message
    enhanced_message = f"""[FILE CONTEXT FROM @ MENTIONS]
{context_info}

[USER MESSAGE]
{original_text}"""
    
    return enhanced_message

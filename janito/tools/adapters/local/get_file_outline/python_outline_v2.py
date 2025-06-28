import re
from typing import List


def extract_signature_and_decorators(lines, start_idx):
    """
    Extracts the signature line and leading decorators for a given function/class/method.
    Returns (signature:str, decorators:List[str], signature_lineno:int)
    """
    decorators = []
    sig_line = None
    sig_lineno = start_idx
    for i in range(start_idx - 1, -1, -1):
        striped = lines[i].strip()
        if striped.startswith("@"):
            decorators.insert(0, striped)
            sig_lineno = i
        elif not striped:
            continue
        else:
            break
    # Find the signature line itself
    for k in range(start_idx, len(lines)):
        striped = lines[k].strip()
        if striped.startswith("def ") or striped.startswith("class "):
            sig_line = striped
            sig_lineno = k
            break
    return sig_line, decorators, sig_lineno


def extract_docstring(lines, start_idx, end_idx):
    """Extracts a docstring from lines[start_idx:end_idx] if present."""
    for i in range(start_idx, min(end_idx, len(lines))):
        line = lines[i].lstrip()
        if not line:
            continue
        if line.startswith('"""') or line.startswith("'''"):
            quote = line[:3]
            doc = line[3:]
            if doc.strip().endswith(quote):
                return doc.strip()[:-3].strip()
            docstring_lines = [doc]
            for j in range(i + 1, min(end_idx, len(lines))):
                line = lines[j]
                if line.strip().endswith(quote):
                    docstring_lines.append(line.strip()[:-3])
                    return "\n".join([d.strip() for d in docstring_lines]).strip()
                docstring_lines.append(line)
            break
        else:
            break
    return ""


def build_outline_entry(obj, lines, outline):
    obj_type, name, start, end, parent, indent = obj
    # Determine if this is a method
    if obj_type == "function" and parent:
        outline_type = "method"
    elif obj_type == "function":
        outline_type = "function"
    else:
        outline_type = obj_type
    docstring = extract_docstring(lines, start, end)
    signature, decorators, signature_lineno = extract_signature_and_decorators(
        lines, start - 1
    )
    outline.append(
        {
            "type": outline_type,
            "name": name,
            "start": start,
            "end": end,
            "parent": parent,
            "signature": signature,
            "decorators": decorators,
            "docstring": docstring,
        }
    )


def parse_python_outline_v2(lines: List[str]):
    class_pat = re.compile(r"^(\s*)class\s+(\w+)")
    func_pat = re.compile(r"^(\s*)def\s+(\w+)")
    assign_pat = re.compile(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*=.*")
    main_pat = re.compile(r"^\s*if\s+__name__\s*==\s*[\'\"]__main__[\'\"]\s*:")
    outline = []
    stack = []
    obj_ranges = []
    last_top_obj = None
    for idx, line in enumerate(lines):
        class_match = class_pat.match(line)
        func_match = func_pat.match(line)
        assign_match = assign_pat.match(line)
        indent = len(line) - len(line.lstrip())
        parent = ""
        for s in reversed(stack):
            if s[0] == "class" and indent > s[2]:
                parent = s[1]
                break
        if class_match:
            obj = ("class", class_match.group(2), idx + 1, None, parent, indent)
            stack.append(obj)
            last_top_obj = obj
        elif func_match:
            obj = ("function", func_match.group(2), idx + 1, None, parent, indent)
            stack.append(obj)
            last_top_obj = obj
        elif assign_match and indent == 0:
            outline.append(
                {
                    "type": "const" if assign_match.group(2).isupper() else "var",
                    "name": assign_match.group(2),
                    "start": idx + 1,
                    "end": idx + 1,
                    "parent": "",
                    "signature": line.strip(),
                    "decorators": [],
                    "docstring": "",
                }
            )
        if line.strip().startswith("if __name__ == "):
            outline.append(
                {
                    "type": "main",
                    "name": "__main__",
                    "start": idx + 1,
                    "end": idx + 1,
                    "parent": "",
                    "signature": line.strip(),
                    "decorators": [],
                    "docstring": "",
                }
            )
        # Close stack objects if indent falls back
        while stack and indent <= stack[-1][5] and idx + 1 > stack[-1][2]:
            finished = stack.pop()
            outline_entry = finished[:2] + (
                finished[2],
                idx + 1,
                finished[4],
                finished[5],
            )
            build_outline_entry(outline_entry, lines, outline)
    # Close any remaining objects
    while stack:
        finished = stack.pop()
        outline_entry = finished[:2] + (
            finished[2],
            len(lines),
            finished[4],
            finished[5],
        )
        build_outline_entry(outline_entry, lines, outline)
    return outline

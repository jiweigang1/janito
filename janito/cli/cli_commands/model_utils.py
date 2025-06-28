"""
Utilities for model-related CLI output
"""


def _print_models_table(models, provider_name):
    from rich.table import Table
    from rich.console import Console

    headers = [
        "name",
        "open",
        "context",
        "max_input",
        "max_cot",
        "max_response",
        "thinking_supported",
        "driver",
    ]
    display_headers = [
        "Model Name",
        "Vendor",
        "context",
        "max_input",
        "max_cot",
        "max_response",
        "Thinking",
        "Driver",
    ]
    table = Table(title=f"Supported models for provider '{provider_name}'")
    _add_table_columns(table, display_headers)
    num_fields = {"context", "max_input", "max_cot", "max_response"}
    for m in models:
        row = [str(m.get("name", ""))]
        row.extend(_build_model_row(m, headers, num_fields))
        table.add_row(*row)
    import sys
    if sys.stdout.isatty():
        from rich.console import Console
        Console().print(table)
    else:
        # ASCII-friendly fallback table when output is redirected
        print(f"Supported models for provider '{provider_name}'")
        headers_fallback = [h for h in display_headers]
        print(' | '.join(headers_fallback))
        for m in models:
            row = [str(m.get('name', ''))]
            row.extend(_build_model_row(m, headers, num_fields))
            print(' | '.join(row))


def _add_table_columns(table, display_headers):
    for i, h in enumerate(display_headers):
        justify = "right" if i == 0 else "center"
        table.add_column(h, style="bold", justify=justify)


def _format_k(val):
    try:
        n = int(val)
        if n >= 1000:
            return f"{n // 1000}k"
        return str(n)
    except Exception:
        return str(val)


def _build_model_row(m, headers, num_fields):
    def format_driver(val):
        if isinstance(val, (list, tuple)):
            return ", ".join(val)
        val_str = str(val)
        return val_str.removesuffix("ModelDriver").strip()

    row = []
    for h in headers[1:]:
        v = m.get(h, "")
        if h in num_fields and v not in ("", "N/A"):
            if (
                h in ("context", "max_input")
                and isinstance(v, (list, tuple))
                and len(v) == 2
            ):
                row.append(f"{_format_k(v[0])} / {_format_k(v[1])}")
            else:
                row.append(_format_k(v))
        elif h == "open":
            row.append("Open" if v is True or v == "Open" else "Locked")
        elif h == "thinking_supported":
            row.append("📖" if v is True or v == "True" else "")
        elif h == "driver":
            row.append(format_driver(v))
        else:
            row.append(str(v))
    return row

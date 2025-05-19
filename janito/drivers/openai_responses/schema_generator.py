import inspect
import typing
from collections import OrderedDict
from typing import List, get_origin, get_args

class OpenAIResponsesSchemaGenerator:
    PYTHON_TYPE_TO_JSON = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    def type_to_json_schema(self, annotation):
        origin = get_origin(annotation)
        args = get_args(annotation)
        # Handle enum via typing.Literal
        if origin is typing.Literal:
            values = list(args)
            types = set(type(v) for v in values)
            json_type = None
            if len(types) == 1:
                py_type = next(iter(types))
                json_type = self.PYTHON_TYPE_TO_JSON.get(py_type, "string")
            else:
                json_type = "string"  # fall back to string if mixed
            return {
                "type": json_type,
                "enum": values
            }
        if origin is list or origin is typing.List:
            return {
                "type": "array",
                "items": self.type_to_json_schema(args[0])
            }
        if origin is dict or origin is typing.Dict:
            return {"type": "object"}
        return {"type": self.PYTHON_TYPE_TO_JSON.get(annotation, "string")}

    def generate_schema(self, tool_class):
        func = getattr(tool_class, '__call__', tool_class)
        tool_name = getattr(tool_class, 'tool_name', tool_class.__name__)
        sig = inspect.signature(func)
        doc = inspect.getdoc(tool_class)
        properties = OrderedDict()
        required = []
        param_descs = {}
        # try to extract param descriptions from docstring
        if doc:
            lines = doc.split('\n')
            for line in lines:
                parts = line.strip().split(':', 1)
                if len(parts) == 2:
                    pname, pdesc = parts
                    param_descs[pname.strip()] = pdesc.strip()
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            annotation = param.annotation
            pdesc = param_descs.get(name, "")
            schema = self.type_to_json_schema(annotation)
            if pdesc:
                schema["description"] = pdesc
            properties[name] = schema
            if param.default == inspect._empty:
                required.append(name)
        return {
            "type": "function",
            "name": tool_name,
            "description": doc or "",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False
            },
            "strict": True
        }

def generate_tool_schemas(tool_classes: List[type]):
    generator = OpenAIResponsesSchemaGenerator()
    return [
        generator.generate_schema(tool_class)
        for tool_class in tool_classes
    ]

import inspect
import typing
from janito.tools.tools_schema import ToolSchemaBase

try:
    from google.genai import types as genai_types
except ImportError:
    genai_types = None


class GeminiSchemaGenerator(ToolSchemaBase):
    PYTHON_TYPE_TO_GENAI_TYPE = {
        str: "STRING",
        int: "INTEGER",
        float: "NUMBER",
        bool: "BOOLEAN",
        list: "ARRAY",
        dict: "OBJECT",
    }

    def type_to_genai_schema(self, annotation, description=None):
        if hasattr(annotation, "__origin__"):
            if annotation.__origin__ is list or annotation.__origin__ is typing.List:
                return genai_types.Schema(
                    type="ARRAY",
                    items=self.type_to_genai_schema(annotation.__args__[0]),
                    description=description,
                )
            if annotation.__origin__ is dict or annotation.__origin__ is typing.Dict:
                return genai_types.Schema(type="OBJECT", description=description)
        return genai_types.Schema(
            type=self.PYTHON_TYPE_TO_GENAI_TYPE.get(annotation, "STRING"),
            description=description,
        )

    def generate_declaration(self, tool_class):
        func, tool_name, sig, summary, param_descs, return_desc, description = (
            self.validate_tool_class(tool_class)
        )
        properties = {}
        required = []
        # Removed tool_call_reason from properties and required
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            annotation = param.annotation
            pdesc = param_descs.get(name, "")
            schema = self.type_to_genai_schema(annotation, description=pdesc)
            properties[name] = schema
            if param.default == inspect._empty:
                required.append(name)
        parameters_schema = genai_types.Schema(
            type="OBJECT", properties=properties, required=required
        )
        return genai_types.FunctionDeclaration(
            name=tool_name, description=description, parameters=parameters_schema
        )


def generate_tool_declarations(tool_classes: list):
    if genai_types is None:
        raise ImportError("google-genai package is not installed.")
    generator = GeminiSchemaGenerator()
    function_declarations = [
        generator.generate_declaration(tool_class) for tool_class in tool_classes
    ]
    return [genai_types.Tool(function_declarations=function_declarations)]

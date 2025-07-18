from typing import List, Dict, Any, Type
from pydantic import BaseModel

def pydantic_model_to_field_dicts(model: Type[BaseModel]) -> List[Dict[str, Any]]:
    field_dicts = []

    schema_extras = getattr(model.Config, "json_schema_extra", {})

    for field_name, field in model.model_fields.items():
        schema_extra = schema_extras.get(field_name)
        if schema_extra:
            field_dicts.append(schema_extra)

    return field_dicts

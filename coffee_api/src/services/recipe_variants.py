from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RecipeSettings(BaseModel):
    dose: float | None = Field(default=None, gt=0, le=1000)
    grind: str = Field(default='', max_length=80)
    temp: Literal['', '0', 'I', 'II'] = ''
    target_yield_g: float | None = Field(default=None, gt=0, le=1000)
    target_yield_max_g: float | None = Field(default=None, gt=0, le=1000)
    water_temp_c: float | None = Field(default=None, ge=0, le=100)
    water_g: float | None = Field(default=None, ge=0, le=5000)
    ice_g: float | None = Field(default=None, ge=0, le=5000)
    bloom_seconds: float | None = Field(default=None, ge=0, le=600)
    pressure: str = Field(default='', max_length=120)
    basket: str = Field(default='', max_length=120)
    puck_screen: Literal['yes', 'no', 'unknown'] = 'unknown'

    @model_validator(mode='after')
    def target_range(self):
        if self.target_yield_max_g is not None and (self.target_yield_g is None or self.target_yield_max_g < self.target_yield_g):
            raise ValueError('Target upper bound must be at least the target grams.')
        return self


class RecipeVariant(RecipeSettings):
    model_config = ConfigDict(extra='forbid', strict=True, str_strip_whitespace=True)
    reason: str = Field(min_length=1, max_length=2000)

    @model_validator(mode='after')
    def complete_recipe(self):
        if self.model_fields_set != set(type(self).model_fields):
            raise ValueError('Each option must supply all recipe fields.')
        if not any(self.model_dump(exclude={'puck_screen', 'reason'}).values()):
            raise ValueError('Each option must contain a brew setting.')
        if not any(character.isalnum() for character in self.reason):
            raise ValueError('Each option must explain its recipe.')
        return self


class RecipeVariants(BaseModel):
    model_config = ConfigDict(extra='forbid')
    with_paper: RecipeVariant
    without_paper: RecipeVariant


def recipe_variants_schema():
    schema = RecipeVariants.model_json_schema()
    recipe = schema['$defs']['RecipeVariant']
    # The bridge's strict schema requires every property. Unknown settings use
    # null, an empty string, or "unknown", as appropriate to the field.
    recipe['required'] = list(recipe['properties'])
    for field in recipe['properties'].values():
        # Native structured output constrains the shape. Pydantic enforces
        # lengths and numeric bounds that some bridge providers do not support.
        for part in (field, *field.get('anyOf', [])):
            for keyword in ('default', 'minimum', 'exclusiveMinimum', 'maximum', 'minLength', 'maxLength'):
                part.pop(keyword, None)
    return schema

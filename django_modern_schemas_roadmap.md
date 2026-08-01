# Django Modern Schemas - Roadmap y diseño de `Source`

Documento de trabajo para `django-modern-schemas`.

## 1. Objetivo del proyecto

La dirección recomendada para el proyecto no debería ser simplemente:

> "Generar modelos Pydantic a partir de modelos Django."

La propuesta más potente es:

> **Convertir metadata de Django ORM en schemas Pydantic v2, con validación, serialización y proyección declarativa de objetos Django.**

Conceptualmente:

```text
Django Model
     │
     ▼
Model Inspector
     │
     ▼
Field Metadata
     │
     ├───────────────┐
     ▼               ▼
Input Schema    Output Schema
     │               │
     └───────┬───────┘
             ▼
         Pydantic v2
             │
       ┌─────┼─────┐
       ▼     ▼     ▼
   Validate Serialize JSON Schema
```

La idea es que Django sea la fuente de información ORM y Pydantic sea el motor de typing, validación y serialización.

---

# 2. Recomendaciones arquitectónicas

## P0 - Prioridad alta

### 2.1 Eliminar `exec()` de la generación de schemas

La generación dinámica debería apoyarse en:

```python
from pydantic import create_model
```

en lugar de construir clases como strings y utilizar `exec()`.

Dirección:

```text
Django Model
    ↓
SchemaFactory
    ↓
create_model(...)
    ↓
Pydantic Model
```

Ventajas:

- menos magia;
- mejor typing;
- menor dependencia de código generado como string;
- mejor control sobre `__base__`, `__module__`, validators y config;
- API más alineada con Pydantic v2.

No es necesario hacer este cambio en el primer PR de `Source`.

---

## 2.2 Reducir la dependencia de internals de Pydantic

Evitar depender innecesariamente de:

```python
pydantic._internal.*
```

y especialmente de internals de `ModelMetaclass`.

La librería debería utilizar APIs públicas de Pydantic siempre que sea posible.

El metaclass puede mantenerse inicialmente por compatibilidad, pero la generación de schemas debería ir desplazándose hacia una capa explícita de factory/builder.

---

## 2.3 Definir correctamente `null`, `blank`, `Optional` y `required`

Estos conceptos no son equivalentes.

Debe existir una matriz de comportamiento explícita.

Ejemplo conceptual:

| Django | Pydantic |
|---|---|
| `null=False`, sin default | campo requerido |
| `null=True` | `T \| None` |
| default definido | default correspondiente |
| callable default | `default_factory` |
| optional explícito | `T \| None` |
| `blank=True` | no convertir automáticamente a nullable |

Especialmente:

```python
blank=True
```

no significa:

```python
null=True
```

`blank` pertenece principalmente a validación/formularios de Django, mientras que `null` representa almacenamiento en DB.

---

## 2.4 Revisar el registry/cache

No debería existir una relación conceptual simple:

```text
Model → Schema
```

si el schema puede cambiar según:

- `include`;
- `exclude`;
- `depth`;
- optional;
- relaciones;
- configuración;
- overrides.

La cache debería tener en cuenta la configuración efectiva.

Por ejemplo:

```text
(
    model,
    include,
    exclude,
    depth,
    optional,
    configuration,
)
        ↓
      Schema
```

Hay que evitar que:

```python
SchemaFactory.create_schema(User, depth=0)
```

contamine posteriormente:

```python
SchemaFactory.create_schema(User, depth=2)
```

---

## 2.5 Revisar `save()` y persistence

La capa de schema y la capa de persistence deberían estar conceptualmente separadas.

Una arquitectura más limpia:

```text
ModelSchema
    ├── validation
    ├── serialization
    └── schema generation

Persistence / Operations
    ├── create
    ├── update
    └── save
```

Si `save()` permanece en el schema, debe evitarse cualquier doble `save()` y dejar clara su semántica.

La prioridad debería ser que `ModelSchema` sea excelente en:

- input validation;
- output serialization;
- JSON Schema.

La persistencia puede ser una capacidad adicional.

---

# 3. P1 - Arquitectura intermedia

## 3.1 Introducir una representación intermedia de metadata

En lugar de hacer directamente:

```text
Django Field → Pydantic Field
```

usar:

```text
Django Field
      ↓
Field Metadata
      ↓
Pydantic Field
```

Ejemplo conceptual:

```python
FieldMetadata(
    name="email",
    python_type=str,
    nullable=False,
    required=True,
    default=...,
    max_length=255,
    description="User email",
)
```

Esto permite posteriormente:

```text
Field Metadata
     ├── Pydantic
     ├── JSON Schema
     ├── OpenAPI
     └── Documentation
```

No es obligatorio implementar una gran clase `FieldMetadata` inmediatamente. `Annotated` y `FieldInfo.metadata` pueden cubrir una parte importante de esta necesidad.

---

## 3.2 Separar el converter

El converter actual tiene demasiadas responsabilidades.

Separar conceptualmente:

```text
mapping/
    field_mapper.py
    scalar.py
    relational.py
    postgres.py
    choices.py

metadata/
    source.py
    resolver.py
```

El objetivo es que cada componente tenga una responsabilidad clara.

---

## 3.3 Extensibilidad para custom Django fields

Debe existir eventualmente un mecanismo público para registrar converters.

Ejemplo conceptual:

```python
@register_field(MyDjangoField)
def convert_my_field(field, context):
    ...
```

Esto permitiría soportar:

- custom fields;
- PostgreSQL fields;
- GIS;
- encrypted fields;
- money fields;
- fields de terceros.

La librería no puede soportar todos los ecosistemas Django por sí sola. Debe permitir extensiones.

---

# 4. Relaciones

## 4.1 `depth`

`depth` es útil y debe mantenerse, pero no debería ser el único mecanismo.

Ejemplo:

```python
depth=2
```

es sencillo, pero limitado para grafos reales.

Sería interesante soportar posteriormente configuración explícita:

```text
User
 ├── profile
 ├── groups
 │    └── permissions
 └── company
      └── address
```

con selección explícita de relaciones.

Conceptualmente:

```python
relations={
    "profile": ProfileSchema,
    "company": {
        "schema": CompanySchema,
        "relations": ["address"],
    },
}
```

No es necesario implementarlo todavía.

---

# 5. `QuerySet`, `RelatedManager` y N+1

El resolver no debe materializar silenciosamente relaciones arbitrarias.

Algo como:

```python
list(queryset)
```

puede provocar:

- queries inesperadas;
- materialización de muchos objetos;
- N+1;
- problemas de rendimiento.

La librería debería respetar que la carga de relaciones es responsabilidad del usuario:

```python
select_related(...)
prefetch_related(...)
```

El futuro resolver debe ser consciente de esto.

Una evolución interesante sería que un conjunto de `Source` pueda analizarse para recomendar o generar:

```python
select_related("category", "author__company")
```

pero esto es una feature posterior.

---

# 6. JSONField

No asumir automáticamente que:

```python
models.JSONField()
```

equivale siempre a:

```python
Json
```

Puede representar:

```python
dict[str, Any]
list[Any]
Any
```

o un tipo declarado explícitamente.

Debe darse prioridad a la anotación explícita del usuario cuando exista.

---

# 7. Choices

La conversión de Django choices a Enum es válida, pero puede ser útil ofrecer diferentes estrategias:

```text
enum
literal
preserve
```

Conceptualmente:

```python
choices_mode="enum"
```

o:

```python
choices_mode="literal"
```

Esto debe diseñarse antes de convertir todos los choices automáticamente.

---

# 8. Constraints y validators

Una de las oportunidades más importantes es convertir metadata de Django a constraints de Pydantic.

Ejemplo:

```python
models.IntegerField(
    validators=[
        MinValueValidator(10),
        MaxValueValidator(100),
    ]
)
```

podría producir algo conceptualmente equivalente a:

```python
Annotated[
    int,
    Field(ge=10, le=100),
]
```

También investigar:

- `MinValueValidator`;
- `MaxValueValidator`;
- `MinLengthValidator`;
- `MaxLengthValidator`;
- `RegexValidator`;
- `UniqueConstraint`;
- `CheckConstraint`.

No todos tienen una traducción directa a Pydantic, especialmente constraints que dependen de DB.

---

# 9. Input schemas y output schemas

Debe analizarse la separación entre schemas de entrada y salida.

Un modelo:

```python
class User(models.Model):
    id
    email
    password_hash
    created_at
```

puede necesitar:

```text
Output:
    id
    email
    created_at

Input:
    email
    password
```

No conviene hacer que `optional` sea responsable de resolver todos estos casos.

Una API futura podría separar explícitamente:

```text
UserSchema.input()
UserSchema.output()
```

o utilizar clases/configuración separadas.

---

# 10. `Source`

## 10.1 Objetivo

Agregar una metadata declarativa para indicar desde qué atributo de un objeto Django debe obtenerse el valor de un campo del schema.

Ejemplo:

```python
from typing import Annotated

from django_modern_schemas import ModelSchema, Source


class QuestionSchema(ModelSchema):
    category_name: Annotated[
        str | None,
        Source("category.name"),
    ]
```

Si el objeto es:

```text
question
    └── category
          └── name = "Python"
```

el campo:

```python
category_name
```

debe obtener:

```text
question.category.name
```

---

# 11. Por qué `Source` debe ser metadata

No se recomienda crear otro `Field()` propio.

Pydantic v2 ya tiene:

```python
Annotated
```

y:

```python
FieldInfo.metadata
```

La librería puede definir:

```python
Source("category.name")
```

como metadata propia.

Ejemplo:

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Source:
    path: str
```

Entonces:

```python
category_name: Annotated[
    str,
    Source("category.name"),
]
```

permite que Pydantic conserve el objeto dentro de:

```python
field.metadata
```

Esto mantiene la API alineada con Pydantic v2.

---

# 12. Implementación de `Source`

Archivo:

```text
src/django_modern_schemas/metadata/source.py
```

Implementación:

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Source:
    path: str

    def __post_init__(self) -> None:
        path = self.path.strip()

        if not path:
            raise ValueError("Source path cannot be empty.")

        parts = path.split(".")

        if any(not part for part in parts):
            raise ValueError(
                f"Invalid source path {self.path!r}. "
                "Source paths must contain non-empty attributes."
            )

        object.__setattr__(self, "path", path)

    @property
    def parts(self) -> tuple[str, ...]:
        return tuple(self.path.split("."))
```

---

# 13. SourceResolver

El resolver debe ser independiente del schema.

Archivo:

```text
src/django_modern_schemas/metadata/resolver.py
```

Implementación inicial:

```python
from collections.abc import Mapping
from typing import Any

from .exceptions import SourceResolutionError
from .source import Source


class SourceResolver:
    def resolve(self, instance: Any, source: Source) -> Any:
        value = instance

        for part in source.parts:
            if value is None:
                return None

            value = self._resolve_attribute(
                value=value,
                attribute=part,
                source=source,
            )

        return value

    def _resolve_attribute(
        self,
        value: Any,
        attribute: str,
        source: Source,
    ) -> Any:
        if isinstance(value, Mapping):
            try:
                return value[attribute]
            except KeyError as exc:
                raise SourceResolutionError(
                    f"Unable to resolve {source.path!r}: "
                    f"key {attribute!r} was not found."
                ) from exc

        try:
            return getattr(value, attribute)
        except AttributeError as exc:
            raise SourceResolutionError(
                f"Unable to resolve {source.path!r}: "
                f"attribute {attribute!r} was not found on "
                f"{type(value).__name__}."
            ) from exc
```

---

# 14. SourceResolutionError

Archivo:

```text
src/django_modern_schemas/metadata/exceptions.py
```

```python
class SourceResolutionError(Exception):
    """Raised when a Source cannot be resolved."""
```

Exportar desde:

```python
src/django_modern_schemas/metadata/__init__.py
```

```python
from .exceptions import SourceResolutionError
from .resolver import SourceResolver
from .source import Source

__all__ = [
    "Source",
    "SourceResolver",
    "SourceResolutionError",
]
```

Y desde el paquete principal:

```python
from .metadata import Source, SourceResolutionError, SourceResolver

__all__ = [
    "Source",
    "SourceResolver",
    "SourceResolutionError",
]
```

---

# 15. Cómo ejecutar `Source` con atributos

## 15.1 Atributo simple

Modelo:

```python
class Question:
    text = "What is Django?"
```

Schema:

```python
class QuestionSchema(ModelSchema):
    text: Annotated[
        str,
        Source("text"),
    ]
```

Resolver:

```python
resolver = SourceResolver()

value = resolver.resolve(
    question,
    Source("text"),
)
```

Resultado:

```text
"What is Django?"
```

---

# 16. Atributos anidados

Django:

```python
class Question(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
    )
```

y:

```python
class Category(models.Model):
    name = models.CharField(max_length=100)
```

Schema:

```python
class QuestionSchema(ModelSchema):
    category_name: Annotated[
        str | None,
        Source("category.name"),
    ]
```

Resolver:

```python
value = resolver.resolve(
    question,
    Source("category.name"),
)
```

Internamente:

```text
question
    ↓
category
    ↓
name
```

equivale conceptualmente a:

```python
question.category.name
```

---

# 17. Atributos profundamente anidados

También:

```python
class QuestionSchema(ModelSchema):
    company_name: Annotated[
        str | None,
        Source("author.company.name"),
    ]
```

El resolver ejecuta conceptualmente:

```python
question.author.company.name
```

sin tener que crear schemas intermedios solamente para exponer ese valor.

---

# 18. `None` en medio del path

Si:

```python
question.category is None
```

y tenemos:

```python
Source("category.name")
```

el resolver debe retornar:

```python
None
```

en lugar de intentar:

```python
None.name
```

Esto es importante para relaciones nullable.

---

# 19. Resolver desde mappings

El resolver puede soportar también:

```python
data = {
    "category": {
        "name": "Python",
    }
}
```

y:

```python
resolver.resolve(
    data,
    Source("category.name"),
)
```

resultará en:

```text
"Python"
```

Esto puede ser útil para tests y para escenarios donde el input ya sea un mapping.

---

# 20. Source con métodos

Hay que distinguir entre atributos y métodos.

No recomiendo ejecutar automáticamente:

```python
getattr(value, "get_display_name")()
```

si el source es:

```python
Source("get_display_name")
```

porque eso convierte cualquier atributo callable en una operación implícita.

Esto puede producir efectos secundarios y comportamiento sorprendente.

## Opción recomendada

Introducir una sintaxis explícita para métodos.

Por ejemplo:

```python
Source("get_display_name()")
```

o, mejor aún, una metadata específica:

```python
MethodSource("get_display_name")
```

La segunda opción es más explícita y segura.

---

# 21. `MethodSource`

Diseño posible:

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MethodSource:
    name: str
```

Uso:

```python
class QuestionSchema(ModelSchema):
    display_name: Annotated[
        str,
        MethodSource("get_display_name"),
    ]
```

Resolver:

```python
value = resolver.resolve_method(
    question,
    MethodSource("get_display_name"),
)
```

Internamente:

```python
method = getattr(question, "get_display_name")
value = method()
```

El resolver debería verificar que sea callable:

```python
if not callable(method):
    raise SourceResolutionError(...)
```

---

# 22. Métodos anidados

Para una primera versión, no permitiría automáticamente:

```python
Source("author.get_display_name()")
```

hasta tener una gramática clara.

Si se necesita, una API explícita podría ser:

```python
MethodSource("author.get_display_name")
```

y el resolver podría navegar:

```text
question
    ↓
author
    ↓
get_display_name()
```

Pero esto es una segunda iteración.

---

# 23. No mezclar `Source` con persistence

`Source` debería representar:

> de dónde obtener un valor para el schema.

No debería significar:

> dónde guardar ese valor en Django.

Por ejemplo:

```python
category_name: Annotated[
    str,
    Source("category.name"),
]
```

no debe intentar hacer:

```python
question.category.name = value
```

durante:

```python
QuestionSchema(...)
```

La semántica inicial debe ser de lectura/serialización.

Para input/persistence se debe diseñar posteriormente un mecanismo separado.

---

# 24. Integración futura con `ModelSchema`

El pipeline recomendado:

```text
ModelSchema
     │
     ▼
Python annotations
     │
     ▼
Annotated metadata
     │
     ▼
FieldInfo.metadata
     │
     ▼
Source
     │
     ▼
SourceResolver
     │
     ▼
Django instance
```

Por ejemplo:

```python
class QuestionSchema(ModelSchema):
    text: str

    category_name: Annotated[
        str | None,
        Source("category.name"),
    ]
```

El introspector debe poder encontrar:

```python
field = QuestionSchema.model_fields["category_name"]
```

y después:

```python
source = next(
    (
        metadata
        for metadata in field.metadata
        if isinstance(metadata, Source)
    ),
    None,
)
```

Si existe:

```python
value = resolver.resolve(
    instance,
    source,
)
```

Si no existe:

```python
value = getattr(instance, field_name)
```

---

# 25. `Source` y `Field`

No crear un `Field` propio únicamente para soportar `source`.

La opción preferida es:

```python
from typing import Annotated

class QuestionSchema(ModelSchema):
    category_name: Annotated[
        str,
        Source("category.name"),
    ]
```

Cuando se necesite metadata de Pydantic:

```python
from typing import Annotated
from pydantic import Field

class QuestionSchema(ModelSchema):
    category_name: Annotated[
        str,
        Source("category.name"),
        Field(description="Category name"),
    ]
```

Esto mantiene separadas las responsabilidades:

```text
Source
    → Django Modern Schemas

Field
    → Pydantic

Annotated
    → composición de metadata
```

---

# 26. `validation_alias` y `AliasPath`

Pydantic también tiene:

```python
AliasPath("category", "name")
```

y `validation_alias`.

Esto es útil para **input validation**, pero no debería confundirse automáticamente con `Source`.

Conceptualmente:

```text
validation_alias
    → cómo encontrar datos de entrada

Source
    → cómo obtener datos de un objeto Django
```

Podrían eventualmente interoperar, pero deben mantener semánticas claras.

---

# 27. Queries y N+1

Esta parte es crítica.

Si:

```python
Source("category.name")
```

se evalúa sobre:

```python
question
```

y `category` no fue cargado, Django puede ejecutar una query.

Si tenemos:

```python
Source("author.company.name")
```

puede haber más queries.

Por eso el resolver **no debería intentar ocultar la responsabilidad de optimizar el QuerySet**.

El usuario debe poder preparar:

```python
Question.objects.select_related(
    "category",
    "author__company",
)
```

antes de serializar.

---

# 28. Tests obligatorios para Source

Como mínimo:

```text
✓ direct attribute
✓ nested attribute
✓ deeply nested attribute
✓ None intermediate value
✓ missing attribute
✓ invalid path
✓ mapping
✓ ForeignKey
✓ nullable ForeignKey
✓ OneToOne
✓ reverse relation
✓ ManyToMany
✓ Query count
✓ method source
✓ non-callable method error
```

Los tests de Django deben comprobar también queries.

Ejemplo conceptual:

```python
with self.assertNumQueries(1):
    schema = QuestionSchema.model_validate(question)
```

y otro test debe comprobar que `select_related()` evita queries adicionales cuando corresponda.

---

# 29. Orden recomendado de implementación

No hacer todo al mismo tiempo.

## PR 1 - Source metadata

Implementar:

```text
Source
Annotated
FieldInfo.metadata
```

Sin resolver todavía.

Objetivo:

```python
field.metadata
```

debe contener `Source`.

---

## PR 2 - SourceResolver

Implementar:

```text
Source
SourceResolver
SourceResolutionError
```

Soportar:

- atributos;
- paths;
- mappings;
- `None`.

Todavía sin integrar profundamente con `ModelSchema`.

---

## PR 3 - Integración con ModelSchema

Hacer:

```text
ModelSchema
    ↓
metadata
    ↓
SourceResolver
```

y permitir:

```python
class QuestionSchema(ModelSchema):
    category_name: Annotated[
        str | None,
        Source("category.name"),
    ]
```

---

## PR 4 - Métodos

Implementar una API explícita para métodos.

Preferiblemente:

```python
MethodSource("get_display_name")
```

en lugar de ejecutar automáticamente cualquier callable.

---

## PR 5 - Relaciones

Agregar tests y comportamiento para:

- ForeignKey;
- OneToOne;
- reverse relations;
- ManyToMany.

Aquí estudiar cuidadosamente `QuerySet`, `RelatedManager` y N+1.

---

## PR 6 - Optimización

Investigar:

```text
Source paths
     ↓
dependency graph
     ↓
select_related / prefetch_related
```

Esto podría convertirse en una feature avanzada de la librería.

---

# 30. Orden general de las demás mejoras

Después de `Source`:

```text
1. Source metadata
2. SourceResolver
3. Integración ModelSchema
4. MethodSource
5. Relaciones y N+1
6. null / blank / Optional / required
7. Registry/cache
8. create_model()
9. eliminar exec()
10. reducir internals de Pydantic
11. separar converter
12. Field metadata
13. custom field converters
14. Django validators → Pydantic constraints
15. JSONField
16. Choices
17. Input/Output schemas
18. OpenAPI / integraciones
```

No conviene hacer un rewrite completo antes de validar estas piezas pequeñas.

---

# 31. Principio de diseño

La regla que debería guiar estas decisiones:

> **Django Modern Schemas debe extender Pydantic, no intentar convertirse en un segundo Pydantic.**

Por eso:

```text
Annotated
FieldInfo
Field
create_model
model_validate
model_dump
```

deben seguir siendo conceptos de Pydantic.

Mientras que:

```text
Source
MethodSource
Django Model introspection
Django Field conversion
Django relation handling
```

son responsabilidad de Django Modern Schemas.

El resultado ideal es:

```text
             Django ORM
                  │
                  ▼
        Django Modern Schemas
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
     Source    Relations   Metadata
       │          │          │
       └──────────┼──────────┘
                  ▼
              Pydantic v2
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
   Validation Serialization JSON Schema
```

La meta no es hacer "otro djantic".

La meta es tener una capa moderna y extensible que permita que Django ORM y Pydantic v2 trabajen juntos de forma declarativa.

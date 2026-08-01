from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Source:
    """Metadata that resolves a schema field from a dotted object attribute path."""

    path: str

    def __post_init__(self) -> None:
        path = self.path.strip()
        if not path:
            raise ValueError('Source path cannot be empty.')

        if any(not part.isidentifier() for part in path.split('.')):
            raise ValueError(f'Invalid Source path {self.path!r}. Source paths must contain valid Python attributes.')

        object.__setattr__(self, 'path', path)

    @property
    def parts(self) -> tuple[str, ...]:
        return tuple(self.path.split('.'))


@dataclass(frozen=True, slots=True)
class MethodSource:
    """Metadata that resolves a schema field by invoking a model method without arguments."""

    name: str

    def __post_init__(self) -> None:
        name = self.name.strip()
        if not name:
            raise ValueError('MethodSource name cannot be empty.')
        if not name.isidentifier():
            raise ValueError('MethodSource only supports methods on the source object.')

        object.__setattr__(self, 'name', name)

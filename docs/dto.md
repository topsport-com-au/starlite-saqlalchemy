# DTOs

## What are DTOs?

DTO stands for "Data Transfer Object". They are the filter through which data is accepted into, and
output from the application.

## Why DTOs?

Data that is modifiable by clients, and that should be read by clients is often only a subset of the
attributes that make up a domain object.

For example, lets say we have an internal representation of an `Author` that looks like this:

```json
{
  "id": "97108ac1-ffcb-411d-8b1e-d9183399f63b",
  "name": "Agatha Christie",
  "dob": "1890-9-15",
  "created": "2022-11-27T01:58:00",
  "updated": "2022-11-27T01:59:00"
}
```

Of those attributes, values for "id", "created" and "updated" are internally generated, and should
not be available to be modified by clients of our application.

This is where a DTO comes in. We create a type to validate user input that will only allow values
for "name" and "dob" from clients, for example:

```json
{
  "name": "Agatha Christie",
  "dob": "1890-9-15"
}
```

## dto.FromMapped

- Generate pydantic models from SQLAlchemy ORM models.
- Mark fields as "read-only" or "private" to control inclusion of fields on DTO models.
- Automatically infer defaults, and default factories from the SQLAlchemy column definitions.

The [`dto.FromMapped`](../reference/starlite_saqlalchemy/dto/#starlite_saqlalchemy.dto.FromMapped)
type allows us to use our domain models, which are defined as SQLAlchemy ORM types, to generate
DTOs.

Here's a quick example.

```py title="Simple Example"
--8<-- "examples/dto/minimal.py"
```

Read the comments in the example for a description of everything that is going on, however notice
that the fields on our DTO type include "id", "created", and "updated" - fields that should not be
modifiable by clients.

Let's have another go:

```py title="Simple Example with Read Only Fields"
--8<-- "examples/dto/minimal_configure_fields.py"
```

That's better! Now, we'll only parse "name" and "dob" fields out of client input.

## Configuring generated DTOs

Th two main factors that influence how a DTO is generated for a given domain model are:

1. The modifiability and privacy of the individual attributes of the domain model.
2. The purpose of the DTO, is it to be used to parse and validate inbound client data, or to
   serialize outbound data.

## Configuring DTO Fields

### dto.DTOField

This is the object that we use to configure DTO fields. To use the
[`dto.DTOField`][starlite_saqlalchemy.dto.types.DTOField] object assign a dict to the `mapped_column()` or
`relationship` `info` parameter, with the `"dto"` key and an instance of `dto.DTOField` as value, for
example `col: Mapped[str] = mapped_column(info={"dto": dto.DTOField(...)})`.

The `dto.DTOField` object supports marking fields as `"read-only"` or `"private"`, setting an explicit
pydantic `FieldInfo` and type, and setting validators for the field.

The easiest way to configure a DTO field is through the
[`dto.field()`][starlite_saqlalchemy.dto.utils.field] function.

### dto.field()

The [`dto.field()`][starlite_saqlalchemy.dto.utils.field] function creates an `info` dict for us,
setting values on an `dto.DTOField` instance as appropriate. For example, the following are identical:

- `col: Mapped[str] = mapped_column(info={"dto": dto.DTOField(mark=dto.Mark.PRIVATE)})`
- `col: Mapped[str] = mapped_column(info=dto.field("private"))`

`field()` supports the same arguments as `DTOField`, however it will also coerce string values for mark
to the appropriate enum.

### dto.Mark

Fields on our domain models can take one of three states.

1. Normal - field can be written to, and read by clients, this is the state of unmarked fields.
2. Read-only - field can be read by clients, but not modified.
3. Private - field can not be read or updated by client.

The [`dto.Mark`][starlite_saqlalchemy.dto.types.Mark] enumeration lets us express these states on
our domain models.

`dto.field()` will accept the mark values as either the explicit enum, or its string representation,
e.g., `dto.field(dto.Mark.PRIVATE)` and `dto.field("private")` are equivalent.

### Example

The following example demonstrates all field configurations available via the `field()` function.

```py title="DTOField Configuration Example"
--8<-- "examples/dto/complete_field_example.py"
```

### SQLAlchemy info dictionary

SQLAlchemy [`Column`][sqlalchemy.schema.Column] and [`relationship`][sqlalchemy.orm.relationship]
accept an `info` parameter, which allows us to store data alongside the columns and relationships of
our model definitions. This is what we use to configure our DTOs at the model level.

### Info dict namespace key

The key that is used to namespace our DTO configuration in the `info` dict is configurable via
environment. By default, this is `"dto"`, however it can be changed to anything you like by setting
the `API_DTO_INFO_KEY` environment variable.

## Configuring DTO Objects

### dto.DTOConfig

This is the object that controls the generated DTO, and should be passed as the first argument to
`Annotated` when declaring the DTO. For example, to create a "read" purposed DTO that excludes the
"id" field:

`ReadDTO = dto.FromMapped[Annotated[Author, dto.DTOConfig(purpose=dto.Purpose.READ, exclude={"id"})]]`

The [`dto.config()`][starlite_saqlalchemy.dto.utils.config] function allows for more compact
expression of DTO configuration.

### dto.config()

Factory function for creating `DTOConfig` instances, and handles coercing the literal strings "read"
and "write" to their `dto.Purpose` enum counterpart.

For example to create a write purposed DTO using the `dto.config()` function:

`WriteDTO = dto.FromMapped[Annotated[Author, dto.config("write")]]`

Which is equivalent to:

`WriteDTO = dto.FromMapped[Annotated[Author, dto.DTOConfig(purpose=dto.Purpose.WRITE)]]`

### Annotated positional arguments

The first argument to [`Annotated`][typing.Annotated] must always be the SQLAlchemy ORM type.
We inspect a single additional positional argument after that, which can either be the string name
of a `dto.Purpose` enum, or a `dto.DTOConfig` object.

For example, these three definitions are equivalent:

- `WriteDTO = dto.FromMapped[Annotated[Author, dto.DTOConfig(purpose=dto.Purpose.WRITE)]]`
- `WriteDTO = dto.FromMapped[Annotated[Author, dto.config("write")]]`
- `WriteDTO = dto.FromMapped[Annotated[Author, "write"]]`

### dto.Purpose

`dto.Purpose` has two values, `dto.Purpose.READ` and `dto.Purpose.WRITE`. These are used to tell
the factory if the purpose of the DTO is to parse data submitted by the client for updating or
"writing" to a resource, or if it is to serialize data to be transmitted back to, or "read" by the
client.

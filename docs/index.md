# starlite-saqlalchemy

Starlite, SQLAlchemy 2.0 and SAQ configuration plugin.

```py title="Simple Example"
--8<-- "examples/basic_example.py"
```

Configuration via environment.

```dotenv title="Example .env"
--8<-- ".env.example"
```

## Pattern

``` mermaid
sequenceDiagram
  Client ->> Controller: Inbound request data
  Controller ->> Service: Invoke service with data validated by DTO
  Service ->> Repository: View or modify the collection
  Repository ->> Service: Detached SQLAlchemy instance(s)
  Service ->> Queue: Enqueue async callback
  Service ->> Controller: Outbound data
  Controller ->> Client: Serialize via DTO
  Queue ->> Worker: Worker invoked
  Worker ->> Service: Makes async callback
```

- Request data is deserialized and validated by Starlite before it is received by controller.
- Controller invokes relevant service object method and waits for response.
- Service method handles business logic of the request and triggers an asynchronous callback.
- Service method returns to controller and response is made to client.
- Async worker makes callback to service object where any async tasks can be performed.
  Depending on architecture, this may not even be the same instance of the application that handled
  the request.

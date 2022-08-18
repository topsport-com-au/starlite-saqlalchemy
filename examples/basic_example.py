from starlite_lib.starlite import Starlite, get


@get("/example")
def example_handler() -> dict:
    return {"hello": "world"}


app = Starlite(route_handlers=[example_handler])

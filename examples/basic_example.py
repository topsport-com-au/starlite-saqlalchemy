from starlite import Starlite

from starlite_lib import ConfigureApp, get


@get("/example")
def example_handler() -> dict:
    return {"hello": "world"}


app = Starlite(route_handlers=[example_handler], on_app_init=[ConfigureApp()])

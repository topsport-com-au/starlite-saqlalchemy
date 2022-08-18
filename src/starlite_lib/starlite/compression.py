from starlite.config import CompressionBackend, CompressionConfig

config = CompressionConfig(backend=CompressionBackend.GZIP)
"""Default compression config"""

from starlite.config.compression import CompressionBackend, CompressionConfig

config = CompressionConfig(backend=CompressionBackend.GZIP)
"""Default compression config"""

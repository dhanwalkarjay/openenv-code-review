[project.scripts]
server = "server.app:main"

[tool.openenv]
entrypoint = "server.app:main"
requires = ["openenv>=0.2.0"]
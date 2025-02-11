import os
from typing import Any, Dict

from sphinx.application import Sphinx


def on_rtd() -> bool:
    return os.getenv("READTHEDOCS") == "True"


def on_pr(html_context: Dict[str, str]) -> bool:
    return (
        html_context["github_version"].startswith(html_context["commit"])
        or os.getenv("GITHUB_EVENT_NAME") == "pull_request"
    )


def inject_changed_files(html_context: Dict[str, str], app: Sphinx) -> None:
    import requests

    res = requests.get(
        f"https://api.github.com/repos/{app.config.delta_repo}/pulls/{html_context['current_version']}/files"
    )
    if res.status_code != requests.codes.ok:
        return

    changes_rst = "".join(
        [
            ".. toctree::\n",
            "   :maxdepth: 1\n",
            "   :caption: PR CHANGED FILES\n",
            "\n",
        ]
    )

    for file_context in res.json():
        status: str = file_context["status"]
        filename: str = file_context["filename"]
        if status == "deleted":
            continue
        if not filename.startswith(app.config.delta_doc_path):
            continue
        if not filename.endswith(".rst"):
            continue

        changes_rst += f"   {os.path.relpath(filename, app.config.delta_doc_path)}\n"

    changes_rst += "\n\n.. todolist::\n"

    if app.config.delta_inject_location is None:
        inject_location = "index.rst"
    else:
        inject_location = app.config.delta_inject_location

    with open(inject_location, "a") as f:
        f.write(changes_rst)


def config_inited(app: Sphinx, config: Dict[str, Any]):
    if on_rtd() and on_pr(config["html_context"]):
        inject_changed_files(config["html_context"], app)


def setup(app: Sphinx) -> Dict[str, Any]:
    app.connect("config-inited", config_inited)
    app.add_config_value("delta_doc_path", "", str)
    app.add_config_value("delta_repo", "", str)
    app.add_config_value("delta_inject_location", "", None)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
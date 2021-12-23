import os
from pathlib import Path
from typing import Dict, List

import pkg_resources
import uvicorn
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import RustLexer
from pygments.lexers import BashLexer
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.staticfiles import StaticFiles

app = FastAPI()

templates = Jinja2Templates(directory=pkg_resources.resource_filename("rustsmith_viewer", "templates/"))

directory = "/Users/mayank/Documents/RustSmith/outRust"

mapping = {"primary": "All correct", "secondary": "No results", "danger": "Compilation Error", "warning": "Bug found!!"}

app.mount(
    "/static", StaticFiles(directory=pkg_resources.resource_filename("rustsmith_viewer", "static/")), name="static"
)


@app.get("/")
async def root():
    files: List[str] = os.listdir(directory)
    files.sort(key=lambda x: int(x.split("file")[1]))
    if len(files):
        return RedirectResponse(f"/file/{files[0]}")
    else:
        return "No generated files"


@app.get("/file/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str):
    files: List[str] = os.listdir(directory)
    files.sort(key=lambda x: int(x.split("file")[1]))
    optimization_flags = ["0", "1", "2", "3", "s", "z"]
    file_summary: Dict[str, str] = {}
    for file in files:
        file_summary[file] = "secondary"
        outputs = []
        for flag in optimization_flags:
            path = Path(directory, file, f"O{flag}", "output.log")
            if path.exists():
                with open(path, "r") as output_file:
                    outputs.append(output_file.read())
            else:
                path = Path(directory, file, f"O{flag}", "compile.log")
                if path.exists():
                    file_summary[file] = "danger"
                else:
                    file_summary[file] = "secondary"
                break
        if len(outputs):
            if all(x == outputs[0] for x in outputs):
                file_summary[file] = "primary"
            else:
                file_summary[file] = "warning"

    with open(Path(directory) / id / f"{id}.rs", "r") as file:
        file_content = highlight(file.read(), RustLexer(), HtmlFormatter(noclasses=True, cssclass="source"))

    with open(Path(directory) / id / f"{id}.json", "r") as file:
        json_ast = file.read()

    compile_log_content = "No Compile Log file found"

    try:
        with open(Path(directory) / id / f"O0" / "compile.log", "r") as file:
            compile_log_content = file.read()
    except:
        pass

    output_log_content = "No Output Log file found"

    try:
        with open(Path(directory) / id / f"O0" / "output.log", "r") as file:
            output_log_content = file.read()
    except:
        pass

    return templates.TemplateResponse(
        "item.jinja2",
        {
            "request": request,
            "mapping": mapping,
            "files": files,
            "id": id,
            "compile_log": highlight(
                compile_log_content, BashLexer(), HtmlFormatter(noclasses=True, cssclass="source")
            ),
            "content": file_content,
            "summary": file_summary,
            "json_ast": json_ast,
            "output_log": highlight(output_log_content, BashLexer(), HtmlFormatter(noclasses=True, cssclass="source")),
        },
    )


def main():
    print(pkg_resources.resource_filename("rustsmith_viewer", "static/"))
    uvicorn.run(app)


if __name__ == "__main__":
    main()

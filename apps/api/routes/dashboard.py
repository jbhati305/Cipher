from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request) -> str:
    settings = request.app.state.settings
    repository = request.app.state.repository
    memos_status = request.app.state.memos_client.health()
    llm_status = request.app.state.llm_router.health()
    tasks = repository.list_tasks()[:10]
    projects = repository.list_projects()[:10]
    memories = repository.list_memory_events(limit=10)
    papers = repository.list_papers()[:10]
    project_items = "".join(
        f"<li>{project.name} ({project.status})</li>" for project in projects
    ) or "<li>No projects yet.</li>"
    task_items = "".join(
        f"<li>{task.title} ({task.status})</li>" for task in tasks
    ) or "<li>No tasks yet.</li>"
    paper_items = "".join(
        f"<li>{paper.title} ({paper.status or 'unknown'})</li>" for paper in papers
    ) or "<li>No synced papers yet.</li>"
    memory_items = "".join(
        f"<li>{memory.kind}: {memory.content}</li>" for memory in memories
    ) or "<li>No memory writes yet.</li>"
    return f"""
    <!doctype html>
    <html>
      <head>
        <title>Cipher Dashboard</title>
        <script src="https://unpkg.com/htmx.org@1.9.12"></script>
        <style>
          body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #17202a; }}
          section {{ margin-bottom: 2rem; }}
          table {{ border-collapse: collapse; width: 100%; }}
          th, td {{ border-bottom: 1px solid #ddd; padding: .5rem; text-align: left; }}
          code {{ background: #f4f4f4; padding: .15rem .3rem; border-radius: 4px; }}
        </style>
      </head>
      <body>
        <h1>Cipher</h1>
        <section>
          <h2>System</h2>
          <p>Environment: <code>{settings.environment}</code></p>
          <p>SQLite: <code>{settings.resolved_sqlite_path}</code></p>
          <p>MemOS: <code>{memos_status}</code></p>
          <p>LLM: <code>{llm_status}</code></p>
        </section>
        <section>
          <h2>Projects</h2>
          <ul>{project_items}</ul>
        </section>
        <section>
          <h2>Tasks</h2>
          <ul>{task_items}</ul>
        </section>
        <section>
          <h2>Research Papers</h2>
          <ul>{paper_items}</ul>
        </section>
        <section>
          <h2>Recent Memory Writes</h2>
          <ul>{memory_items}</ul>
        </section>
      </body>
    </html>
    """

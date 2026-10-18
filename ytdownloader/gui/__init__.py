"""Desktop GUI (CustomTkinter)."""


def run() -> int:
    from ytdownloader.core.service import Service
    from ytdownloader.core.settings import load_settings
    from ytdownloader.core.tools import ToolManager

    from .app import MainWindow

    tools = ToolManager()
    service = Service(tools)
    window = MainWindow(service, tools, load_settings())
    window.mainloop()
    return 0

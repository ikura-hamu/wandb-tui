import wandb
from textual import work, worker
from textual.app import App

from .controllers import RunsController
from .models import WandbRunsModel
from .repositories import WandbRunRepository
from .services import RunService


class RunApp(App):
    CSS_PATH = "../styles/run.tcss"

    def __init__(
        self, driver_class=None, css_path=None, watch_css=False, ansi_color=False
    ):
        super().__init__(driver_class, css_path, watch_css, ansi_color)

        # Initialize dependencies
        wandb.login()
        repository = WandbRunRepository()
        self.service = RunService(repository)
        self.model = WandbRunsModel()
        self.controller: RunsController | None = None  # Initialized on mount
        self.worker: worker.Worker | None = None

    def compose(self):
        """Compose the UI components."""
        yield RunsController(self.model, self.service)

    def on_mount(self):
        """Called when the app is mounted."""
        self.controller = self.query_one(RunsController)
        self.worker = self.fetch_wandb_data()

    @work(exclusive=True, thread=True)
    def fetch_wandb_data(self) -> None:
        """Fetches WandB data in a background thread."""
        project_name = "ikura-hamu-institute-of-science-tokyo/Load-aware_Tram-FL"

        if self.controller:
            self.controller.load_runs(project_name)

    def on_unmount(self) -> None:
        """Clean up when the app is unmounted."""
        if self.controller:
            self.controller.cleanup()

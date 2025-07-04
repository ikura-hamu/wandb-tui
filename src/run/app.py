import wandb
from textual import work, worker
from textual.app import App

from .controllers import RunsController
from .models import WandbApiDataSource, WandbRunsModel


class RunApp(App):
    CSS_PATH = "../styles/run.tcss"

    def __init__(
        self, driver_class=None, css_path=None, watch_css=False, ansi_color=False
    ):
        super().__init__(driver_class, css_path, watch_css, ansi_color)

        # 依存関係の初期化
        wandb.login()
        self.data_source: WandbApiDataSource = WandbApiDataSource()
        self.model: WandbRunsModel = WandbRunsModel(self.data_source, "")
        self.controller: RunsController | None = None  # マウント後に初期化
        self.worker: worker.Worker | None = None  # ワーカースレッドの初期化

    def compose(self):
        """UIコンポーネントを構成"""
        yield RunsController(self.model)

    def on_mount(self):
        """アプリケーション起動時の処理"""
        # ビューがマウントされた後にコントローラーを初期化
        self.controller = self.query_one(RunsController)
        # データ取得を開始
        self.worker = self.fetch_wandb_data()

    @work(exclusive=True, thread=True)
    def fetch_wandb_data(self) -> None:
        """WandBからデータを非同期で取得する"""
        # プロジェクト名を定数として定義
        project_name = "ikura-hamu-institute-of-science-tokyo/Load-aware_Tram-FL"

        try:
            # データを読み込み
            if self.controller:
                self.controller.load_runs(project_name)
        except Exception as e:
            # エラーハンドリング
            self.call_from_thread(
                self.notify, f"Failed to load data: {str(e)}", severity="error"
            )

    def on_unmount(self) -> None:
        """アプリケーション終了時のクリーンアップ"""
        if self.controller:
            self.controller.cleanup()

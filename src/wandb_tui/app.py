import wandb
from textual import work
from textual.app import App
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Header, LoadingIndicator


class WandbTUI(App):
    def __init__(
        self, driver_class=None, css_path=None, watch_css=False, ansi_color=False
    ):
        super().__init__(driver_class, css_path, watch_css, ansi_color)

        wandb.login()
        self.api = wandb.Api()

    def compose(self):
        yield Header()
        with Vertical():
            yield DataTable(id="runs-table")
            yield LoadingIndicator(id="loading")
        yield Footer()

    def on_mount(self):
        table = self.query_one("#runs-table", DataTable)
        table.add_columns("ID", "Name", "State", "Created At")

        # Workerを使って非同期でデータを取得開始
        self.fetch_wandb_data()

    @work(exclusive=True, thread=True)
    def fetch_wandb_data(self) -> None:
        """WandBからデータを段階的に取得してテーブルに追加する"""
        # プロジェクト名を定数として定義
        project_name = "ikura-hamu-institute-of-science-tokyo/Load-aware_Tram-FL"
        per_page_count = 30

        try:
            # 1ページ目: 最初の50件を取得
            self.call_from_thread(self.notify, "Loading Runs ...")

            runs_iterator = self.api.runs(
                project_name, per_page=per_page_count, order="-created_at"
            )

            # 1ページ目のデータを段階的に追加
            count = 0
            total_count = 0
            page_number = 1
            for run in runs_iterator:
                # UIスレッドでテーブルに行を追加
                self.call_from_thread(
                    self._add_table_row,
                    run.id,
                    run.name,
                    run.state,
                    str(run.created_at),
                )
                count += 1
                total_count += 1
                if count >= per_page_count:
                    self.call_from_thread(
                        self.notify,
                        f"Loaded {count} runs. Loading next page...",
                    )
                    count = 0
                    page_number += 1

            # 1ページ目のローディング完了を通知
            self.call_from_thread(self.notify, f"Loaded {total_count} runs.")

        except Exception as e:
            # エラーハンドリング
            self.call_from_thread(
                self.notify, f"Failed to load data: {str(e)}", severity="error"
            )
        finally:
            # ローディングを非表示
            self.call_from_thread(self._hide_loading)

    def _add_table_row(
        self, run_id: str, name: str, state: str, created_at: str
    ) -> None:
        """テーブルに行を追加する（UIスレッド用）"""
        table = self.query_one("#runs-table", DataTable)
        table.add_row(run_id, name, state, created_at)

    def _hide_loading(self) -> None:
        """ローディングインジケーターを非表示にする（UIスレッド用）"""
        loading = self.query_one("#loading", LoadingIndicator)
        loading.display = False

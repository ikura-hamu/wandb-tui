"""Data models and business logic for WandB TUI."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

import wandb.apis.public.runs


@dataclass
class RunData:
    """WandB実行データを表すモデル"""

    id: str
    name: str
    state: str
    created_at: datetime

    @classmethod
    def from_wandb_run(cls, run: wandb.apis.public.runs.Run) -> RunData:
        """WandB RunオブジェクトからRunDataを作成"""
        return cls(
            id=run.id,
            name=run.name,
            state=run.state,
            created_at=run.created_at,
        )


class DataObserver(Protocol):
    """データ変更を観察するためのプロトコル"""

    def on_data_loading_started(self) -> None:
        """データ読み込み開始時に呼ばれる"""
        ...

    def on_data_loaded(self, run_data: RunData) -> None:
        """新しいデータが読み込まれた時に呼ばれる"""
        ...

    def on_data_loading_completed(self, total_count: int) -> None:
        """データ読み込み完了時に呼ばれる"""
        ...

    def on_data_loading_failed(self, error: Exception) -> None:
        """データ読み込み失敗時に呼ばれる"""
        ...


class WandbDataSource(ABC):
    """WandBデータソースの抽象基底クラス"""

    @abstractmethod
    def fetch_runs(
        self,
        project_name: str,
        per_page: int = 30,
        observer: DataObserver | None = None,
    ) -> None:
        """実行データを取得する"""
        ...


class WandbApiDataSource(WandbDataSource):
    """WandB APIを使用したデータソース実装"""

    def __init__(self) -> None:
        self.api = wandb.Api()

    def fetch_runs(
        self,
        project_name: str,
        per_page: int = 30,
        observer: DataObserver | None = None,
    ) -> None:
        """WandB APIから実行データを取得"""
        if observer:
            observer.on_data_loading_started()

        try:
            runs_iterator = self.api.runs(
                project_name, per_page=per_page, order="-created_at"
            )

            count = 0
            for run in runs_iterator:
                run_data = RunData.from_wandb_run(run)
                if observer:
                    observer.on_data_loaded(run_data)
                count += 1

            if observer:
                observer.on_data_loading_completed(count)

        except Exception as e:
            if observer:
                observer.on_data_loading_failed(e)
            raise


class WandbRunsModel:
    """WandB実行データを管理するモデル"""

    def __init__(self, data_source: WandbDataSource) -> None:
        self.data_source = data_source
        self.runs: list[RunData] = []
        self._observers: list[DataObserver] = []

    def add_observer(self, observer: DataObserver) -> None:
        """オブザーバーを追加"""
        self._observers.append(observer)

    def remove_observer(self, observer: DataObserver) -> None:
        """オブザーバーを削除"""
        if observer in self._observers:
            self._observers.remove(observer)

    def _notify_observers(self, method_name: str, *args, **kwargs) -> None:
        """全オブザーバーに通知"""
        for observer in self._observers:
            method = getattr(observer, method_name)
            method(*args, **kwargs)

    # DataObserver実装
    def on_data_loading_started(self) -> None:
        """データ読み込み開始時の処理"""
        for obs in self._observers:
            obs.on_data_loading_started()

    def on_data_loaded(self, run_data: RunData) -> None:
        """新しいデータが読み込まれた時の処理"""
        self.runs.append(run_data)
        for obs in self._observers:
            obs.on_data_loaded(run_data)

    def on_data_loading_completed(self, total_count: int) -> None:
        """データ読み込み完了時の処理"""
        for obs in self._observers:
            obs.on_data_loading_completed(total_count)

    def on_data_loading_failed(self, error: Exception) -> None:
        """データ読み込み失敗時の処理"""
        for obs in self._observers:
            obs.on_data_loading_failed(error)

    def load_runs(self, project_name: str, per_page: int = 30) -> None:
        """実行データを読み込む"""
        self.data_source.fetch_runs(project_name, per_page, self)

    def get_runs(self) -> list[RunData]:
        """全実行データを取得"""
        return self.runs.copy()

    def clear_runs(self) -> None:
        """実行データをクリア"""
        self.runs.clear()

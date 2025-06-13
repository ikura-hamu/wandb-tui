default: format lint type    

lint:
    @ruff check .

format:
    @ruff format .

type:
    @ty check .

dev:
    @textual run --dev --command wandb-tui

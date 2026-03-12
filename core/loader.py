from pathlib import Path
import pandas as pd

class DataRepo:
    def __init__(self, data_dir: Path):
        self.cards = pd.read_csv(data_dir / "Cards.csv", encoding="utf-8-sig")
        self.buildings = pd.read_csv(data_dir / "Buildings.csv", encoding="utf-8-sig")
        self.monuments = pd.read_csv(data_dir / "Monuments.csv", encoding="utf-8-sig")
        self.invasions = pd.read_csv(data_dir / "Invasions.csv", encoding="utf-8-sig")

        self.card_by_id = {r["Card_ID"]: r for _, r in self.cards.iterrows()}
        self.building_by_id = {r["Building_ID"]: r for _, r in self.buildings.iterrows()}
        self.monument_by_id = {r["Monument_ID"]: r for _, r in self.monuments.iterrows()}

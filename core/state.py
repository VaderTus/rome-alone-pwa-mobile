from dataclasses import dataclass, field
from typing import Dict, List, Set

@dataclass
class GameState:
    culture: int = 1
    military: int = 1
    industry: int = 1
    max_resource: int = 9

    rome_occupied: bool = True
    occupied_culture_regions: int = 0
    occupied_industry_regions: int = 0
    total_culture_regions: int = 3
    total_industry_regions: int = 3

    built_buildings: Set[str] = field(default_factory=set)
    monument_progress: Dict[str, int] = field(default_factory=dict)

    deck: List[str] = field(default_factory=list)
    discard: List[str] = field(default_factory=list)

    invasions_resolved: int = 0
    game_lost: bool = False
    turn_count: int = 0

    def occupied_regions(self) -> int:
        return (1 if self.rome_occupied else 0) + self.occupied_culture_regions + self.occupied_industry_regions

    def unoccupied_culture_regions(self) -> int:
        return self.total_culture_regions - self.occupied_culture_regions

    def unoccupied_industry_regions(self) -> int:
        return self.total_industry_regions - self.occupied_industry_regions

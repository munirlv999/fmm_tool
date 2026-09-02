"""Editor modules for FMM Tool."""

from .calculator import mode_kalkulator
from .club_simple import mode_club_simple
from .competition_simple import mode_competition_simple
from .extended import mode_extended
from .history_simple import mode_history_simple
from .language_simple import mode_language_simple
from .name_simple import mode_name_simple
from .nation_simple import mode_nation_simple
from .player_simple import mode_player_simple
from .region_simple import mode_region_simple
from .stadium_simple import mode_stadium_simple

__all__ = [
    'mode_player_simple',
    'mode_nation_simple',
    'mode_club_simple',
    'mode_name_simple',
    'mode_competition_simple',
    'mode_stadium_simple',
    'mode_region_simple',
    'mode_language_simple',
    'mode_history_simple',
    'mode_extended',
    'mode_kalkulator',
]

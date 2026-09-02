"""UI modules for FMM Tool."""

from .console import (
    console, RICH_AVAILABLE,
    print_header, print_success, print_error, print_warning, print_info,
    print_panel, get_input, create_menu_table, create_data_table
)
from .display import (
    show_people_block, show_player_block, show_selected_player_editor,
    show_team_block, show_nation_block, show_club_block, show_competition_block,
    show_stadium_block, show_region_block, get_stat_bar
)

__all__ = [
    'console', 'RICH_AVAILABLE',
    'print_header', 'print_success', 'print_error', 'print_warning', 'print_info',
    'print_panel', 'get_input', 'create_menu_table', 'create_data_table',
    'show_people_block', 'show_player_block', 'show_selected_player_editor',
    'show_team_block', 'show_nation_block', 'show_club_block', 'show_competition_block',
    'show_stadium_block', 'show_region_block', 'get_stat_bar'
]

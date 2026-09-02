"""Registry mapping extended data files to their editors.

Each entry: (title, app_attr, record_class, dirty_key, module_name).
The record classes come from the reverse-engineered format modules; if a
module/class is not yet present the entry is skipped at build time.
"""


def _load_cls(modname, clsname):
    try:
        mod = __import__(f"fmm_tool.core.{modname}", fromlist=[clsname])
        return getattr(mod, clsname)
    except Exception:
        return None


def build(app):
    """Return list of (title, run_fn) for editors whose modules exist."""
    from .extended import _make_editor

    specs = [
        ("🏙️ City Editor", "cities", "city.dat", "CityRec", "geo_format", "cities"),
        ("🌍 Continent Editor", "continents", "continent.dat", "ContinentRec", "geo_format", "continents"),
        ("🏆 Award Editor", "awards", "awards.dat", "AwardRec", "comp_format", "awards"),
        ("⚔️ Rivalries Editor", "rivalries", "rivalries.dat", "RivalryRec", "comp_format", "rivalries"),
        ("👨‍⚖️ Officials Editor", "officials", "officials.dat", "OfficialRec", "staff_format", "officials"),
        ("🧑‍🏫 Coaches Editor", "coaches", "coaches.dat", "CoachRec", "staff_format", "coaches"),
        ("🩺 Physios Editor", "physios", "physios.dat", "PhysioRec", "staff_format", "physios"),
        ("🔭 Scouts Editor", "scouts", "scouts.dat", "ScoutRec", "staff_format", "scouts"),
        ("👥 Non-Players Editor", "non_players", "non_players.dat", "NonPlayerRec", "nonplayer_format", "non_players"),
        ("🔀 Future Transfers", "starting_transfers", "starting_transfers.dat", "FutureTransferRec", "transfer_format", "starting_transfers"),
        ("🎂 Retirements", "starting_retirements", "starting_retirements.dat", "RetirementRec", "transfer_format", "starting_retirements"),
        ("🚫 Starting Bans", "starting_bans", "starting_bans.dat", "StartingBanRec", "transfer_format", "starting_bans"),
        ("🤕 Starting Injuries", "starting_injuries", "starting_injuries.dat", "StartingInjuryRec", "transfer_format", "starting_injuries"),
        ("📄 Starting Contracts", "starting_contracts", "starting_contracts.dat", "StartingContractRec", "transfer_format", "starting_contracts"),
        ("🏦 Starting Loans", "starting_loans", "starting_loans.dat", "StartingLoanRec", "transfer_format", "starting_loans"),
    ]

    entries = []
    for title, attr, fname, clsname, modname, dirty_key in specs:
        cls = _load_cls(modname, clsname)
        if cls is None:
            continue
        run = _make_editor(app, attr, title, cls, dirty_key)
        entries.append((title, run))

    # Player history: whole-file structure, custom editor.
    if app.player_history is not None:
        try:
            from . import history_simple
            entries.append(("📈 Player History", lambda: history_simple.mode_history_simple(app)))
        except Exception:
            pass
    return entries
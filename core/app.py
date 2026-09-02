"""Application state management for FMM Tool."""

import os
from typing import Dict, List, Optional
from .binary import DatList, AlwaysLoadList
from .models import (
    People, Player, NameRec, LanguageRec,
    NationRec, ClubRec, CompetitionRec, StadiumRec, RegionRec
)


class App:
    """Main application state container."""
    
    # Required data files
    REQUIRED_FILES = [
        "people.dat", "players.dat", "first_names.dat", "second_names.dat", "common_names.dat",
        "languages.dat", "nation.dat", "club.dat", "competition.dat", "stadium.dat", "regions.dat"
    ]

    @classmethod
    def get_android_storage_paths(cls) -> List[str]:
        """Get common Android storage paths."""
        paths = []
        # Common Termux/Android paths
        home = os.path.expanduser("~")
        paths.extend([
            "/sdcard",
            "/sdcard/Download",
            "/sdcard/Downloads", 
            "/storage/emulated/0",
            "/storage/emulated/0/Download",
            "/storage/emulated/0/Documents",
            os.path.join(home, "storage", "shared"),
            os.path.join(home, "storage", "downloads"),
        ])
        return [p for p in paths if os.path.exists(p)]

    @classmethod
    def resolve_data_dir(cls, preferred: Optional[str] = None) -> str:
        """Resolve a directory that contains all required .dat files."""
        pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates = [preferred, os.getcwd(), pkg_dir]
        
        # Add Android storage paths
        candidates.extend(cls.get_android_storage_paths())

        checked = []
        for cand in candidates:
            if not cand:
                continue
            full = os.path.abspath(cand)
            if full in checked:
                continue
            checked.append(full)
            if all(os.path.exists(os.path.join(full, fn)) for fn in cls.REQUIRED_FILES):
                return full

        # Not found - return None to trigger user prompt
        return None

    def __init__(self, data_dir: Optional[str] = None):
        resolved = self.resolve_data_dir(data_dir)
        
        # If not found, we need to handle this in main.py
        # For now, raise error with helpful message
        if resolved is None:
            raise FileNotFoundError("DAT_NOT_FOUND")
        
        self.data_dir = resolved

        def p(name: str) -> str:
            return os.path.join(self.data_dir, name)

        # Load all data files
        self.people = DatList.load_i32(p("people.dat"), People.read, pad_u8=True)
        self.players = DatList.load_i32(p("players.dat"), Player.read, pad_u8=False)
        self.first_names = DatList.load_i32(p("first_names.dat"), NameRec.read)
        self.second_names = DatList.load_i32(p("second_names.dat"), NameRec.read)
        self.common_names = DatList.load_i32(p("common_names.dat"), NameRec.read)
        self.languages = DatList.load_i16(p("languages.dat"), LanguageRec.read)
        self.nations = DatList.load_i16(p("nation.dat"), NationRec.read)
        self.clubs = DatList.load_i32(p("club.dat"), ClubRec.read)
        self.competitions = DatList.load_i16(p("competition.dat"), CompetitionRec.read)
        self.stadiums = DatList.load_i16(p("stadium.dat"), StadiumRec.read)
        self.regions = DatList.load_i16(p("regions.dat"), RegionRec.read)
        
        # CRITICAL FIX: Reassign IDs for records that have id == -1 (same as C# source)
        for idx, person in enumerate(self.people.items):
            if person.id == -1:
                person.id = idx
        for idx, club in enumerate(self.clubs.items):
            if club.id == -1:
                club.id = idx
        
        # Load optional always_load files
        self.always_load_male: Optional[AlwaysLoadList] = None
        self.always_load_female: Optional[AlwaysLoadList] = None
        if os.path.exists(p("clubs_to_always_load_male.dat")):
            self.always_load_male = AlwaysLoadList.load(p("clubs_to_always_load_male.dat"))
        if os.path.exists(p("clubs_to_always_load_female.dat")):
            self.always_load_female = AlwaysLoadList.load(p("clubs_to_always_load_female.dat"))

        # ---- Extended data files (optional; reverse-engineered formats) ----
        self._load_extended()
        
        # Build indexes
        self.people_uid_index: Dict[int, int] = {
            p.uid: i for i, p in enumerate(self.people.items)
        }
        self.player_by_id: Dict[int, Player] = {
            pl.id: pl for pl in self.players.items
        }
        
        self.first_by_id = {n.id: n for n in self.first_names.items}
        self.second_by_id = {n.id: n for n in self.second_names.items}
        self.common_by_id = {n.id: n for n in self.common_names.items}
        
        self.nation_by_id = {n.id: n for n in self.nations.items}
        self.nation_name_by_id = {n.id: n.name for n in self.nations.items}
        
        self.lang_by_id = {l.id: l for l in self.languages.items}
        self.stadium_by_id = {s.id: s for s in self.stadiums.items}
        
        self.club_by_eff_id: Dict[int, ClubRec] = {}
        for idx, c in enumerate(self.clubs.items):
            eff = idx if c.id == -1 else c.id
            self.club_by_eff_id[eff] = c
        
        # Name search cache
        self.people_name_cache: Dict[str, List[int]] = {}
        self.rebuild_people_name_cache()

        # Person-detail UID indexes (built once at load for O(1) lookup by the
        # unified PersonDetailModel). See _build_person_indexes for field refs.
        self._build_person_indexes()
        
        # Last search results
        self.last_people_list: List[int] = []
        self.last_nation_list: List[int] = []
        self.last_club_list: List[int] = []
        self.last_competition_list: List[int] = []
        self.last_stadium_list: List[int] = []
        self.last_region_list: List[int] = []
        
        # Current selections
        self.cur_people_idx: Optional[int] = None
        self.cur_nation_idx: Optional[int] = None
        self.cur_club_idx: Optional[int] = None
        self.cur_competition_idx: Optional[int] = None
        self.cur_stadium_idx: Optional[int] = None
        self.cur_region_idx: Optional[int] = None
        
        # Dirty flags for save
        self.dirty_people = False
        self.dirty_players = False
        self.dirty_names_first = False
        self.dirty_names_second = False
        self.dirty_names_common = False
        self.dirty_languages = False
        self.dirty_nations = False
        self.dirty_clubs = False
        self.dirty_competitions = False
        self.dirty_stadiums = False
        self.dirty_regions = False
        self.dirty_always_load_male = False
        self.dirty_always_load_female = False

    def _load_extended(self):
        """Load the extended/optional data files (reverse-engineered formats).

        Every list is stored as a DatList (or None if the file/module is
        absent) so the generic editor + save machinery can handle them
        uniformly. Missing/not-yet-decoded modules are skipped gracefully.
        """
        from .binary import DatList

        def load(name, rec_read, pad=None):
            path = os.path.join(self.data_dir, name)
            if not os.path.exists(path):
                return None
            return DatList.load_i32(path, rec_read, pad=pad)

        # (attr_name, filename, module_path, record_class_name)
        specs = [
            ("cities", "city.dat", "geo_format", "CityRec"),
            ("continents", "continent.dat", "geo_format", "ContinentRec"),
            ("rivalries", "rivalries.dat", "comp_format", "RivalryRec"),
            ("awards", "awards.dat", "comp_format", "AwardRec"),
            ("officials", "officials.dat", "staff_format", "OfficialRec"),
            ("coaches", "coaches.dat", "staff_format", "CoachRec"),
            ("physios", "physios.dat", "staff_format", "PhysioRec"),
            ("scouts", "scouts.dat", "staff_format", "ScoutRec"),
            ("non_players", "non_players.dat", "nonplayer_format", "NonPlayerRec"),
            ("starting_transfers", "starting_transfers.dat", "transfer_format", "FutureTransferRec"),
            ("starting_retirements", "starting_retirements.dat", "transfer_format", "RetirementRec"),
            ("starting_bans", "starting_bans.dat", "transfer_format", "StartingBanRec"),
            ("starting_injuries", "starting_injuries.dat", "transfer_format", "StartingInjuryRec"),
            ("starting_contracts", "starting_contracts.dat", "transfer_format", "StartingContractRec"),
            ("starting_loans", "starting_loans.dat", "transfer_format", "StartingLoanRec"),
            ("player_history", "player_history.dat", "history_format", "PlayerHistoryRec"),
        ]

        # rivalries.dat has a 6-byte pad after the count (3x i16 = 6 bytes, per format spec)
        for attr, fname, modname, clsname in specs:
            try:
                mod = __import__(f"fmm_tool.core.{modname}", fromlist=[clsname])
                rec_cls = getattr(mod, clsname)
            except Exception:
                rec_cls = None
            pad = b"\x00\x00\xb9\x79\x02\x00" if fname == "rivalries.dat" else None
            setattr(self, attr, load(fname, rec_cls.read, pad) if rec_cls else None)
            setattr(self, f"dirty_{attr}", False)

        # player_history.dat has a non-list structure; handle it as a whole file.
        self.player_history = None
        self.dirty_player_history = False
        try:
            from .binary import ReaderEx
            from . import history_format
            ph_path = os.path.join(self.data_dir, "player_history.dat")
            if os.path.exists(ph_path):
                with open(ph_path, "rb") as f:
                    self.player_history = history_format.PlayerHistoryFile.read(ReaderEx(f))
        except Exception:
            self.player_history = None

    def _build_person_indexes(self):
        """Build UID (or array-index) -> record indexes for the unified
        PersonDetailModel, so a person's full footprint (contract, loan,
        injury, ban, transfer, retirement, history, staff, non-player) can
        be looked up in O(1) instead of scanning every list.

        Multi-value sources (loans/injuries/bans/transfers/history) map to
        lists; single-value sources map to the record directly.

        Note on person-ref types (from core/squad_ops comments):
          - most extended files key off person UID via ``person_id``/``uid``;
          - officials uses a real person UID (``person_uid``);
          - coaches/physios/scouts ``id`` stores the person ARRAY INDEX, NOT
            a UID — so the staff reverse index maps people-array-index -> rec.
        Indexes are built once at load. Existing editors mutate record objects
        in place (same objects the index points at), so edits are reflected
        without rebuilding.
        """
        def by_uid(lst, fname):
            """Map uid -> list[rec] for records carrying a person uid."""
            d: Dict[int, list] = {}
            if lst is None:
                return d
            for rec in lst.items:
                uid = getattr(rec, fname, None)
                if uid is None:
                    continue
                d.setdefault(uid, []).append(rec)
            return d

        def first_by_uid(lst, fname):
            """Map uid -> first rec (single-record-per-person sources)."""
            d: Dict[int, object] = {}
            if lst is None:
                return d
            for rec in lst.items:
                uid = getattr(rec, fname, None)
                if uid is None or uid in d:
                    continue
                d[uid] = rec
            return d

        self.contracts_by_uid   = first_by_uid(self.starting_contracts,   "person_id")
        self.loans_by_uid       = by_uid(self.starting_loans,             "person_id")
        self.injuries_by_uid    = by_uid(self.starting_injuries,          "person_id")
        self.bans_by_uid        = by_uid(self.starting_bans,              "person_id")
        self.transfers_by_uid   = by_uid(self.starting_transfers,         "person_id")
        self.retirements_by_uid = first_by_uid(self.starting_retirements, "person_id")
        self.nonplayers_by_uid  = first_by_uid(self.non_players,          "uid")
        self.officials_by_uid   = first_by_uid(self.officials,           "person_uid")
        # staff keyed by people-array-index (their `id` field = person index)
        self.coaches_by_idx = {r.id: r for r in (self.coaches.items if self.coaches else [])}
        self.physios_by_idx = {r.id: r for r in (self.physios.items if self.physios else [])}
        self.scouts_by_idx  = {r.id: r for r in (self.scouts.items  if self.scouts  else [])}
        # history: person_uid -> PlayerHistory
        self.history_by_uid: Dict[int, list] = {}
        if self.player_history:
            for ph in self.player_history.players:
                self.history_by_uid.setdefault(ph.person_uid, []).append(ph)

    def rebuild_people_name_cache(self):
        """Rebuild people name search cache."""
        from ..utils.helpers import lower_norm
        self.people_name_cache.clear()
        for idx, p in enumerate(self.people.items):
            nm = lower_norm(self.people_display_name(p))
            self.people_name_cache.setdefault(nm, []).append(idx)
    
    def name_first(self, id_: int) -> str:
        """Get first name by ID."""
        n = self.first_by_id.get(id_)
        return n.value if n else f"#{id_}"
    
    def name_second(self, id_: int) -> str:
        """Get last name by ID."""
        n = self.second_by_id.get(id_)
        return n.value if n else f"#{id_}"
    
    def name_common(self, id_: int) -> str:
        """Get common name by ID."""
        n = self.common_by_id.get(id_)
        return n.value if n else f"#{id_}"
    
    def people_display_name(self, p: People) -> str:
        """Get display name for a person."""
        from ..utils.helpers import norm_space
        last = self.name_second(p.last_name_id)
        if p.common_name_id != -1:
            common = self.name_common(p.common_name_id)
            return norm_space(f"{common} {last}")
        first = self.name_first(p.first_name_id)
        return norm_space(f"{first} {last}")
    
    def people_name_by_uid(self, uid: int) -> str:
        """Get person name by UID."""
        idx = self.people_uid_index.get(uid)
        if idx is None:
            return "-"
        return self.people_display_name(self.people.items[idx])
    
    def nation_name(self, nation_id: int) -> str:
        """Get nation name by ID."""
        return self.nation_name_by_id.get(nation_id, "-")
    
    def lang_name(self, lang_id: int) -> str:
        """Get language name by ID."""
        lr = self.lang_by_id.get(lang_id)
        return lr.name if lr else "-"
    
    def stadium_name(self, stadium_id: int) -> str:
        """Get stadium name by ID."""
        st = self.stadium_by_id.get(stadium_id)
        return st.name if st else "-"
    
    def club_eff_id_of_index(self, idx: int) -> int:
        """Get effective club ID from index."""
        c = self.clubs.items[idx]
        return idx if c.id == -1 else c.id
    
    def club_name_from_people(self, p: People) -> str:
        """Get club name from people record."""
        c = self.club_by_eff_id.get(p.club_id)
        if not c:
            return "-"
        return c.full_name
    
    def save_all_dirty(self):
        """Save all modified data files."""
        if self.dirty_people:
            self.people.save_overwrite(lambda it, w: it.write(w))
            self.dirty_people = False
        
        if self.dirty_players:
            self.players.save_overwrite(lambda it, w: it.write(w))
            self.dirty_players = False
        
        if self.dirty_names_first:
            self.first_names.save_overwrite(lambda it, w: it.write(w))
            self.dirty_names_first = False
        
        if self.dirty_names_second:
            self.second_names.save_overwrite(lambda it, w: it.write(w))
            self.dirty_names_second = False
        
        if self.dirty_names_common:
            self.common_names.save_overwrite(lambda it, w: it.write(w))
            self.dirty_names_common = False
        
        if self.dirty_languages:
            self.languages.save_overwrite(lambda it, w: it.write(w))
            self.dirty_languages = False
        
        if self.dirty_nations:
            self.nations.save_overwrite(lambda it, w: it.write(w))
            self.dirty_nations = False
        
        if self.dirty_clubs:
            self.clubs.save_overwrite(lambda it, w: it.write(w))
            self.dirty_clubs = False

        if self.dirty_competitions:
            self.competitions.save_overwrite(lambda it, w: it.write(w))
            self.dirty_competitions = False
        
        if self.dirty_stadiums:
            self.stadiums.save_overwrite(lambda it, w: it.write(w))
            self.dirty_stadiums = False
        
        if self.dirty_regions:
            self.regions.save_overwrite(lambda it, w: it.write(w))
            self.dirty_regions = False
        
        if self.dirty_always_load_male and self.always_load_male is not None:
            self.always_load_male.save_overwrite()
            self.dirty_always_load_male = False

        if self.dirty_always_load_female and self.always_load_female is not None:
            self.always_load_female.save_overwrite()
            self.dirty_always_load_female = False

        # Extended files
        self._save_extended()

    def _save_extended(self):
        """Save any dirty extended data files (byte-identical writers)."""
        specs = [
            ("cities", "geo_format", "CityRec"),
            ("continents", "geo_format", "ContinentRec"),
            ("rivalries", "comp_format", "RivalryRec"),
            ("awards", "comp_format", "AwardRec"),
            ("officials", "staff_format", "OfficialRec"),
            ("coaches", "staff_format", "CoachRec"),
            ("physios", "staff_format", "PhysioRec"),
            ("scouts", "staff_format", "ScoutRec"),
            ("non_players", "nonplayer_format", "NonPlayerRec"),
            ("starting_transfers", "transfer_format", "FutureTransferRec"),
            ("starting_retirements", "transfer_format", "RetirementRec"),
            ("starting_bans", "transfer_format", "StartingBanRec"),
            ("starting_injuries", "transfer_format", "StartingInjuryRec"),
            ("starting_contracts", "transfer_format", "StartingContractRec"),
            ("starting_loans", "transfer_format", "StartingLoanRec"),
            ("player_history", "history_format", "PlayerHistoryRec"),
        ]
        for attr, modname, clsname in specs:
            dat = getattr(self, attr, None)
            if dat is None or not getattr(self, f"dirty_{attr}", False):
                continue
            try:
                mod = __import__(f"fmm_tool.core.{modname}", fromlist=[clsname])
                cls = getattr(mod, clsname)
                write_fn = cls.write
                # Support both instance method (write(self, w)) and static
                # method (write(self, w) called as cls.write(rec, w)).
                dat.save_overwrite(lambda it, w, write_fn=write_fn: write_fn(it, w))
                setattr(self, f"dirty_{attr}", False)
            except Exception:
                # If a module/class is missing, leave dirty flag set so it is
                # retried rather than silently dropping the change.
                pass

        # player_history: whole-file save
        if getattr(self, "dirty_player_history", False) and self.player_history is not None:
            try:
                from .binary import atomic_overwrite
                from . import history_format
                atomic_overwrite(
                    os.path.join(self.data_dir, "player_history.dat"),
                    lambda f: self.player_history.write(history_format.WriterEx(f))
                )
                self.dirty_player_history = False
            except Exception:
                pass
    
    def update_nation_indexes(self):
        """Update nation indexes after modification."""
        self.nation_by_id = {x.id: x for x in self.nations.items}
        self.nation_name_by_id = {x.id: x.name for x in self.nations.items}
    
    def update_stadium_indexes(self):
        """Update stadium indexes after modification."""
        self.stadium_by_id = {s.id: s for s in self.stadiums.items}

"""Data models for FMM Tool."""

import struct
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from .binary import ReaderEx, WriterEx


# Fixed 82-byte Player layout (no variable parts) — one bulk read + unpack
# instead of ~50 separate read_u8/read_i16/read_i32 syscalls per record.
# Matches the sequential field order in Player.read below:
#   ii  = id, uid
#   B*51 = 27 attrs + 7 gk attrs + 15 pos attrs + leftfoot + rightfoot
#   hhhhhBh = ca, pa, home, cur, world, intl, unk1
#   BBhh  = squad, pref, height, weight
#   i     = unknown2
_PLAYER_FMT = "<ii" + "B" * 51 + "hhhhhBh" + "BBhh" + "i"
_PLAYER_SIZE = struct.calcsize(_PLAYER_FMT)


@dataclass
class Relationship:
    """People relationship record."""
    level: int
    type: int
    unknown: int
    uid: int
    reason: int
    
    @staticmethod
    def read(r: ReaderEx) -> "Relationship":
        return Relationship(
            r.read_u8(), r.read_u8(), r.read_u8(),
            r.read_i32(), r.read_u8()
        )
    
    def write(self, w: WriterEx):
        w.write_u8(self.level)
        w.write_u8(self.type)
        w.write_u8(self.unknown)
        w.write_i32(self.uid)
        w.write_u8(self.reason)


@dataclass
class People:
    """People/Person record (non-player data)."""
    id: int
    uid: int
    first_name_id: int
    last_name_id: int
    common_name_id: int
    dob_raw: int
    nation_id: int
    other_nationalities: List[int]
    ethnicity: int
    ptype: int
    national_caps: int
    national_goals: int
    national_u21_caps: int
    national_u21_goals: int
    club_id: int
    joined_raw: int
    adaptability: int
    ambition: int
    controversy: int
    loyality: int
    pressure: int
    professionalism: int
    sportmanship: int
    temperament: int
    player_id: int
    default_languages: List[Tuple[int, int]]
    other_languages: List[Tuple[int, int]]
    relationships: List[Relationship]
    unknown1: int
    unknown_date: int
    unknown3: int
    unknown6b: int
    unknown6c: int
    unknown6d: int
    unknown6e: int
    unknown6f: Optional[int]
    unknown7: int
    unknown8: int
    unknown9: Optional[int]
    unknown10: Optional[int]
    unknown21: int
    
    @staticmethod
    def read(r: ReaderEx) -> "People":
        pid = r.read_i32()
        uid = r.read_i32()
        first = r.read_i32()
        last = r.read_i32()
        common = r.read_i32()
        dob_raw = r.read_i32()
        
        nation = r.read_i16()
        oc = r.read_i16()
        others = [r.read_i16() for _ in range(oc)]
        
        ethnicity = r.read_u8()
        unknown1 = r.read_i32()
        ptype = r.read_u8()
        unknown_date = r.read_i32()
        
        nat_caps = r.read_i16()
        nat_goals = r.read_i16()
        u21_caps = r.read_u8()
        u21_goals = r.read_u8()
        
        club_id = r.read_i32()
        joined_raw = r.read_i32()
        
        unknown3 = r.read_i16()
        
        adaptability = r.read_u8()
        ambition = r.read_u8()
        controversy = r.read_u8()
        loyality = r.read_u8()
        pressure = r.read_u8()
        professionalism = r.read_u8()
        sportmanship = r.read_u8()
        temperament = r.read_u8()
        
        player_id = r.read_i32()
        u6b = r.read_i32()
        u6c = r.read_i32()
        u6d = r.read_i32()
        u6e = r.read_i32()
        
        unknown6f = None
        pos = r.tell()
        maybe = r.read_i32()
        if maybe == -1:
            unknown6f = -1
        else:
            r.seek(pos)
        
        unknown7 = r.read_u8()
        unknown8 = r.read_u8()
        
        unknown9 = None
        unknown10 = None
        if r.peek_i16() <= 0:
            unknown9 = r.read_i32()
            if unknown9 == -1:
                unknown10 = r.read_i16()
        
        dcnt = r.read_u8()
        dlangs = [(r.read_i16(), r.read_u8()) for _ in range(dcnt)]
        
        ocnt = r.read_u8()
        olangs = [(r.read_i16(), r.read_u8()) for _ in range(ocnt)]
        
        rcnt = r.read_u8()
        rels = [Relationship.read(r) for _ in range(rcnt)]
        
        unknown21 = r.read_u8()
        
        return People(
            id=pid, uid=uid,
            first_name_id=first, last_name_id=last, common_name_id=common,
            dob_raw=dob_raw,
            nation_id=nation, other_nationalities=others,
            ethnicity=ethnicity, ptype=ptype,
            national_caps=nat_caps, national_goals=nat_goals,
            national_u21_caps=u21_caps, national_u21_goals=u21_goals,
            club_id=club_id, joined_raw=joined_raw,
            adaptability=adaptability, ambition=ambition,
            controversy=controversy, loyality=loyality,
            pressure=pressure, professionalism=professionalism,
            sportmanship=sportmanship, temperament=temperament,
            player_id=player_id,
            default_languages=dlangs, other_languages=olangs, relationships=rels,
            unknown1=unknown1, unknown_date=unknown_date, unknown3=unknown3,
            unknown6b=u6b, unknown6c=u6c, unknown6d=u6d, unknown6e=u6e, unknown6f=unknown6f,
            unknown7=unknown7, unknown8=unknown8, unknown9=unknown9, unknown10=unknown10,
            unknown21=unknown21
        )
    
    def write(self, w: WriterEx):
        w.write_i32(self.id)
        w.write_i32(self.uid)
        w.write_i32(self.first_name_id)
        w.write_i32(self.last_name_id)
        w.write_i32(self.common_name_id)
        w.write_i32(self.dob_raw)
        
        w.write_i16(self.nation_id)
        w.write_i16(len(self.other_nationalities))
        for n in self.other_nationalities:
            w.write_i16(n)
        
        w.write_u8(self.ethnicity)
        w.write_i32(self.unknown1)
        w.write_u8(self.ptype)
        w.write_i32(self.unknown_date)
        
        w.write_i16(self.national_caps)
        w.write_i16(self.national_goals)
        w.write_u8(self.national_u21_caps)
        w.write_u8(self.national_u21_goals)
        
        w.write_i32(self.club_id)
        w.write_i32(self.joined_raw)
        
        w.write_i16(self.unknown3)
        
        for v in (self.adaptability, self.ambition, self.controversy, self.loyality,
                  self.pressure, self.professionalism, self.sportmanship, self.temperament):
            w.write_u8(v)
        
        w.write_i32(self.player_id)
        for v in (self.unknown6b, self.unknown6c, self.unknown6d, self.unknown6e):
            w.write_i32(v)
        
        if self.unknown6f is not None:
            w.write_i32(self.unknown6f)
        
        w.write_u8(self.unknown7)
        w.write_u8(self.unknown8)
        
        if self.unknown9 is not None:
            w.write_i32(self.unknown9)
        if self.unknown10 is not None:
            w.write_i16(self.unknown10)
        
        w.write_u8(len(self.default_languages))
        for i, p in self.default_languages:
            w.write_i16(i)
            w.write_u8(p)
        
        w.write_u8(len(self.other_languages))
        for i, p in self.other_languages:
            w.write_i16(i)
            w.write_u8(p)
        
        w.write_u8(len(self.relationships))
        for rel in self.relationships:
            rel.write(w)
        
        w.write_u8(self.unknown21)


@dataclass
class Player:
    """Player attributes record."""
    id: int
    uid: int
    crossing: int
    dribbling: int
    tackling: int
    finishing: int
    longshot: int
    heading: int
    jumping: int
    passing: int
    decision: int
    unselfishness: int
    pace: int
    strength: int
    stamina: int
    technique: int
    consistency: int
    aggression: int
    bigmatch: int
    injuryprone: int
    leadership: int
    versatility: int
    setpieces: int
    penalty: int
    creativity: int
    movement: int
    positioning: int
    workrate: int
    flair: int
    handling: int
    kicking: int
    agility: int
    aerial: int
    reflexes: int
    communication: int
    throwing: int
    gk: int
    lib: int
    lb: int
    cb: int
    rb: int
    dm: int
    lm: int
    cm: int
    rm: int
    lw: int
    am: int
    rw: int
    cf: int
    lwb: int
    rwb: int
    leftfoot: int
    rightfoot: int
    ca: int
    pa: int
    home_rep: int
    current_rep: int
    world_rep: int
    international_retirement: int
    squad_number: int
    preferred_squad_number: int
    height: int
    weight: int
    unknown1: int
    unknown2: int
    
    @staticmethod
    def read(r: ReaderEx) -> "Player":
        # Bulk unpack of the fixed 82-byte layout (one read_bytes + one
        # struct.unpack) instead of ~50 individual read_* syscalls. At 108k
        # records this cuts ~5.4M read calls down to ~216k.
        fields = struct.unpack(_PLAYER_FMT, r.read_bytes(_PLAYER_SIZE))
        pid = fields[0]
        uid = fields[1]
        vals = fields[2:29]            # 27 attrs
        gkvals = fields[29:36]         # 7 gk attrs
        posvals = fields[36:51]        # 15 pos attrs
        leftfoot = fields[51]
        rightfoot = fields[52]
        ca = fields[53]
        pa = fields[54]
        home = fields[55]
        cur = fields[56]
        world = fields[57]
        intl = fields[58]
        unk1 = fields[59]
        squad = fields[60]
        pref = fields[61]
        height = fields[62]
        weight = fields[63]
        unk2 = fields[64]
        
        return Player(
            id=pid, uid=uid,
            crossing=vals[0], dribbling=vals[1], tackling=vals[2], finishing=vals[3],
            longshot=vals[4], heading=vals[5], jumping=vals[6], passing=vals[7],
            decision=vals[8], unselfishness=vals[9], pace=vals[10], strength=vals[11],
            stamina=vals[12], technique=vals[13], consistency=vals[14], aggression=vals[15],
            bigmatch=vals[16], injuryprone=vals[17], leadership=vals[18], versatility=vals[19],
            setpieces=vals[20], penalty=vals[21], creativity=vals[22], movement=vals[23],
            positioning=vals[24], workrate=vals[25], flair=vals[26],
            handling=gkvals[0], kicking=gkvals[1], agility=gkvals[2], aerial=gkvals[3],
            reflexes=gkvals[4], communication=gkvals[5], throwing=gkvals[6],
            gk=posvals[0], lib=posvals[1], lb=posvals[2], cb=posvals[3], rb=posvals[4],
            dm=posvals[5], lm=posvals[6], cm=posvals[7], rm=posvals[8], lw=posvals[9],
            am=posvals[10], rw=posvals[11], cf=posvals[12], lwb=posvals[13], rwb=posvals[14],
            leftfoot=leftfoot, rightfoot=rightfoot,
            ca=ca, pa=pa,
            home_rep=home, current_rep=cur, world_rep=world,
            international_retirement=intl,
            unknown1=unk1, squad_number=squad, preferred_squad_number=pref,
            height=height, weight=weight,
            unknown2=unk2
        )
    
    def write(self, w: WriterEx):
        w.write_i32(self.id)
        w.write_i32(self.uid)
        vals = [
            self.crossing, self.dribbling, self.tackling, self.finishing, self.longshot,
            self.heading, self.jumping, self.passing, self.decision, self.unselfishness,
            self.pace, self.strength, self.stamina, self.technique, self.consistency,
            self.aggression, self.bigmatch, self.injuryprone, self.leadership, self.versatility,
            self.setpieces, self.penalty, self.creativity, self.movement, self.positioning,
            self.workrate, self.flair
        ]
        for v in vals:
            w.write_u8(v)
        for v in [self.handling, self.kicking, self.agility, self.aerial, self.reflexes, 
                  self.communication, self.throwing]:
            w.write_u8(v)
        for v in [self.gk, self.lib, self.lb, self.cb, self.rb, self.dm, self.lm, 
                  self.cm, self.rm, self.lw, self.am, self.rw, self.cf, self.lwb, self.rwb]:
            w.write_u8(v)
        w.write_u8(self.leftfoot)
        w.write_u8(self.rightfoot)
        w.write_i16(self.ca)
        w.write_i16(self.pa)
        w.write_i16(self.home_rep)
        w.write_i16(self.current_rep)
        w.write_i16(self.world_rep)
        w.write_u8(self.international_retirement)
        w.write_i16(self.unknown1)
        w.write_u8(self.squad_number)
        w.write_u8(self.preferred_squad_number)
        w.write_i16(self.height)
        w.write_i16(self.weight)
        w.write_i32(self.unknown2)


@dataclass
class NameRec:
    """Name record (first/second/common names)."""
    unknown1: int
    id: int
    gender: int
    nation_uid: int
    unknown2: int
    unknown3: int
    value: str
    
    @staticmethod
    def read(r: ReaderEx) -> "NameRec":
        return NameRec(
            unknown1=r.read_i32(),
            id=r.read_i32(),
            gender=r.read_u8(),
            nation_uid=r.read_i32(),
            unknown2=r.read_i16(),
            unknown3=r.read_u8(),
            value=r.read_string()
        )
    
    def write(self, w: WriterEx):
        w.write_i32(self.unknown1)
        w.write_i32(self.id)
        w.write_u8(self.gender)
        w.write_i32(self.nation_uid)
        w.write_i16(self.unknown2)
        w.write_u8(self.unknown3)
        w.write_string(self.value)


@dataclass
class LanguageRec:
    """Language record."""
    id: int
    uid: int
    name: str
    other_name: str
    nation_id: int
    difficulty: int
    
    @staticmethod
    def read(r: ReaderEx) -> "LanguageRec":
        return LanguageRec(
            id=r.read_i16(),
            uid=r.read_i32(),
            name=r.read_string(),
            other_name=r.read_string(),
            nation_id=r.read_i16(),
            difficulty=r.read_u8()
        )
    
    def write(self, w: WriterEx):
        w.write_i16(self.id)
        w.write_i32(self.uid)
        w.write_string(self.name)
        w.write_string(self.other_name)
        w.write_i16(self.nation_id)
        w.write_u8(self.difficulty)


@dataclass
class NationalTeamRec:
    """National team sub-record."""
    color1: int
    color2: int
    color3: int
    color4: int
    game_importance: int
    rival_id: int
    unknown4: int
    is_ranked: bool
    ranking: int
    points: int
    unknown5: int
    coefficients: List[float]
    unknown6: bytes
    
    @staticmethod
    def read(r: ReaderEx) -> "NationalTeamRec":
        c1 = r.read_i16()
        c2 = r.read_i16()
        c3 = r.read_i16()
        c4 = r.read_i16()
        gi = r.read_u8()
        rival = r.read_i16()
        u4 = r.read_u8()
        ranked = r.read_bool()
        ranking = r.read_i16()
        points = r.read_i16()
        u5 = r.read_i16()
        cnt = r.read_u8()
        coeff = [r.read_f32() for _ in range(cnt)]
        u6 = r.read_bytes(11)
        return NationalTeamRec(c1, c2, c3, c4, gi, rival, u4, ranked, ranking, points, u5, coeff, u6)
    
    def write(self, w: WriterEx):
        w.write_i16(self.color1)
        w.write_i16(self.color2)
        w.write_i16(self.color3)
        w.write_i16(self.color4)
        w.write_u8(self.game_importance)
        w.write_i16(self.rival_id)
        w.write_u8(self.unknown4)
        w.write_bool(self.is_ranked)
        w.write_i16(self.ranking)
        w.write_i16(self.points)
        w.write_i16(self.unknown5)
        w.write_u8(len(self.coefficients))
        for f in self.coefficients:
            w.write_f32(f)
        w.write_bytes(self.unknown6 if self.unknown6 else b"\x00" * 11)


@dataclass
class NationRec:
    """Nation record."""
    uid: int
    id: int
    name: str
    terminator1: int
    nationality: str
    terminator2: int
    codename: str
    continent_id: int
    capital_id: int
    stadium_id: int
    state_dev: int
    unknown1: int
    unknown2: int
    region: int
    unknown3: int
    languages: List[Tuple[int, int]]
    has_male_team: bool
    male_team: Optional[NationalTeamRec]
    has_female_team: bool
    female_team: Optional[NationalTeamRec]
    
    @staticmethod
    def read(r: ReaderEx) -> "NationRec":
        uid = r.read_i32()
        nid = r.read_i16()
        
        name = r.read_string()
        t1 = r.read_u8()
        
        nat = r.read_string()
        t2 = r.read_u8()
        
        codename = r.read_string()
        
        continent = r.read_i16()
        capital = r.read_i16()
        stadium = r.read_i16()
        
        state_dev = r.read_u8()
        unknown1 = r.read_u8()
        unknown2 = r.read_i16()
        region = r.read_i16()
        unknown3 = r.read_u8()
        
        lcnt = r.read_u8()
        langs = [(r.read_i16(), r.read_u8()) for _ in range(lcnt)]
        
        has_male = r.read_bool()
        male = NationalTeamRec.read(r) if has_male else None
        
        has_female = r.read_bool()
        female = NationalTeamRec.read(r) if has_female else None
        
        return NationRec(
            uid=uid, id=nid,
            name=name, terminator1=t1,
            nationality=nat, terminator2=t2,
            codename=codename,
            continent_id=continent, capital_id=capital, stadium_id=stadium,
            state_dev=state_dev, unknown1=unknown1, unknown2=unknown2,
            region=region, unknown3=unknown3,
            languages=langs,
            has_male_team=has_male, male_team=male,
            has_female_team=has_female, female_team=female
        )
    
    def write(self, w: WriterEx):
        w.write_i32(self.uid)
        w.write_i16(self.id)
        
        w.write_string(self.name)
        w.write_u8(self.terminator1)
        
        w.write_string(self.nationality)
        w.write_u8(self.terminator2)
        
        w.write_string(self.codename)
        
        w.write_i16(self.continent_id)
        w.write_i16(self.capital_id)
        w.write_i16(self.stadium_id)
        
        w.write_u8(self.state_dev)
        w.write_u8(self.unknown1)
        w.write_i16(self.unknown2)
        w.write_i16(self.region)
        w.write_u8(self.unknown3)
        
        w.write_u8(len(self.languages))
        for lid, prof in self.languages:
            w.write_i16(lid)
            w.write_u8(prof)
        
        w.write_bool(self.has_male_team)
        if self.has_male_team and self.male_team is not None:
            self.male_team.write(w)
        
        w.write_bool(self.has_female_team)
        if self.has_female_team and self.female_team is not None:
            self.female_team.write(w)


@dataclass
class KitRec:
    """Club kit record."""
    unknown1: int
    unknown2: int
    colors: List[int]
    
    @staticmethod
    def read(r: ReaderEx) -> "KitRec":
        u1 = r.read_u8()
        u2 = r.read_u8()
        cols = [r.read_u16() for _ in range(10)]
        return KitRec(u1, u2, cols)
    
    def write(self, w: WriterEx):
        w.write_u8(self.unknown1)
        w.write_u8(self.unknown2)
        for c in self.colors:
            w.write_u16(c)


@dataclass
class AffiliateRec:
    """Club affiliate relationship record."""
    unknown1: int
    club1_id: int
    club2_id: int
    start_day: int
    start_year: int
    end_day: int
    end_year: int
    unknown2: int
    
    @staticmethod
    def read(r: ReaderEx) -> "AffiliateRec":
        return AffiliateRec(
            unknown1=r.read_i32(),
            club1_id=r.read_i32(),
            club2_id=r.read_i32(),
            start_day=r.read_i16(),
            start_year=r.read_i16(),
            end_day=r.read_i16(),
            end_year=r.read_i16(),
            unknown2=r.read_u8()
        )
    
    def write(self, w: WriterEx):
        w.write_i32(self.unknown1)
        w.write_i32(self.club1_id)
        w.write_i32(self.club2_id)
        w.write_i16(self.start_day)
        w.write_i16(self.start_year)
        w.write_i16(self.end_day)
        w.write_i16(self.end_year)
        w.write_u8(self.unknown2)


@dataclass
class ClubRec:
    """Club record."""
    id: int
    uid: int
    full_name: str
    full_term: int
    short_name: str
    short_term: int
    six_letter: str
    three_letter: str
    based_id: int
    nation_id: int
    colors6: List[int]
    kits6: List[KitRec]
    status: int
    academy: int
    facilities: int
    att_avg: int
    att_min: int
    att_max: int
    reserves: int
    league_id: int
    other_division: int
    other_last_pos: int
    stadium: int
    last_league: int
    unknown4flag: bool
    unknown4: bytes
    unknown5: bytes
    league_pos: int
    reputation: int
    unknown6: bytes
    affiliates: List[AffiliateRec]
    players: List[int]
    unknown7: List[int]
    main_club: int
    ctype: int
    unknown8: bytes
    unknown9: bytes
    gender: int
    
    @staticmethod
    def read(r: ReaderEx) -> "ClubRec":
        cid = r.read_i32()
        uid = r.read_i32()
        full = r.read_string()
        full_term = r.read_u8()
        short = r.read_string()
        short_term = r.read_u8()
        six = r.read_string()
        three = r.read_string()
        based = r.read_i16()
        nation = r.read_i16()
        colors6 = [r.read_u16() for _ in range(6)]
        kits6 = [KitRec.read(r) for _ in range(6)]
        status = r.read_u8()
        academy = r.read_u8()
        facilities = r.read_u8()
        att_avg = r.read_i16()
        att_min = r.read_i16()
        att_max = r.read_i16()
        reserves = r.read_u8()
        league_id = r.read_i16()
        
        other_division = r.read_i16()
        other_last_pos = r.read_u8()
        stadium = r.read_i16()
        last_league = r.read_i16()
        
        u4flag = r.read_bool()
        u4 = r.read_bytes(68) if u4flag else b""
        u5_len = r.read_i32()
        u5 = r.read_bytes(u5_len) if u5_len > 0 else b""
        
        league_pos = r.read_u8()
        rep = r.read_i16()
        u6 = r.read_bytes(20)
        
        aff_count = r.read_i16()
        affiliates = [AffiliateRec.read(r) for _ in range(aff_count)]
        
        pcount = r.read_i16()
        players = [r.read_i32() for _ in range(pcount)]
        
        unknown7 = [r.read_i32() for _ in range(11)]
        
        main = r.read_i32()
        ctype = r.read_u8()
        
        u8 = r.read_bytes(34)
        u9 = r.read_bytes(41)
        
        gender = r.read_u8()
        
        return ClubRec(
            id=cid, uid=uid,
            full_name=full, full_term=full_term,
            short_name=short, short_term=short_term,
            six_letter=six, three_letter=three,
            based_id=based, nation_id=nation,
            colors6=colors6, kits6=kits6,
            status=status, academy=academy, facilities=facilities,
            att_avg=att_avg, att_min=att_min, att_max=att_max,
            reserves=reserves, league_id=league_id,
            other_division=other_division, other_last_pos=other_last_pos,
            stadium=stadium, last_league=last_league,
            unknown4flag=u4flag, unknown4=u4,
            unknown5=u5,
            league_pos=league_pos, reputation=rep,
            unknown6=u6,
            affiliates=affiliates,
            players=players,
            unknown7=unknown7,
            main_club=main,
            ctype=ctype,
            unknown8=u8, unknown9=u9,
            gender=gender
        )
    
    def write(self, w: WriterEx):
        w.write_i32(self.id)
        w.write_i32(self.uid)
        w.write_string(self.full_name)
        w.write_u8(self.full_term)
        w.write_string(self.short_name)
        w.write_u8(self.short_term)
        w.write_string(self.six_letter)
        w.write_string(self.three_letter)
        w.write_i16(self.based_id)
        w.write_i16(self.nation_id)
        for c in self.colors6:
            w.write_u16(c)
        for k in self.kits6:
            k.write(w)
        w.write_u8(self.status)
        w.write_u8(self.academy)
        w.write_u8(self.facilities)
        w.write_i16(self.att_avg)
        w.write_i16(self.att_min)
        w.write_i16(self.att_max)
        w.write_u8(self.reserves)
        w.write_i16(self.league_id)
        
        w.write_i16(self.other_division)
        w.write_u8(self.other_last_pos)
        w.write_i16(self.stadium)
        w.write_i16(self.last_league)
        
        w.write_bool(self.unknown4flag)
        if self.unknown4flag:
            w.write_bytes(self.unknown4)
        
        w.write_i32(len(self.unknown5))
        if self.unknown5:
            w.write_bytes(self.unknown5)
        
        w.write_u8(self.league_pos)
        w.write_i16(self.reputation)
        w.write_bytes(self.unknown6 if self.unknown6 else b"\x00" * 20)
        
        w.write_i16(len(self.affiliates))
        for a in self.affiliates:
            a.write(w)
        
        w.write_i16(len(self.players))
        for p in self.players:
            w.write_i32(p)
        
        for u in self.unknown7:
            w.write_i32(u)
        
        w.write_i32(self.main_club)
        w.write_u8(self.ctype)
        
        w.write_bytes(self.unknown8 if self.unknown8 else b"\x00" * 34)
        w.write_bytes(self.unknown9 if self.unknown9 else b"\x00" * 41)
        
        w.write_u8(self.gender)


@dataclass
class CompetitionRec:
    """Competition record."""
    id: int
    uid: int
    full_name: str
    full_term: int
    short_name: str
    short_term: int
    code_name: str
    ctype: int
    continent_id: int
    nation_id: int
    fg_color: int
    bg_color: int
    reputation: int
    level: int
    parent_competition_id: int
    qualifiers: List[bytes]
    rank1: int
    rank2: int
    rank3: int
    year1: int
    year2: int
    year3: int
    unknown3: int
    is_women: bool

    @staticmethod
    def read(r: ReaderEx) -> "CompetitionRec":
        cid = r.read_i16()
        uid = r.read_i32()
        full = r.read_string()
        full_term = r.read_u8()
        short = r.read_string()
        short_term = r.read_u8()
        code = r.read_string()
        ctype = r.read_u8()
        continent = r.read_i16()
        nation = r.read_i16()
        fg = r.read_u16()
        bg = r.read_u16()
        rep = r.read_i16()
        level = r.read_u8()
        parent = r.read_i16()
        q_count = r.read_i32()
        qualifiers = [r.read_bytes(8) for _ in range(q_count)]
        rank1 = r.read_i32()
        rank2 = r.read_i32()
        rank3 = r.read_i32()
        year1 = r.read_i16()
        year2 = r.read_i16()
        year3 = r.read_i16()
        unknown3 = r.read_u8()
        is_women = r.read_bool()
        return CompetitionRec(
            id=cid, uid=uid,
            full_name=full, full_term=full_term,
            short_name=short, short_term=short_term,
            code_name=code,
            ctype=ctype,
            continent_id=continent, nation_id=nation,
            fg_color=fg, bg_color=bg,
            reputation=rep, level=level,
            parent_competition_id=parent,
            qualifiers=qualifiers,
            rank1=rank1, rank2=rank2, rank3=rank3,
            year1=year1, year2=year2, year3=year3,
            unknown3=unknown3, is_women=is_women,
        )

    def write(self, w: WriterEx):
        w.write_i16(self.id)
        w.write_i32(self.uid)
        w.write_string(self.full_name)
        w.write_u8(self.full_term)
        w.write_string(self.short_name)
        w.write_u8(self.short_term)
        w.write_string(self.code_name)
        w.write_u8(self.ctype)
        w.write_i16(self.continent_id)
        w.write_i16(self.nation_id)
        w.write_u16(self.fg_color)
        w.write_u16(self.bg_color)
        w.write_i16(self.reputation)
        w.write_u8(self.level)
        w.write_i16(self.parent_competition_id)
        w.write_i32(len(self.qualifiers))
        for q in self.qualifiers:
            b = (q or b"")[:8]
            w.write_bytes(b + (b"\x00" * (8 - len(b))))
        w.write_i32(self.rank1)
        w.write_i32(self.rank2)
        w.write_i32(self.rank3)
        w.write_i16(self.year1)
        w.write_i16(self.year2)
        w.write_i16(self.year3)
        w.write_u8(self.unknown3)
        w.write_bool(self.is_women)


@dataclass
class StadiumRec:
    """Stadium record.

    Actual FMM .dat layout (verified against the game database; matches the
    release GUI editor which exposes stadium Name/Name2/Capacity only):
        id(i32) uid(i32) city_id(i16) capacity(i32) expansion_capacity(i32)
        name(string) name2(string)
        extra_count(i32) + extra_data(raw, that many bytes)   <- variable, must skip
        terminator(u8, always 0xff) unknown(u8) other(i16)
    """
    id: int
    uid: int
    city_id: int
    capacity: int
    expansion_capacity: int
    name: str
    name2: str
    extra_count: int
    extra_data: bytes
    terminator: int
    unknown3: int
    unknown4: int

    @staticmethod
    def read(r: ReaderEx) -> "StadiumRec":
        ident = r.read_i32()
        uid = r.read_i32()
        city = r.read_i16()
        capacity = r.read_i32()
        expansion = r.read_i32()
        name = r.read_string()
        name2 = r.read_string()
        ec = r.read_i32()
        extra = r.read_bytes(ec)
        terminator = r.read_u8()
        unk3 = r.read_u8()
        unk4 = r.read_i16()
        return StadiumRec(
            id=ident, uid=uid, city_id=city,
            capacity=capacity, expansion_capacity=expansion,
            name=name, name2=name2,
            extra_count=ec, extra_data=extra,
            terminator=terminator, unknown3=unk3, unknown4=unk4
        )

    def write(self, w: WriterEx):
        w.write_i32(self.id)
        w.write_i32(self.uid)
        w.write_i16(self.city_id)
        w.write_i32(self.capacity)
        w.write_i32(self.expansion_capacity)
        w.write_string(self.name)
        w.write_string(self.name2)
        w.write_i32(self.extra_count)
        w.write_bytes(self.extra_data)
        w.write_u8(self.terminator)
        w.write_u8(self.unknown3)
        w.write_i16(self.unknown4)


@dataclass
class RegionRec:
    """Region record."""
    id: int
    uid: int
    name: str
    terminator: int
    nation_id: int
    weather_id: int
    
    @staticmethod
    def read(r: ReaderEx) -> "RegionRec":
        return RegionRec(
            id=r.read_i16(),
            uid=r.read_i32(),
            name=r.read_string(),
            terminator=r.read_u8(),
            nation_id=r.read_i16(),
            weather_id=r.read_i16()
        )
    
    def write(self, w: WriterEx):
        w.write_i16(self.id)
        w.write_i32(self.uid)
        w.write_string(self.name)
        w.write_u8(self.terminator)
        w.write_i16(self.nation_id)
        w.write_i16(self.weather_id)

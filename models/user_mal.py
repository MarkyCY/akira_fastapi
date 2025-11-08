from typing import List, Optional
from pydantic import BaseModel
from enum import Enum
from datetime import datetime


# === ENUMS ===

class NsfwEnum(str, Enum):
    white = "white"
    gray = "gray"
    black = "black"

class MediaTypeEnum(str, Enum):
    unknown = "unknown"
    tv = "tv"
    ova = "ova"
    movie = "movie"
    special = "special"
    ona = "ona"
    music = "music"

class AiringStatusEnum(str, Enum):
    finished_airing = "finished_airing"
    currently_airing = "currently_airing"
    not_yet_aired = "not_yet_aired"

class UserStatusEnum(str, Enum):
    watching = "watching"
    completed = "completed"
    on_hold = "on_hold"
    dropped = "dropped"
    plan_to_watch = "plan_to_watch"

class SeasonEnum(str, Enum):
    winter = "winter"
    spring = "spring"
    summer = "summer"
    fall = "fall"

class SourceEnum(str, Enum):
    other = "other"
    original = "original"
    manga = "manga"
    four_koma_manga = "4_koma_manga"
    web_manga = "web_manga"
    digital_manga = "digital_manga"
    novel = "novel"
    light_novel = "light_novel"
    visual_novel = "visual_novel"
    game = "game"
    card_game = "card_game"
    book = "book"
    picture_book = "picture_book"
    radio = "radio"
    music = "music"

class RatingEnum(str, Enum):
    g = "g"
    pg = "pg"
    pg_13 = "pg_13"
    r = "r"
    r_plus = "r+"
    rx = "rx"


# === MODELOS ANIDADOS ===

class MainPicture(BaseModel):
    medium: Optional[str] = None
    large: Optional[str] = None


class AlternativeTitles(BaseModel):
    synonyms: Optional[List[str]] = None
    en: Optional[str] = None
    ja: Optional[str] = None


class Genre(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None


class MyListStatus(BaseModel):
    status: Optional[UserStatusEnum] = None
    score: Optional[int] = None
    num_episodes_watched: Optional[int] = None
    is_rewatching: Optional[bool] = None
    start_date: Optional[str] = None
    finish_date: Optional[str] = None
    priority: Optional[int] = None
    num_times_rewatched: Optional[int] = None
    rewatch_value: Optional[int] = None
    tags: Optional[List[str]] = None
    comments: Optional[str] = None
    updated_at: Optional[datetime] = None


class StartSeason(BaseModel):
    year: Optional[int] = None
    season: Optional[SeasonEnum] = None


class Broadcast(BaseModel):
    day_of_the_week: Optional[str] = None
    start_time: Optional[str] = None


class Studio(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None


class AnimeNode(BaseModel):
    id: int
    title: str
    main_picture: Optional[MainPicture] = None
    alternative_titles: Optional[AlternativeTitles] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    synopsis: Optional[str] = None
    mean: Optional[float] = None
    rank: Optional[int] = None
    popularity: Optional[int] = None
    num_list_users: Optional[int] = None
    num_scoring_users: Optional[int] = None
    nsfw: Optional[NsfwEnum] = None
    genres: Optional[List[Genre]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    media_type: Optional[MediaTypeEnum] = None
    status: Optional[AiringStatusEnum] = None
    my_list_status: Optional[MyListStatus] = None
    num_episodes: Optional[int] = None
    start_season: Optional[StartSeason] = None
    broadcast: Optional[Broadcast] = None
    source: Optional[SourceEnum] = None
    average_episode_duration: Optional[int] = None
    rating: Optional[RatingEnum] = None
    studios: Optional[List[Studio]] = None

    class Config:
        extra = "ignore"  # ✅ Ignorar campos desconocidos


class AnimeListStatus(MyListStatus):
    pass


class UserAnimeListEdge(BaseModel):
    node: AnimeNode
    list_status: AnimeListStatus


class Paging(BaseModel):
    previous: Optional[str] = None
    next: Optional[str] = None


class AnimeAPIResponse(BaseModel):
    data: List[UserAnimeListEdge]
    paging: Optional[Paging] = None

    class Config:
        extra = "ignore"  # ✅ Evita error si llegan campos nuevos

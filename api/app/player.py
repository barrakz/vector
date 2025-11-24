"""
Player Profile API endpoints.
Niezależny moduł dla systemu generowania profili piłkarzy Ekstraklasy.
"""
from typing import Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from psycopg.types.json import Jsonb

import logging
from app.db import get_db_connection

# Configure logging
logger = logging.getLogger(__name__)

# Create router for player endpoints
router = APIRouter(prefix="/player", tags=["player"])


# Request/Response models
class PlayerProfileCreate(BaseModel):
    name: str = Field(..., description="Imię i nazwisko piłkarza")
    summary: str = Field(..., description="Krótkie podsumowanie kariery")
    position: str = Field(..., description="Pozycja na boisku")
    clubs: List[str] = Field(default_factory=list, description="Lista klubów w karierze")
    characteristics: str = Field(..., description="Charakterystyka stylu gry")
    strengths: str = Field(..., description="Mocne strony")
    weaknesses: str = Field(..., description="Słabe strony")
    estimated_current_form: str = Field(..., description="Ocena aktualnej formy")
    team: Optional[str] = Field(None, description="Obecna drużyna")
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict, description="Dodatkowe dane")


class PlayerProfileUpdate(BaseModel):
    summary: Optional[str] = None
    position: Optional[str] = None
    clubs: Optional[List[str]] = None
    characteristics: Optional[str] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    estimated_current_form: Optional[str] = None
    team: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class PlayerProfileResponse(BaseModel):
    id: int
    name: str
    summary: str
    position: str
    clubs: List[str]
    characteristics: str
    strengths: str
    weaknesses: str
    estimated_current_form: str
    team: Optional[str]
    metadata: Optional[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class PlayerCreateResponse(BaseModel):
    status: str
    player_id: int
    message: str


@router.post("/create", response_model=PlayerCreateResponse)
async def create_player(profile: PlayerProfileCreate):
    """
    Utwórz lub zaktualizuj profil piłkarza (UPSERT).
    
    Endpoint używany przez n8n workflow po wygenerowaniu profilu przez Gemini.
    Jeśli piłkarz już istnieje (po nazwisku), aktualizuje jego profil.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Dodaj metadata z timestampem generowania
        metadata = profile.metadata or {}
        metadata["generated_at"] = datetime.utcnow().isoformat()
        
        # UPSERT - wstaw nowy lub zaktualizuj istniejący
        logger.info(f"Creating/updating player profile: '{profile.name}'")
        cursor.execute(
            """
            INSERT INTO players (
                name, summary, position, clubs, characteristics,
                strengths, weaknesses, estimated_current_form, team, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                summary = EXCLUDED.summary,
                position = EXCLUDED.position,
                clubs = EXCLUDED.clubs,
                characteristics = EXCLUDED.characteristics,
                strengths = EXCLUDED.strengths,
                weaknesses = EXCLUDED.weaknesses,
                estimated_current_form = EXCLUDED.estimated_current_form,
                team = EXCLUDED.team,
                metadata = EXCLUDED.metadata,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, (xmax = 0) AS inserted;
            """,
            (
                profile.name,
                profile.summary,
                profile.position,
                profile.clubs,
                profile.characteristics,
                profile.strengths,
                profile.weaknesses,
                profile.estimated_current_form,
                profile.team,
                Jsonb(metadata)
            )
        )
        
        result = cursor.fetchone()
        player_id = result[0]
        was_inserted = result[1]
        
        cursor.close()
        conn.close()
        
        status = "created" if was_inserted else "updated"
        message = f"Profil piłkarza '{profile.name}' został {'utworzony' if was_inserted else 'zaktualizowany'}"
        
        logger.info(f"Player profile {status} successfully with ID: {player_id}")
        return PlayerCreateResponse(
            status=status,
            player_id=player_id,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error creating/updating player profile: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd podczas tworzenia/aktualizacji profilu: {str(e)}")


@router.get("/search")
async def search_player(name: str):
    """
    Wyszukaj piłkarza po nazwisku.
    
    Używane przez n8n workflow do sprawdzenia czy profil już istnieje.
    Zwraca obiekt z polem 'found' i opcjonalnie 'profile'.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT 
                id, name, summary, position, clubs, characteristics,
                strengths, weaknesses, estimated_current_form, team,
                metadata, created_at, updated_at
            FROM players
            WHERE name ILIKE %s
            LIMIT 1;
            """,
            (f"%{name}%",)
        )
        
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not row:
            return {"found": False}
        
        profile = PlayerProfileResponse(
            id=row[0],
            name=row[1],
            summary=row[2],
            position=row[3],
            clubs=row[4],
            characteristics=row[5],
            strengths=row[6],
            weaknesses=row[7],
            estimated_current_form=row[8],
            team=row[9],
            metadata=row[10],
            created_at=row[11],
            updated_at=row[12]
        )
        
        return {"found": True, "profile": profile.model_dump()}
        
    except Exception as e:
        logger.error(f"Error searching player: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd podczas wyszukiwania: {str(e)}")


@router.get("/{player_id}", response_model=PlayerProfileResponse)
async def get_player(player_id: int):
    """
    Pobierz profil piłkarza po ID.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT 
                id, name, summary, position, clubs, characteristics,
                strengths, weaknesses, estimated_current_form, team,
                metadata, created_at, updated_at
            FROM players
            WHERE id = %s;
            """,
            (player_id,)
        )
        
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Piłkarz o ID {player_id} nie został znaleziony")
        
        return PlayerProfileResponse(
            id=row[0],
            name=row[1],
            summary=row[2],
            position=row[3],
            clubs=row[4],
            characteristics=row[5],
            strengths=row[6],
            weaknesses=row[7],
            estimated_current_form=row[8],
            team=row[9],
            metadata=row[10],
            created_at=row[11],
            updated_at=row[12]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching player: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd podczas pobierania profilu: {str(e)}")


@router.put("/{player_id}", response_model=PlayerProfileResponse)
async def update_player(player_id: int, updates: PlayerProfileUpdate):
    """
    Zaktualizuj profil piłkarza.
    
    Umożliwia ręczną edycję wygenerowanego profilu.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Sprawdź czy piłkarz istnieje
        cursor.execute("SELECT id FROM players WHERE id = %s;", (player_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail=f"Piłkarz o ID {player_id} nie został znaleziony")
        
        # Przygotuj update query tylko dla podanych pól
        update_fields = []
        update_values = []
        
        if updates.summary is not None:
            update_fields.append("summary = %s")
            update_values.append(updates.summary)
        if updates.position is not None:
            update_fields.append("position = %s")
            update_values.append(updates.position)
        if updates.clubs is not None:
            update_fields.append("clubs = %s")
            update_values.append(updates.clubs)
        if updates.characteristics is not None:
            update_fields.append("characteristics = %s")
            update_values.append(updates.characteristics)
        if updates.strengths is not None:
            update_fields.append("strengths = %s")
            update_values.append(updates.strengths)
        if updates.weaknesses is not None:
            update_fields.append("weaknesses = %s")
            update_values.append(updates.weaknesses)
        if updates.estimated_current_form is not None:
            update_fields.append("estimated_current_form = %s")
            update_values.append(updates.estimated_current_form)
        if updates.team is not None:
            update_fields.append("team = %s")
            update_values.append(updates.team)
        if updates.metadata is not None:
            update_fields.append("metadata = %s")
            update_values.append(Jsonb(updates.metadata))
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="Brak pól do aktualizacji")
        
        # Zawsze aktualizuj updated_at
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        update_values.append(player_id)
        
        query = f"""
            UPDATE players
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING id, name, summary, position, clubs, characteristics,
                      strengths, weaknesses, estimated_current_form, team,
                      metadata, created_at, updated_at;
        """
        
        cursor.execute(query, update_values)
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Player profile updated: ID {player_id}")
        
        return PlayerProfileResponse(
            id=row[0],
            name=row[1],
            summary=row[2],
            position=row[3],
            clubs=row[4],
            characteristics=row[5],
            strengths=row[6],
            weaknesses=row[7],
            estimated_current_form=row[8],
            team=row[9],
            metadata=row[10],
            created_at=row[11],
            updated_at=row[12]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating player: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd podczas aktualizacji profilu: {str(e)}")


@router.delete("/{player_id}")
async def delete_player(player_id: int):
    """
    Usuń profil piłkarza.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM players WHERE id = %s RETURNING name;", (player_id,))
        deleted = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Piłkarz o ID {player_id} nie został znaleziony")
        
        logger.info(f"Player profile deleted: '{deleted[0]}' (ID: {player_id})")
        return {"status": "deleted", "message": f"Profil piłkarza '{deleted[0]}' został usunięty"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting player: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd podczas usuwania profilu: {str(e)}")


@router.get("/", response_model=List[PlayerProfileResponse])
async def list_players(limit: int = 50, offset: int = 0):
    """
    Lista wszystkich piłkarzy z paginacją.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT 
                id, name, summary, position, clubs, characteristics,
                strengths, weaknesses, estimated_current_form, team,
                metadata, created_at, updated_at
            FROM players
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s;
            """,
            (limit, offset)
        )
        
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        players = [
            PlayerProfileResponse(
                id=row[0],
                name=row[1],
                summary=row[2],
                position=row[3],
                clubs=row[4],
                characteristics=row[5],
                strengths=row[6],
                weaknesses=row[7],
                estimated_current_form=row[8],
                team=row[9],
                metadata=row[10],
                created_at=row[11],
                updated_at=row[12]
            )
            for row in rows
        ]
        
        return players
        
    except Exception as e:
        logger.error(f"Error listing players: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd podczas pobierania listy piłkarzy: {str(e)}")

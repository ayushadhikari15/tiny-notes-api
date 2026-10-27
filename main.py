import os
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Type
from datetime import datetime
import sqlite3
from fastapi import FastAPI, status, HTTPException

app = FastAPI()

DB_NAME = "notes.db"

def myDB():
    """Initializes the SQLite database and creates the notes table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

myDB()

class NoteCreate(BaseModel):
    title: str = Field(description="This is the main Title of the page")
    content: str = Field(description="This is the content of the page")

class NoteResponse(BaseModel):
    id: int = Field(description="This is the unique ID for every new note's page.")
    title: str = Field(description="This is the main Title of the page")
    content: str = Field(description="This is the content of the page")
    timestamp: str = Field(description="Time when the notes were created")

@app.get("/")
def welcome():    
    return "Welcome to my Project Dude \U0001F680"  

@app.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(note: NoteCreate):
    """Takes title and content, add an id and a timestamp. Saves in SQLite and returns a response."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO notes (title, content, timestamp) VALUES (?, ?, ?)",
        (note.title, note.content, current_time)
    )

    conn.commit()
    note_id = cursor.lastrowid
    conn.close()

    return NoteResponse(
        id=note_id,
        title=note.title,
        content=note.content,
        timestamp=current_time
    )


# --- FIXED: GET ALL NOTES ROUTE ---
@app.get("/notes", response_model=List[NoteResponse])
def get_all_notes():
    """Fetches all saved notes from SQLite."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, content, timestamp FROM notes")
    rows = cursor.fetchall()
    conn.close()

    notes_list = []
    for row in rows:
        notes_list.append(
            NoteResponse(
                id=row[0],
                title=row[1],
                content=row[2],
                timestamp=row[3]
            )
        )
    return notes_list


# --- FIXED: GET SINGLE NOTE BY ID ROUTE ---
@app.get("/notes/{id}", response_model=NoteResponse)
def get_note(id: int):
    """It is used to fetch title, content, unique id and timestamp by ID from SQLite."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, title, content, timestamp FROM notes WHERE id = ?",
        (id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Note with id {id} not found.")

    return NoteResponse(
        id=row[0],
        title=row[1],
        content=row[2],
        timestamp=row[3]
    )


@app.put("/notes/{id}", response_model=NoteResponse)
def update_note(id: int, updated_note: NoteCreate):
    """Updates an existing note's content and title by ID"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT timestamp FROM notes WHERE id = ?", (id,))
    row = cursor.fetchone()

    if row is None:    
        conn.close()
        raise HTTPException(status_code=404, detail=f"Note with id {id} does not exist.")

    existing_timestamp = row[0]

    cursor.execute(
        "UPDATE notes SET title = ?, content = ? WHERE id = ?",
        (updated_note.title, updated_note.content, id)
    )
    
    conn.commit()
    conn.close()
    
    return NoteResponse(
        id=id,
        title=updated_note.title,
        content=updated_note.content,
        timestamp=existing_timestamp
    )


@app.delete("/notes/{id}")
def delete_note(id: int):
    """Deletes a note from SQLite by its unique ID."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM notes WHERE id = ?", (id,))
    row = cursor.fetchone()
    
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Note with id {id} not found.")

    cursor.execute("DELETE FROM notes WHERE id = ?", (id,))
    
    conn.commit()
    conn.close()

    return {"message": f"Note with id {id} has been deleted successfully."}
    

if __name__ == "__main__":
    myDB()
    print("Database 'notes.db' initialized successfully with the 'notes' table!")
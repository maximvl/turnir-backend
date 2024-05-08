from datetime import datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from flask_sqlalchemy import SQLAlchemy
import json

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

class Preset(db.Model):
    id: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str]
    owner_id: Mapped[str]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    options: Mapped[str]


def init_db(flask_app) -> None:
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///turnir.db"
    db.init_app(flask_app)
    with flask_app.app_context():
        db.create_all()


def get_preset(preset_id: str) -> Preset:
    return db.get_or_404(Preset, preset_id)


def save_preset(preset: Preset) -> None:
    db.session.add(preset)
    db.session.commit()


def serialize_preset(preset: Preset) -> dict:
    return {
        "id": preset.id,
        "title": preset.title,
        "owner_id": preset.owner_id,
        "created_at": preset.created_at,
        "updated_at": preset.updated_at,
        "options": json.loads(preset.options)
    }

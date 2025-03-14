from tortoise import fields
from tortoise.models import Model
from datetime import datetime


class SharedChat(Model):
    """Model for storing shared chat sessions"""
    id = fields.CharField(max_length=36, pk=True)
    title = fields.CharField(max_length=255)
    messages = fields.JSONField()
    created_at = fields.DatetimeField()  # Removed auto_now_add to allow explicit time setting

    class Meta:
        table = "shared_chats"

    def __str__(self):
        return f"{self.title} ({self.id})"

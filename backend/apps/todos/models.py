from django.db import models

from apps.accounts.models import Account


class Todo(models.Model):
    account = models.ForeignKey(
        Account,
        related_name="todos",
        on_delete=models.CASCADE,
        help_text="Owning account. Set from the authenticated request only — never from client input.",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["account", "completed"]),
        ]

    def __str__(self) -> str:
        return self.title

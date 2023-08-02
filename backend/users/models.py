import os
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint


MAX_LENGTH_LIMIT = os.getenv('MAX_LENGTH_LIMIT', default=150)


class User(AbstractUser):
    """Кастомная модель пользователей."""

    first_name = models.CharField('Имя',
                                  max_length=MAX_LENGTH_LIMIT,
                                  blank=False)
    last_name = models.CharField('Фамилия',
                                 max_length=MAX_LENGTH_LIMIT,
                                 blank=False)
    email = models.EmailField('email',
                              max_length=254,
                              blank=False,
                              unique=True
                              )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('email',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Пользователь'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        ordering = ('author',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            UniqueConstraint(fields=['user', 'author'],
                             name='unique_follow'),
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_prevent_self_follow",
                check=~models.Q(user=models.F("author"))
            )
        ]

    def __str__(self):
        return f'Подписка {self.user} на {self.author}'

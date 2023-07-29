from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint
from django.core.exceptions import ValidationError


def username_not_be_me(value):
    if value.lower() == 'me':
        raise ValidationError('')


class User(AbstractUser):
    """Кастомная модель пользователей."""
    first_name = models.CharField('Имя', max_length=50, blank=False)
    last_name = models.CharField('Фамилия', max_length=150, blank=False)
    email = models.EmailField('email', max_length=254,
                              blank=False, unique=True
                              )
    ROLE_CHOICES = (
        ('user', 'user'),
        ('admin', 'admin'),
    )
    role = models.CharField('роль',
                            max_length=25,
                            choices=ROLE_CHOICES,
                            default='user',
                            )

    @property
    def is_admin(self):
        """Проверка, является ли пользователь админом или суперюзером."""
        return self.role == 'admin' or self.is_superuser or self.is_staff

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('first_name',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            UniqueConstraint(fields=['user', 'author'],
                             name='unique_follow')
        ]

    def __str__(self):
        return f'Пользователь {self.user} подписался на {self.author}'

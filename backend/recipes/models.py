from colorfield.fields import ColorField
from django.db import models
from django.db.models import UniqueConstraint
from django.core import validators

from users.models import User


MAX_LENGTH_LIMIT = 150


class Tag(models.Model):
    '''Модель тегов.'''

    name = models.CharField('Название тега',
                            max_length=MAX_LENGTH_LIMIT,
                            null=False)
    color = ColorField('Цвет тега',
                       default='#ffffff',
                       null=False)
    slug = models.CharField('slug',
                            max_length=MAX_LENGTH_LIMIT,
                            null=False,
                            unique=True
                            )

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    '''Модель ингредиентов.'''

    name = models.CharField('Название ингредиента',
                            max_length=MAX_LENGTH_LIMIT
                            )
    measurement_unit = models.CharField('Единицы измерения',
                                        max_length=MAX_LENGTH_LIMIT
                                        )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            UniqueConstraint(fields=['name', 'measurement_unit'],
                             name='unique_ingredient_unit')
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    '''Рецепты.'''

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe',
        verbose_name='Автор рецепта',
    )
    name = models.CharField('Название рецепта',
                            max_length=MAX_LENGTH_LIMIT
                            )
    image = models.ImageField('Фото рецепта',
                              upload_to='recipe/',
                              null=True,
                              default=None
                              )
    text = models.TextField('Описание рецепта')
    tags = models.ManyToManyField(Tag,
                                  blank=False,
                                  verbose_name='Теги'
                                  )
    cooking_time = models.PositiveIntegerField(
        'Время приготовления',
        validators=[
            validators.MinValueValidator(1, message='Минимум 1 минута'),
            validators.MaxValueValidator(720, message='Максимум 720 минут')]
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-name',)

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    """Буферная модель для связи моделей ингридиента и рецепта."""
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Рецепт',
        blank=False,
        null=False
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Ингредиент',
        blank=False,
        null=False
    )
    amount = models.PositiveIntegerField(
        'Колличество ингредиента.',
        blank=False,
        null=False,
        validators=[
            validators.MinValueValidator(
                1,
                message='Минимум 1 грамм'
            ),
            validators.MaxValueValidator(
                10000,
                message='Максимум 10000 грамм'
            )
        ]
    )

    class Meta:
        verbose_name = 'Ингридиент в рецепте'
        verbose_name_plural = 'Ингридиенты в рецепте'

    def __str__(self):
        return f'{self.amount}гр. {self.ingredient.name} в {self.recipe.name}'


class Model_user_recipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='%(class)s'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт в избранном',
        related_name='%(class)s'
    )

    class Meta:
        abstract = True


class Favourites(Model_user_recipe):
    """Модель Избранного"""

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'Пользователь {self.user} добавил в избранное {self.recipe}'


class Shopping_list(Model_user_recipe):
    """Модель листа покупок"""

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'Список покупок пользователя {self.user}'

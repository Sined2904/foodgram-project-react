from django.db import models
from users.models import User
from django.core.validators import RegexValidator


class Tag(models.Model):
    '''Модель тегов.'''
    name = models.CharField(max_length=200, null=False)
    color = models.CharField(max_length=7, null=False, unique=True,
                             validators=[RegexValidator(
                                 regex=r'^#([A-Fa-f0-9]{3,6})$',
                                 message='Название цвета в формате HEX!')])
    slug = models.CharField(max_length=200, null=False, unique=True)

    class Meta:
        verbose_name = 'Тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    '''Модель ингредиентов.'''
    name = models.CharField(verbose_name='Название ингредиента',
                            max_length=200)
    measurement_unit = models.CharField(verbose_name='Единицы измерения',
                                        max_length=200)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

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
    name = models.CharField(verbose_name='Название рецепта', max_length=200)
    image = models.ImageField(
        upload_to='recipe/', null=True, blank=True)
    text = models.TextField(verbose_name='Описание рецепта')
    tags = models.ManyToManyField(Tag)
    cooking_time = models.PositiveIntegerField('Время приготовления')

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-name',)

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    '''Буферная модель для связи моделей ингридиента и рецепта.'''
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    amount = models.PositiveIntegerField('Колличество ингредиента.')

    class Meta:
        verbose_name = 'Ингридиент в рецепте '
        verbose_name_plural = 'Ингридиенты в рецепте'

    def __str__(self):
        return f'{self.ingredient.name} в {self.recipe.name}'


class Favourites(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favourites',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Рецепт в избранном',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'Пользователь {self.user} добавил в избранное {self.recipe}'


class Shopping_list(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='Shopping_list'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'Список покупок пользователя {self.user}'

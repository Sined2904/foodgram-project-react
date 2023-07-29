# Generated by Django 4.2.3 on 2023-07-28 09:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recipe',
            name='ingredients',
        ),
        migrations.AlterField(
            model_name='ingredientinrecipe',
            name='ingredient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipe', to='recipes.ingredient'),
        ),
        migrations.AlterField(
            model_name='ingredientinrecipe',
            name='recipe',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredient', to='recipes.recipe'),
        ),
        migrations.AlterField(
            model_name='shopping_list',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipeinshoppinglist', to=settings.AUTH_USER_MODEL),
        ),
    ]

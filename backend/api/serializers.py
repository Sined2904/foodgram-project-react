import base64
import re

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from django.core.files.base import ContentFile

from users.models import Follow, User
from recipes.models import (Favourites, Ingredient, IngredientInRecipe, Recipe,
                            Shopping_list, Tag)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class IngredientSerializer(serializers.ModelSerializer):
    measurement_unit = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']
        read_only_fields = (
            'name',
            'measurement_unit'
        )


class SubscribeRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed'
                  ]

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Follow.objects.filter(author=obj, user=request.user).exists()


class CreateUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password']


class FavouriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='recipe.id')
    name = serializers.CharField(
        source='recipe.name')
    image = serializers.ImageField(
        source='recipe.image')
    cooking_time = serializers.IntegerField(
        source='recipe.cooking_time')

    class Meta:
        model = Follow
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'amount', 'measurement_unit')

    def validate_amount(self, amount):
        if amount < 1:
            raise serializers.ValidationError('Количество ингредиента'
                                              ' не может быть 0!')


class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ['id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time']

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Favourites.objects.filter(
            recipe=obj, user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Shopping_list.objects.filter(
            recipe=obj, user=request.user).exists()


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    amount = serializers.IntegerField()
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)

    class Meta:
        model = IngredientInRecipe
        fields = ['id', 'name', 'measurement_unit', 'amount']


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CreateRecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(many=True)
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    cooking_time = serializers.IntegerField()
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = ['id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time']

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        instance = super().create(validated_data)
        for data in ingredients:
            ingredient = data['ingredient']
            IngredientInRecipe(
                recipe=instance,
                ingredient=get_object_or_404(Ingredient, id=ingredient['id']),
                amount=data['amount']
            ).save()
        return instance

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        IngredientInRecipe.objects.filter(recipe=instance).delete()
        super().update(instance, validated_data)
        for data in ingredients:
            ingredient = data['ingredient']
            IngredientInRecipe(
                recipe=instance,
                ingredient=get_object_or_404(Ingredient, id=ingredient['id']),
                amount=data['amount']
            ).save()
        return instance

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Favourites.objects.filter(
            recipe=obj, user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Shopping_list.objects.filter(
            recipe=obj, user=request.user
        ).exists()

    def validate_cooking_time(self, attrs):
        if attrs < 1:
            raise serializers.ValidationError('Время готовки не может'
                                              'быть меньше 1 минуты')
        return attrs

    def validate_tags(self, tags):
        if len(tags) < 1:
            raise serializers.ValidationError('Добавьте хотя бы 1 тег')
        tag_in_recipe = []
        for tag in tags:
            if tag in tag_in_recipe:
                raise serializers.ValidationError(
                    'Каждый тег указывается один раз!')
            tag_in_recipe.append(tag)
        return tags

    def validate_ingredients(self, ingredients):
        if len(ingredients) < 1:
            raise serializers.ValidationError('Добавьте хотя бы 1 ингредиент!')
        ingredient_in_recipe = []
        for ingredient in ingredients:
            if int(ingredient.get('amount')) < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента не может быть 0!')
            if ingredient in ingredient_in_recipe:
                raise serializers.ValidationError(
                    'Каждый ингредиент указывается один раз!')
            ingredient_in_recipe.append(ingredient)
        return ingredients

    def validate_name(self, name):
        if re.search('[a-zA-Zа-яА-ЯёЁ]', name) is None:
            raise serializers.ValidationError('В названии должны быть буквы')
        return name


class RecipeShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscribeSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(
        source='author.id')
    email = serializers.EmailField(
        source='author.email')
    username = serializers.CharField(
        source='author.username')
    first_name = serializers.CharField(
        source='author.first_name')
    last_name = serializers.CharField(
        source='author.last_name')
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Follow
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_anonymous:
            return False
        return Follow.objects.filter(
            author=obj.author, user=request.user).exists()

    def get_recipes(self, obj):
        recipes = obj.author.recipe.all()
        return SubscribeRecipeSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.author.recipe.all().count()


class Shopping_cartSerializer(serializers.ModelSerializer):

    name = serializers.CharField()
    image = serializers.ImageField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Shopping_list
        fields = ['id', 'name', 'image', 'cooking_time']
        read_only_fields = ('name', 'image', 'cooking_time')

from django.db.models.aggregates import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Ingredient, IngredientInRecipe, Recipe,
                            Tag)
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import Follow, User

from .permissions import IsAdminOrReadOnly
from .serializers import (CreateRecipeSerializer, FavouriteSerializer,
                          IngredientSerializer, RecipeSerializer,
                          Shopping_cartSerializer, SubscribeSerializer,
                          TagSerializer)
from .utils import RecipeFilter
from rest_framework import filters


class TagViewSet(viewsets.ModelViewSet):
    '''Вьюсет для Тегов.'''

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    '''Вьюсет для Ингредиентов.'''

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAdminOrReadOnly,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    search_fields = ('^name',)


class Favourites(generics.RetrieveDestroyAPIView, generics.ListCreateAPIView):
    '''Вью для добавления и удаления рецепта в избранное.'''

    queryset = Recipe.objects.all()
    serializer_class = FavouriteSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        '''Получение id рецепта из URL.'''
        return get_object_or_404(Recipe, id=self.kwargs['recipe_id'])

    def create(self, request, *args, **kwargs):
        '''Добавление в избранное.'''
        recipe = self.get_object()
        favorite = request.user.favourites.create(recipe=recipe)
        serializer = self.get_serializer(favorite)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        '''Удаление подписки.'''
        self.request.user.favourites.filter(recipe=instance).delete()


class RecipeViewSet(viewsets.ModelViewSet):
    '''Вьюсет для рецептов.'''

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = (IsAuthenticated, )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        '''Переопределение сериализатора для POST запроса.'''
        if self.action == 'create' or 'update':
            return CreateRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        '''Добавление автора рецепта, пользователя который сделал запрос.'''
        serializer.save(author=self.request.user)

    @action(detail=False)
    def download_shopping_cart(self, request):
        '''Метод для скачивания листа покупок.'''
        ingredients = (
            IngredientInRecipe.objects.filter(
                recipe__in_cart__user=request.user,
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(ingredient_amount=Sum('amount'))
        )
        data = []
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            measurement_unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['ingredient_amount']
            data.append(f'{name}: {amount}, {measurement_unit}\n')
        response = HttpResponse(content=data, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="cart.txt"'
        return response


class Subscribe(generics.RetrieveDestroyAPIView, generics.ListCreateAPIView):
    """Подписка и отписка от пользователя."""

    serializer_class = SubscribeSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        '''Получение id пользователя из URL.'''
        user_id = self.kwargs['user_id']
        return get_object_or_404(User, id=user_id)

    def get_queryset(self):
        '''Проверка наличие подписки.'''
        follow = Follow.objects.filter(
            user=self.request.user, author=self.get_object()).exists()
        return follow

    def create(self, request, *args, **kwargs):
        '''Создание подписки.'''
        user_author = self.get_object()
        if request.user.id == user_author.id:
            return Response('Нельзя подписаться на самого себя!',
                            status=status.HTTP_400_BAD_REQUEST)
        if request.user.follower.filter(author=user_author).exists():
            return Response('Нельзя подписаться дважды!',
                            status=status.HTTP_400_BAD_REQUEST)
        subscribe = request.user.follower.create(author=user_author)
        serializer = self.get_serializer(subscribe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        '''Удаление подписки.'''
        self.request.user.follower.filter(author=instance).delete()


class Shopping_listViews(generics.RetrieveDestroyAPIView,
                         generics.ListCreateAPIView):
    """Добавление и удаление рецептов из листа покупок."""

    serializer_class = Shopping_cartSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        '''Получение id рецепта из URL.'''
        return get_object_or_404(Recipe, id=self.kwargs['recipe_id'])

    def create(self, request, *args, **kwargs):
        '''Добавление в список покупок.'''
        recipe = self.get_object()
        request.user.shopping_list.create(recipe=recipe)
        serializer = self.get_serializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        '''Удаление рецепта из листа покупок.'''
        self.request.user.shopping_list.filter(
            recipe=self.get_object()).delete()


class SubscriptionsViews(generics.ListAPIView):
    '''Вьюсет для отображения подписок пользователя'''

    queryset = Follow.objects.all()
    serializer_class = SubscribeSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = PageNumberPagination

    @action(detail=False, methods=['GET'])
    def subscriptions(self, request):
        '''Метод для отображения всех подписок пользователя.'''
        follows = request.user.follower
        serializer = SubscribeSerializer(follows, many=True)
        return Response(serializer.data)

import io

from django.db.models.aggregates import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Ingredient, IngredientInRecipe, Recipe,
                            Tag)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import Follow, User

from .permissions import IsAdminOrReadOnly, IsAuthororAdmin
from .serializers import (CreateRecipeSerializer, FavouriteSerializer,
                          IngredientSerializer, RecipeSerializer,
                          Shopping_cartSerializer, SubscribeSerializer,
                          TagSerializer)


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
    permission_classes = (IsAuthenticated, IsAuthororAdmin)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('author', 'tags')

    def get_serializer_class(self):
        '''Переопределение сериализатора для POST запроса.'''
        if self.action == 'create':
            return CreateRecipeSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        '''Добавление автора рецепта, пользователя который сделал запрос.'''
        serializer.save(author=self.request.user)

    @action(detail=False)
    def download_shopping_cart(self, request):
        '''Метод для скачивания листа покупок.'''
        buffer = io.BytesIO()
        page = canvas.Canvas(buffer)
        pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
        x_position, y_position = 50, 800
        shopping_cart = (
            IngredientInRecipe.objects.filter(
                recipe__shopping_list__user=request.user).values(
                    'ingredient__name',
                    'ingredient__measurement_unit',
                    ).annotate(amount=Sum('amount')).order_by()
                    )
        if shopping_cart:
            indent = 20
            page.setFont("Arial", 24)
            page.drawString(x_position, y_position, 'Cписок покупок:')
            page.setFont("Arial", 12)
            for index, recipe in enumerate(shopping_cart, start=1):
                page.drawString(
                    x_position, y_position - indent,
                    f'{index}. {recipe["ingredient__name"]} - '
                    f'{recipe["amount"]} '
                    f'{recipe["ingredient__measurement_unit"]}.')
                y_position -= 15
                if y_position <= 50:
                    page.showPage()
                    y_position = 800
            page.save()
            buffer.seek(0)
            return FileResponse(
                buffer, as_attachment=True, filename='Shopping_cart.pdf')
        page.setFont("Arial", 24)
        page.drawString(
            x_position,
            y_position,
            'Cписок покупок пуст!')
        page.save()
        buffer.seek(0)
        return FileResponse(
            buffer, as_attachment=True, filename='Shopping_cart.pdf')


class Subscribe(generics.RetrieveDestroyAPIView, generics.ListCreateAPIView):
    """Подписка и отписка от пользователя."""
    serializer_class = SubscribeSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        '''Получение id пользователя из URL.'''
        user_id = self.kwargs['user_id']
        user = get_object_or_404(User, id=user_id)
        return user

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
        request.user.Shopping_list.create(recipe=recipe)
        serializer = self.get_serializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        '''Удаление рецепта из листа покупок.'''
        self.request.user.Shopping_list.filter(
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

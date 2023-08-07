import io

import django_filters
from django.http import FileResponse
from recipes.models import Recipe, Tag
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def create_shopping_list(shopping_cart):
    buffer = io.BytesIO()
    page = canvas.Canvas(buffer)
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
    x_position, y_position = 50, 800
    page.setFont("Arial", 24)
    page.drawString(x_position, y_position, 'Cписок покупок:')
    page.setFont("Arial", 12)
    indent = 20
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
    return FileResponse(buffer,
                        as_attachment=True,
                        filename='Shopping_cart.pdf')


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.filters.AllValuesMultipleFilter(
        queryset=Tag.objects.all(),
        field_name='tag__slug',
    )
    is_favorited = django_filters.filters.BooleanFilter(
        method='get_is_favorited'
    )
    is_in_shopping_cart = django_filters.filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def get_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favourites__user=self.request.user)
        return queryset

    def get_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_list__user=self.request.user)
        return queryset

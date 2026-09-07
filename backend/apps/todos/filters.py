import django_filters

from .models import Todo


class TodoFilter(django_filters.FilterSet):
    completed = django_filters.BooleanFilter(field_name="completed")

    class Meta:
        model = Todo
        fields = ["completed"]

from rest_framework.pagination import LimitOffsetPagination
from django.db import connection
from website.models import Statistic


class CustomPagination(LimitOffsetPagination):
    def get_count(self, queryset):
        if 'WHERE "website_darwincoreobject"."data" @> \'{}\'' in str(queryset.query): # No filters
            return Statistic.objects.get_total_count()
        return queryset.count()


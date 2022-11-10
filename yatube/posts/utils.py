from django.core.paginator import Paginator
from django.conf import settings


def make_paginator(request, data):
    paginator = Paginator(data, settings.NUMBER_POSTS_ON_ONE_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj

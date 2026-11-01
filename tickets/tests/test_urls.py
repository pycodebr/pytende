from django.test import SimpleTestCase
from django.urls import URLPattern, URLResolver

import accounts.urls
import core.urls
import tickets.urls


def pattern_names(patterns):
    return {pattern.name for pattern in patterns if isinstance(pattern, URLPattern)}


class UrlTests(SimpleTestCase):
    def test_only_expected_routes_exist(self):
        self.assertEqual(pattern_names(core.urls.urlpatterns), {'health'})
        includes = [p for p in core.urls.urlpatterns if isinstance(p, URLResolver)]
        self.assertEqual(
            sorted(str(p.pattern) for p in includes),
            ['', '', 'admin/'],
        )
        self.assertEqual(pattern_names(accounts.urls.urlpatterns), {'login', 'logout'})
        self.assertEqual(
            pattern_names(tickets.urls.urlpatterns),
            {'list', 'create', 'update', 'update_status'},
        )
        self.assertEqual(accounts.urls.app_name, 'accounts')
        self.assertEqual(tickets.urls.app_name, 'tickets')

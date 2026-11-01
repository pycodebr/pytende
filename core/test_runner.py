from django.test.runner import DiscoverRunner
from django.test.utils import override_settings


class PytendeTestRunner(DiscoverRunner):
    """Runs the suite the same way in development and inside the production image.

    With DEBUG=False the production block turns on SECURE_SSL_REDIRECT, and the
    test client (plain HTTP) would get 301 on every request. The suite checks the
    app's behaviour, not the HTTPS redirect done in front of it by the Traefik.
    """

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        self._https_override = override_settings(SECURE_SSL_REDIRECT=False)
        self._https_override.enable()

    def teardown_test_environment(self, **kwargs):
        self._https_override.disable()
        super().teardown_test_environment(**kwargs)

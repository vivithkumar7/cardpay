from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import override_settings

User = get_user_model()

class AuthTests(APITestCase):
    def test_root_redirects_to_api_docs(self):
        response = self.client.get("/")
        self.assertRedirects(response, "/api/docs/", fetch_redirect_response=False)

    def test_api_root_redirects_to_api_docs(self):
        response = self.client.get("/api/")
        self.assertRedirects(response, "/api/docs/", fetch_redirect_response=False)

    def test_register_and_login(self):
        response = self.client.post("/api/auth/register/", {
            "username": "testuser", "email": "test@example.com",
            "password": "StrongPass123!", "password2": "StrongPass123!"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        login = self.client.post("/api/auth/login/", {
            "username": "testuser", "password": "StrongPass123!"
        }, format="json")
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.assertIn("access", login.data)

    def test_refresh_endpoint_returns_a_new_access_token(self):
        user = User.objects.create_user(username="refreshuser", password="StrongPass123!")
        refresh = str(RefreshToken.for_user(user))

        response = self.client.post("/api/auth/refresh/", {"refresh": refresh}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, status.HTTP_200_OK)

    def test_logout_blacklists_refresh_token(self):
        user = User.objects.create_user(username="logoutuser", password="StrongPass123!")
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout = self.client.post(
            "/api/auth/logout/", {"refresh": str(refresh)}, format="json"
        )
        refreshed = self.client.post(
            "/api/auth/refresh/", {"refresh": str(refresh)}, format="json"
        )

        self.assertEqual(logout.status_code, status.HTTP_200_OK)
        self.assertEqual(refreshed.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="PaySecure <no-reply@example.com>",
    )
    def test_successful_login_queues_an_account_security_email(self):
        mail.outbox.clear()
        user = User.objects.create_user(
            username="emailuser",
            email="emailuser@example.com",
            password="StrongPass123!",
        )

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                "/api/auth/login/",
                {"username": "emailuser", "password": "StrongPass123!"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["emailuser@example.com"])
        self.assertIn("sign-in", mail.outbox[0].subject.lower())

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class CardTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="carduser", password="StrongPass123!")
        token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_card_is_masked_and_cvv_not_stored(self):
        response = self.client.post("/api/cards/", {
            "card_type": "CREDIT",
            "card_holder_name": "Test User",
            "expiry_month": 12,
            "expiry_year": 2030,
            "card_number": "4111111111111111",
            "cvv": "123"
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["last4"], "1111")
        self.assertNotIn("cvv", response.data)
        self.assertEqual(response.data["masked_card_number"], "************1111")

import os

TEST_STRIPE_API_KEY = os.getenv(
    "STRIPE_API_KEY",
    "sk_test_51JQqS5DRo0HQjSKXyBpcQN5FuPDUea3PSquXziw6hfgDHT3hD5JMjURVrfnfum0gHjqChJ23rYmA6Z7rpX0RXZuS00DKdfq9rd",
)
TEST_STRIPE_BASE_URL = os.getenv("STRIPE_BASE_URL", "https://api.stripe.com/v1")

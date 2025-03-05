from rest_framework import serializers
from datetime import date

class PriceCalculatorRequestSerializer(serializers.Serializer):
    listing_id = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    guests = serializers.IntegerField(min_value=1)

class DailyPriceSerializer(serializers.Serializer):
    date = serializers.DateField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    note = serializers.CharField()

class PriceCalculatorResponseSerializer(serializers.Serializer):
    daily_prices = DailyPriceSerializer(many=True)
    extras = serializers.DictField()
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
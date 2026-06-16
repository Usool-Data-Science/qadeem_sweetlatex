from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Address, CustomUser, Profile


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        obj = self.user
        first_name = ""
        last_name = ""
        if hasattr(obj, "user_profile"):
            first_name = obj.user_profile.first_name
            last_name = obj.user_profile.last_name
        data.update(
            {
                "user_id": obj.id,
                "email": obj.email,
                "first_name": first_name,
                "last_name": last_name,
                "has_password_login": obj.has_password_login,
            }
        )

        return data


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id",
            "street",
            "city",
            "state",
            "country",
            "address_type",
            "is_default",
        ]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["first_name", "last_name", "gender", "bio", "receive_emails"]


class UserUpdateSerializer(serializers.ModelSerializer):
    # ─────────────────────────────────────────
    # USER FIELDS (direct on CustomUser)
    # ─────────────────────────────────────────
    # orders = OrderSerializer(many=True, read_only=True)
    phone_number = serializers.CharField(required=False, allow_null=True)

    # ─────────────────────────────────────────
    # PROFILE FIELDS (flat input → we map manually)
    # ─────────────────────────────────────────
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    bio = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    receive_emails = serializers.BooleanField(required=False)

    # ─────────────────────────────────────────
    # ADDRESS FIELDS (flat input → we map manually)
    # ─────────────────────────────────────────
    street = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    address_type = serializers.CharField(required=False, default="home")
    is_default = serializers.BooleanField(required=False)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "phone_number",
            # "orders",
            "first_name",
            "last_name",
            "gender",
            "bio",
            "receive_emails",
            # address
            "street",
            "city",
            "state",
            "country",
            "address_type",
            "is_default",
        ]
        read_only_fields = ["id", "email"]

    # ─────────────────────────────────────────
    # UPDATE LOGIC
    # ─────────────────────────────────────────
    def update(self, instance, validated_data):
        print("Validated data:", validated_data)

        # -------------------------
        # USER FIELDS
        # -------------------------
        instance.phone_number = validated_data.get(
            "phone_number", instance.phone_number
        )
        instance.save()

        # -------------------------
        # PROFILE UPDATE
        # -------------------------
        profile_data = {
            "first_name": validated_data.pop("first_name", None),
            "last_name": validated_data.pop("last_name", None),
            "gender": validated_data.pop("gender", None),
            "bio": validated_data.pop("bio", None),
            "receive_emails": validated_data.pop("receive_emails", None),
        }

        # remove None values
        profile_data = {k: v for k, v in profile_data.items() if v is not None}

        if profile_data:
            Profile.objects.update_or_create(user=instance, defaults=profile_data)

        # -------------------------
        # ADDRESS UPDATE
        # -------------------------
        address_fields = {
            "street": validated_data.pop("street", None),
            "city": validated_data.pop("city", None),
            "state": validated_data.pop("state", None),
            "country": validated_data.pop("country", None),
            "address_type": validated_data.pop("address_type", "home"),
            "is_default": validated_data.pop("is_default", False),
        }

        address_fields = {k: v for k, v in address_fields.items() if v is not None}

        if address_fields:
            address_type = address_fields.pop("address_type", "home")

            Address.objects.update_or_create(
                user=instance, address_type=address_type, defaults=address_fields
            )

        return instance

    # ─────────────────────────────────────────
    # RESPONSE FORMAT (READ SIDE)
    # ─────────────────────────────────────────
    def to_representation(self, instance):
        data = super().to_representation(instance)

        # -------------------------
        # PROFILE (read)
        # -------------------------
        try:
            profile = instance.user_profile
            data["first_name"] = profile.first_name
            data["last_name"] = profile.last_name
            data["gender"] = profile.gender
            data["bio"] = profile.bio
            data["receive_emails"] = profile.receive_emails
        except Profile.DoesNotExist:
            data["first_name"] = ""
            data["last_name"] = ""
            data["gender"] = None
            data["bio"] = None
            data["receive_emails"] = True

        # -------------------------
        # ADDRESS (read default)
        # -------------------------
        addresses = instance.addresses.all()
        data["addresses"] = AddressSerializer(addresses, many=True).data
        # -------------------------
        # DEFAULT ADDRESS (optional convenience)
        # -------------------------
        default_address = addresses.filter(is_default=True).first()

        if default_address:
            data["street"] = default_address.street
            data["city"] = default_address.city
            data["state"] = default_address.state
            data["country"] = default_address.country
            data["address_type"] = default_address.address_type
            data["is_default"] = default_address.is_default
        else:
            data["street"] = ""
            data["city"] = ""
            data["state"] = ""
            data["country"] = ""
            data["address_type"] = None
            data["is_default"] = False

        return data

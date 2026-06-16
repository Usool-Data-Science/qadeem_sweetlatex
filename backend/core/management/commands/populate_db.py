import random
from datetime import timedelta

from core.models import Artist, ArtistImage, Product, ProductImage, ProductSize
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = "Instantiate the database with dummy dataset"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force reseeding by clearing existing data",
        )

    def handle(self, *args, **kwargs):
        force = kwargs.get("force")

        if Product.objects.exists() and not force:
            self.stdout.write(
                self.style.WARNING("Database already seeded. Use --force to reseed.")
            )
            return

        if force:
            self.stdout.write("Clearing existing data...")
            # Delete in order of dependency
            ProductImage.objects.all().delete()
            ProductSize.objects.all().delete()
            Product.objects.all().delete()
            ArtistImage.objects.all().delete()
            Artist.objects.all().delete()
            self.stdout.write(self.style.WARNING("Old data deleted"))

        self.stdout.write("Seeding database...")

        with transaction.atomic():
            # 1. Create Users
            admin_email = "admin@example.com"
            user, created = User.objects.get_or_create(
                email=admin_email, defaults={"is_staff": True, "is_superuser": True}
            )
            if created:
                user.set_password("test")
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Admin {admin_email} created"))

            # 2. Create Artists
            artists = []
            for i in range(3):
                artist = Artist.objects.create(
                    name=f"Artist {i + 1}",
                    description=f"Bio for Artist {i + 1}. Expert in modern aesthetics.",
                    website=f"https://artist{i + 1}.com",
                )

                # Note: If using real ImageFields, you'd usually pass a file.
                # Since this is a seeder, we'll assume your model allows URL strings
                # or you're mocking the image field.
                ArtistImage.objects.create(
                    artist=artist,
                    # If your model uses an ImageField, this might need to be a File object.
                    # If it's a URLField/CloudinaryField, a string is fine.
                    image=f"https://picsum.photos/400/400?random={i}",
                )
                artists.append(artist)

            # 3. Create Products
            for i in range(10):
                # Calculate a future deadline
                random_days = random.randint(5, 30)
                future_deadline = timezone.now() + timedelta(days=random_days)

                product = Product.objects.create(
                    title=f"Limited Edition Artwork {i + 1}",
                    artist=random.choice(artists),
                    goal=random.randint(100, 1000),
                    deadline=future_deadline,  # Now a datetime object
                    color=random.choice(["Crimson", "Azure", "Obsidian", "Ivory"]),
                    style=random.choice(["Minimalist", "Surrealism", "Pop Art"]),
                    composition="High-quality sustainable latex and mixed media.",
                    price=random.choice([49.99, 75.00, 120.00, 199.99]),
                )

                # 4. Create Product Images
                for j in range(3):
                    ProductImage.objects.create(
                        product=product,
                        image=f"https://picsum.photos/800/1000?random={i}{j}",
                    )

                # 5. Create Product Sizes & Stock
                # We pick a subset of sizes for variety
                available_sizes = ["XS", "S", "M", "L", "XL"]
                selected_sizes = random.sample(available_sizes, k=random.randint(2, 5))

                for size_label in selected_sizes:
                    ProductSize.objects.create(
                        product=product, size=size_label, stock=random.randint(0, 50)
                    )

        self.stdout.write(self.style.SUCCESS("Successfully seeded database!"))

from django.contrib import admin

from .models import (
    Artist,
    ArtistImage,
    Cart,
    CartItem,
    Order,
    OrderItem,
    Product,
    ProductImage,
    ProductSize,
)


class ArtistImageInLine(admin.TabularInline):
    model = ArtistImage
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductSizesInline(admin.TabularInline):
    model = ProductSize
    extra = 1


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 1


class ArtistAdmin(admin.ModelAdmin):
    inlines = [ArtistImageInLine]


class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline, ProductSizesInline]


class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline]


class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline]


admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Artist, ArtistAdmin)
admin.site.register(Cart, CartAdmin)

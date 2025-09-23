from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True)
    birth_date = models.DateField(blank=True, null=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    baby_due_date = models.DateField(
        blank=True, null=True, verbose_name="Data Prevista do Parto"
    )
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Address(models.Model):
    cep = models.CharField(max_length=10)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    neighborhood = models.CharField(max_length=100)
    street = models.CharField(max_length=255)
    number = models.CharField(max_length=20)
    complement = models.CharField(max_length=255, blank=True, null=True)
    customer = models.ForeignKey(
        "Customer", on_delete=models.CASCADE, related_name="addresses"
    )

    class Meta:
        verbose_name = "Endereço"
        verbose_name_plural = "Endereços"

    def __str__(self):
        return f"{self.city}, {self.neighborhood}, {self.street}, {self.number}"
